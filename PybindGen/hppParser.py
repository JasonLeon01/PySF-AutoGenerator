import os
import re
import clang.cindex


INTERESTED_KINDS = (
    clang.cindex.CursorKind.CLASS_DECL,
    clang.cindex.CursorKind.STRUCT_DECL,
    clang.cindex.CursorKind.CXX_METHOD,
    clang.cindex.CursorKind.FIELD_DECL,
    clang.cindex.CursorKind.CONSTRUCTOR,
    clang.cindex.CursorKind.FUNCTION_TEMPLATE,
    clang.cindex.CursorKind.DESTRUCTOR,
    clang.cindex.CursorKind.FUNCTION_DECL,
    clang.cindex.CursorKind.NAMESPACE,
    clang.cindex.CursorKind.ENUM_DECL,
    clang.cindex.CursorKind.VAR_DECL,
)
LITERAL_KINDS = (
    clang.cindex.CursorKind.INTEGER_LITERAL,
    clang.cindex.CursorKind.FLOATING_LITERAL,
    clang.cindex.CursorKind.IMAGINARY_LITERAL,
    clang.cindex.CursorKind.STRING_LITERAL,
    clang.cindex.CursorKind.CHARACTER_LITERAL,
    clang.cindex.CursorKind.CXX_BOOL_LITERAL_EXPR,
    clang.cindex.CursorKind.CXX_NULL_PTR_LITERAL_EXPR,
)


class Parser:
    def __init__(self, includes, hpp_root, hpp_file, cpp_version, ignored_macros):
        args = [
            f"-std={cpp_version}",
            "-I.",
            includes,
            *[f"-D{macro}=" for macro in ignored_macros],
        ]
        index = clang.cindex.Index.create()
        real_path = os.path.join(hpp_root, hpp_file)
        tu = index.parse(
            real_path,
            args,
            options=clang.cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD,
        )
        if tu.diagnostics:
            print("Clang diagnostics:")
            for diag in tu.diagnostics:
                print(f"  - {diag}")
        target_file = os.path.abspath(real_path)
        self._root_items = []
        for c in tu.cursor.get_children():
            d = self._node_to_dict(c, target_file)
            if d:
                if isinstance(d, list):
                    self._root_items.extend(d)
                else:
                    self._root_items.append(d)

    def get_dict(self):
        return self._root_items

    def _get_qualified_name(self, cursor):
        if cursor is None:
            return ""

        parent = cursor.semantic_parent
        if parent and parent.kind in (
            clang.cindex.CursorKind.NAMESPACE,
            clang.cindex.CursorKind.CLASS_DECL,
            clang.cindex.CursorKind.STRUCT_DECL,
            clang.cindex.CursorKind.ENUM_DECL,
        ):
            parent_name = self._get_qualified_name(parent)
            if cursor.spelling:
                if parent_name:
                    return f"{parent_name}::{cursor.spelling}"
                return cursor.spelling
            else:
                return parent_name
        return cursor.spelling

    def _resolve_default_value(self, expr_cursor):
        children = list(expr_cursor.get_children())

        if expr_cursor.kind == clang.cindex.CursorKind.DECL_REF_EXPR:
            ref_cursor = expr_cursor.referenced
            if ref_cursor:
                return self._get_qualified_name(ref_cursor)

        if expr_cursor.kind == clang.cindex.CursorKind.MEMBER_REF_EXPR:
            ref_cursor = expr_cursor.referenced
            if ref_cursor:
                return self._get_qualified_name(ref_cursor)

        if expr_cursor.kind == clang.cindex.CursorKind.BINARY_OPERATOR and len(children) == 2:
            op_token = [
                t.spelling
                for t in expr_cursor.get_tokens()
                if not t.spelling.isalnum() and t.spelling not in ["::", "_"]
            ]
            operator = op_token[0] if op_token else " "
            lhs = self._resolve_default_value(children[0])
            rhs = self._resolve_default_value(children[1])
            return f"{lhs} {operator} {rhs}"

        if expr_cursor.kind == clang.cindex.CursorKind.UNEXPOSED_EXPR and children:
            return self._resolve_default_value(children[0])

        if expr_cursor.kind in LITERAL_KINDS:
            try:
                return next(expr_cursor.get_tokens()).spelling
            except StopIteration:
                return ""

        tokens = [tok.spelling for tok in expr_cursor.get_tokens()]
        result = " ".join(tokens)
        result = re.sub(r"\s*::\s*", "::", result)
        result = re.sub(r"\{\s*\}", "{}", result)
        return result

    def _is_std_spelling(self, type_spelling):
        if not type_spelling:
            return False
        return "std::" in type_spelling or type_spelling.startswith("std")

    def _is_std_cursor(self, cursor):
        if not cursor:
            return False
        qualified_name = self._get_qualified_name(cursor)
        if qualified_name and (qualified_name.startswith("std::") or qualified_name == "std"):
            return True
        semantic_parent = getattr(cursor, "semantic_parent", None)
        while semantic_parent:
            parent_name = getattr(semantic_parent, "spelling", "")
            if parent_name == "std":
                return True
            semantic_parent = getattr(semantic_parent, "semantic_parent", None)
        return False

    def _prefer_std_spelling(self, current_value, candidate_value):
        if not candidate_value:
            return current_value
        if not current_value:
            return candidate_value

        current_has_template = "<" in current_value and ">" in current_value
        candidate_has_template = "<" in candidate_value and ">" in candidate_value
        if candidate_has_template and not current_has_template:
            return candidate_value
        if current_has_template and not candidate_has_template:
            return current_value
        if len(candidate_value) > len(current_value):
            return candidate_value
        return current_value

    def _qualify_std_top_level(self, type_spelling, qualified_name):
        if not type_spelling:
            return type_spelling
        if "std::" in type_spelling:
            return type_spelling
        if not qualified_name or not qualified_name.startswith("std::"):
            return type_spelling

        top_name = qualified_name.split("::")[-1]
        match = re.match(r"\s*([A-Za-z_]\w*)", type_spelling)
        if not match:
            return type_spelling
        if match.group(1) != top_name:
            return type_spelling

        start, end = match.span(1)
        return f"{type_spelling[:start]}{qualified_name}{type_spelling[end:]}"

    def _normalize_std_string_like(self, type_spelling):
        if not type_spelling:
            return type_spelling

        base = re.sub(r"\bconst\b|\bvolatile\b", "", type_spelling)
        base = base.replace("&", "").replace("*", "").strip()
        base = re.sub(r"\s+", "", base)

        if re.search(r"(^|::)string_view($|[^A-Za-z_0-9])", base):
            return "std::string"
        if re.search(r"(^|::)basic_string_view<char([>,].*|$)", base):
            return "std::string"
        if re.search(r"(^|::)basic_string<char([>,].*|$)", base):
            return "std::string"
        return type_spelling

    def _type_spelling_with_std_floor(self, type_obj):
        if not type_obj:
            return ""

        current_type = type_obj
        std_candidate = None
        seen = set()

        for _ in range(64):
            current_spelling = current_type.spelling
            seen_key = (str(current_type.kind), current_spelling)
            if seen_key in seen:
                break
            seen.add(seen_key)

            if self._is_std_spelling(current_spelling):
                std_candidate = self._prefer_std_spelling(std_candidate, current_spelling)

            type_decl = current_type.get_declaration()
            if self._is_std_cursor(type_decl):
                qualified_name = self._get_qualified_name(type_decl)
                qualified_current_spelling = self._qualify_std_top_level(current_spelling, qualified_name)
                if current_spelling:
                    std_candidate = self._prefer_std_spelling(std_candidate, qualified_current_spelling)
                if qualified_name and self._is_std_spelling(qualified_name):
                    std_candidate = self._prefer_std_spelling(std_candidate, qualified_name)

            underlying_type = None
            if type_decl and type_decl.kind.is_declaration():
                candidate = type_decl.underlying_typedef_type
                if candidate and candidate.kind != clang.cindex.TypeKind.INVALID:
                    underlying_type = candidate
            if underlying_type:
                if self._is_std_spelling(underlying_type.spelling):
                    return self._normalize_std_string_like(underlying_type.spelling)
                current_type = underlying_type
                continue

            canonical_type = current_type.get_canonical()
            if not canonical_type:
                break
            if canonical_type.spelling == current_spelling:
                break
            current_type = canonical_type

        if std_candidate:
            return self._normalize_std_string_like(std_candidate)

        canonical_type = type_obj.get_canonical()
        if canonical_type and canonical_type.spelling:
            return self._normalize_std_string_like(canonical_type.spelling)
        return self._normalize_std_string_like(type_obj.spelling)

    def _get_function_parameters(self, node):
        params = []
        anonymous_param_counter = 0
        for c in node.get_children():
            if c.kind == clang.cindex.CursorKind.PARM_DECL:
                full_type = self._type_spelling_with_std_floor(c.type)

                default_value = None
                expr_children = [
                    child for child in c.get_children() if child.kind.is_expression() or child.kind.is_unexposed()
                ]

                if expr_children:
                    default_expr = expr_children[-1]
                    default_value = self._resolve_default_value(default_expr)
                    if default_value:
                        default_value = default_value.strip()

                param_name = c.spelling
                if not param_name:
                    print(
                        f"Warning: Anonymous parameter detected in {node.spelling}, type: {full_type}. Assigning a default name."
                    )
                    param_name = f"ANONYMOUS_PARAM_{anonymous_param_counter}"
                    anonymous_param_counter += 1

                params.append(
                    {
                        "name": param_name,
                        "type": full_type,
                        "raw_type": c.type.spelling,
                        "default_value": default_value,
                    }
                )
        return params

    def _get_return_type(self, node):
        if hasattr(node, "result_type"):
            return self._normalize_std_string_like(node.result_type.spelling)
        return ""

    def _get_full_return_type(self, node):
        if hasattr(node, "result_type"):
            return self._type_spelling_with_std_floor(node.result_type)
        return ""

    def _get_base_classes(self, node):
        bases = []
        for c in node.get_children():
            if c.kind == clang.cindex.CursorKind.CXX_BASE_SPECIFIER:
                bases.append(
                    {
                        "name": c.type.spelling,
                        "access": self._get_access_specifier(c),
                    }
                )
        return bases

    def _get_access_specifier(self, node):
        try:
            kind = node.access_specifier
            if kind == clang.cindex.AccessSpecifier.PUBLIC:
                return "public"
            elif kind == clang.cindex.AccessSpecifier.PROTECTED:
                return "protected"
            elif kind == clang.cindex.AccessSpecifier.PRIVATE:
                return "private"
            else:
                if node.semantic_parent.kind == clang.cindex.CursorKind.STRUCT_DECL:
                    return "public"
                return "private"
        except Exception:
            if node.semantic_parent.kind == clang.cindex.CursorKind.STRUCT_DECL:
                return "public"
            return "private"

    def _is_constructor_template(self, node):
        if not node.semantic_parent:
            return False

        parent = node.semantic_parent
        if parent.kind in (clang.cindex.CursorKind.CLASS_DECL, clang.cindex.CursorKind.STRUCT_DECL):
            return node.spelling == parent.spelling

        return False

    def _clean_doc_comment(self, raw_comment):
        if not raw_comment:
            return None
        cleaned_lines = []
        for line in raw_comment.splitlines():
            line = line.strip()
            if not line:
                cleaned_lines.append("")
                continue
            line = re.sub(r"^/\*+<?\s?", "", line)
            line = re.sub(r"\*/$", "", line)
            line = re.sub(r"^\*+\s?", "", line)
            line = re.sub(r"^//[/!<]*\s?", "", line)
            line = line.strip()
            cleaned_lines.append(line)
        cleaned = "\n".join(cleaned_lines).strip()
        return cleaned if cleaned else None

    def _extract_doc(self, node):
        raw_comment = None
        brief_comment = None
        if hasattr(node, "raw_comment"):
            raw_comment = node.raw_comment
        if hasattr(node, "brief_comment"):
            brief_comment = node.brief_comment
        cleaned = self._clean_doc_comment(raw_comment)
        doc = {}
        if raw_comment:
            doc["raw"] = raw_comment
        if brief_comment:
            doc["brief"] = brief_comment
        if cleaned:
            doc["text"] = cleaned
        return doc if doc else None

    def _node_to_dict(self, node, target_filename):
        if node.location and node.location.file and os.path.abspath(node.location.file.name) != target_filename:
            return None

        if (
            node.kind
            in (
                clang.cindex.CursorKind.CLASS_DECL,
                clang.cindex.CursorKind.STRUCT_DECL,
            )
            and not node.is_definition()
        ):
            return None

        if node.kind == clang.cindex.CursorKind.FRIEND_DECL:
            result = []
            for c in node.get_children():
                d = self._node_to_dict(c, target_filename)
                if d is not None:
                    if isinstance(d, list):
                        for item in d:
                            item["is_friend"] = True
                        result.extend(d)
                    else:
                        d["is_friend"] = True
                        result.append(d)
            if result:
                return result if len(result) > 1 else result[0]
            else:
                return None

        if node.kind == clang.cindex.CursorKind.ENUM_DECL and node.is_anonymous():
            hoisted_constants = []
            parent_qualified_name = self._get_qualified_name(node.semantic_parent)

            for child in node.get_children():
                if child.kind == clang.cindex.CursorKind.ENUM_CONSTANT_DECL:
                    qualified_const_name = (
                        f"{parent_qualified_name}::{child.spelling}"
                        if parent_qualified_name and parent_qualified_name != "::"
                        else child.spelling
                    )

                    hoisted_constants.append(
                        {
                            "kind": "VAR_DECL",
                            "name": child.spelling,
                            "displayname": child.displayname,
                            "type": node.enum_type.spelling,
                            "value": f"py::int_(static_cast<int>({qualified_const_name}))",
                            "access": self._get_access_specifier(child),
                            "readonly": True,
                            "line": (child.location.line if child.location and child.location.file else None),
                        }
                    )
            return hoisted_constants if hoisted_constants else None

        if node.kind not in INTERESTED_KINDS:
            return None

        node_dict = {}
        node_dict["kind"] = str(node.kind).replace("CursorKind.", "")
        node_dict["name"] = node.spelling
        node_dict["displayname"] = node.displayname
        node_dict["line"] = node.location.line if node.location and node.location.file else None
        doc = self._extract_doc(node)
        if doc:
            node_dict["doc"] = doc

        if node.kind in (
            clang.cindex.CursorKind.CXX_METHOD,
            clang.cindex.CursorKind.FUNCTION_DECL,
            clang.cindex.CursorKind.CONSTRUCTOR,
            clang.cindex.CursorKind.DESTRUCTOR,
        ):
            for token in node.get_tokens():
                if token.spelling == "delete":
                    node_dict["deleted"] = True
                    break

            if node.kind == clang.cindex.CursorKind.CONSTRUCTOR:
                if hasattr(node, "is_copy_constructor") and node.is_copy_constructor():
                    node_dict["is_copy_constructor"] = True
                if hasattr(node, "is_move_constructor") and node.is_move_constructor():
                    node_dict["is_move_constructor"] = True

        if node.kind in (
            clang.cindex.CursorKind.CLASS_DECL,
            clang.cindex.CursorKind.STRUCT_DECL,
        ):
            node_dict["base_classes"] = self._get_base_classes(node)
            if hasattr(node, "is_abstract_record"):
                node_dict["is_abstract"] = node.is_abstract_record()

        if hasattr(node, "access_specifier"):
            node_dict["access"] = self._get_access_specifier(node)
        if node.kind == clang.cindex.CursorKind.FIELD_DECL:
            node_dict["type"] = self._normalize_std_string_like(node.type.spelling)
            node_dict["access"] = self._get_access_specifier(node)

        if node.kind in (
            clang.cindex.CursorKind.CXX_METHOD,
            clang.cindex.CursorKind.FUNCTION_DECL,
            clang.cindex.CursorKind.CONSTRUCTOR,
            clang.cindex.CursorKind.DESTRUCTOR,
        ):
            node_dict["parameters"] = self._get_function_parameters(node)
            node_dict["return_type"] = self._get_return_type(node)
            node_dict["full_return_type"] = self._get_full_return_type(node)

            if hasattr(node, "is_static_method"):
                node_dict["static"] = node.is_static_method()
            elif hasattr(node, "is_static"):
                node_dict["static"] = node.is_static()

        children = []
        for c in node.get_children():
            d = self._node_to_dict(c, target_filename)
            if d is None:
                continue
            if isinstance(d, list):
                children.extend(d)
            else:
                children.append(d)
        if children:
            node_dict["children"] = children

        if node.kind == clang.cindex.CursorKind.ENUM_DECL:
            node_dict["kind"] = "ENUM_DECL"
            node_dict["name"] = node.spelling
            node_dict["displayname"] = node.displayname
            node_dict["line"] = node.location.line if node.location and node.location.file else None

            enum_constants = []
            for child in node.get_children():
                if child.kind == clang.cindex.CursorKind.ENUM_CONSTANT_DECL:
                    enum_constants.append(
                        {
                            "name": child.spelling,
                            "value": child.enum_value,
                            "line": (child.location.line if child.location and child.location.file else None),
                        }
                    )
            if enum_constants:
                node_dict["constants"] = enum_constants

        if node.kind == clang.cindex.CursorKind.FUNCTION_TEMPLATE:
            if self._is_constructor_template(node):
                node_dict["kind"] = "CONSTRUCTOR"
                node_dict["is_template"] = True
            else:
                node_dict["kind"] = "FUNCTION_TEMPLATE"

        if node.kind == clang.cindex.CursorKind.VAR_DECL:
            node_dict["type"] = node.type.spelling

        return node_dict
