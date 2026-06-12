import os
import re
import sys
import clang.cindex
from .utils import get_macos_clang_args


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
    clang.cindex.CursorKind.TYPEDEF_DECL,
    clang.cindex.CursorKind.TYPE_ALIAS_DECL,
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
        if sys.platform == "darwin":
            args.extend(get_macos_clang_args())
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
        self._include_root = os.path.abspath(hpp_root)
        self._surface_type_qualifications = {}
        self._ambiguous_surface_type_names = set()
        self._collect_surface_type_qualifications(tu.cursor)
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

    def _is_in_include_root(self, cursor):
        if not cursor.location or not cursor.location.file:
            return False
        file_path = os.path.abspath(cursor.location.file.name)
        try:
            return os.path.commonpath([file_path, self._include_root]) == self._include_root
        except ValueError:
            return False

    def _remember_surface_type_qualification(self, name, qualified_name):
        if not name or not qualified_name or not qualified_name.startswith("sf::"):
            return

        previous = self._surface_type_qualifications.get(name)
        if previous and previous != qualified_name:
            self._ambiguous_surface_type_names.add(name)
            self._surface_type_qualifications.pop(name, None)
            return

        if name not in self._ambiguous_surface_type_names:
            self._surface_type_qualifications[name] = qualified_name

    def _collect_surface_type_qualifications(self, cursor):
        if (
            cursor.kind != clang.cindex.CursorKind.TRANSLATION_UNIT
            and cursor.location
            and cursor.location.file
            and not self._is_in_include_root(cursor)
        ):
            return

        if self._is_in_include_root(cursor) and cursor.kind in (
            clang.cindex.CursorKind.CLASS_DECL,
            clang.cindex.CursorKind.STRUCT_DECL,
            clang.cindex.CursorKind.ENUM_DECL,
            clang.cindex.CursorKind.NAMESPACE,
            clang.cindex.CursorKind.TYPEDEF_DECL,
            clang.cindex.CursorKind.TYPE_ALIAS_DECL,
        ):
            self._remember_surface_type_qualification(cursor.spelling, self._get_qualified_name(cursor))

        for child in cursor.get_children():
            self._collect_surface_type_qualifications(child)

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

    def _qualify_surface_type(self, type_spelling, qualified_name):
        if not type_spelling or not qualified_name or "::" not in qualified_name:
            return type_spelling

        top_name = qualified_name.split("::")[-1]
        pattern = rf"(?<![:\w]){re.escape(top_name)}(?!\w)"
        return re.sub(pattern, qualified_name, type_spelling, count=1)

    def _qualify_known_surface_types(self, type_spelling):
        if not type_spelling:
            return type_spelling

        def replace(match):
            name = match.group(1)
            return self._surface_type_qualifications.get(name, name)

        return re.sub(r"(?<![:\w])([A-Z]\w*)(?!\w)", replace, type_spelling)

    def _template_argument_types(self, type_obj):
        try:
            count = type_obj.get_num_template_arguments()
        except Exception:
            return []

        if count <= 0:
            return []

        args = []
        for index in range(count):
            try:
                arg_type = type_obj.get_template_argument_type(index)
            except Exception:
                continue
            if arg_type and arg_type.kind != clang.cindex.TypeKind.INVALID:
                args.append(arg_type)
        return args

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

    def _normalize_cstddef_types(self, type_spelling):
        if not type_spelling:
            return type_spelling

        result = type_spelling
        result = re.sub(r"(?<![:\w])::size_t(?!\w)", "std::size_t", result)
        result = re.sub(r"(?<![:\w])size_t(?!\w)", "std::size_t", result)
        return result

    def _type_spelling_with_std_floor(self, type_obj):
        if not type_obj:
            return ""

        type_spelling = type_obj.spelling
        type_decl = type_obj.get_declaration()
        qualified_name = self._get_qualified_name(type_decl)
        type_spelling = self._qualify_surface_type(type_spelling, qualified_name)

        for arg_type in self._template_argument_types(type_obj):
            arg_spelling = arg_type.spelling
            qualified_arg_spelling = self._type_spelling_with_std_floor(arg_type)
            if arg_spelling and qualified_arg_spelling and arg_spelling != qualified_arg_spelling:
                type_spelling = type_spelling.replace(arg_spelling, qualified_arg_spelling)

        type_spelling = self._qualify_known_surface_types(type_spelling)
        type_spelling = type_spelling.replace("::sf::", "::")
        return self._normalize_cstddef_types(self._normalize_std_string_like(type_spelling))

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
            return self._normalize_cstddef_types(self._normalize_std_string_like(node.result_type.spelling))
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
            if hasattr(node, "type") and hasattr(node.type, "is_const_qualified"):
                try:
                    node_dict["readonly"] = node.type.is_const_qualified()
                except Exception:
                    pass

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
            if node.kind == clang.cindex.CursorKind.CXX_METHOD and hasattr(node, "is_const_method"):
                node_dict["const_method"] = node.is_const_method()

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
            node_dict["value"] = self._get_qualified_name(node)

            readonly = False
            if hasattr(node, "type") and hasattr(node.type, "is_const_qualified"):
                try:
                    readonly = bool(node.type.is_const_qualified())
                except Exception:
                    readonly = False

            if not readonly:
                try:
                    tokens = [t.spelling for t in node.get_tokens()]
                    if "constexpr" in tokens or "const" in tokens:
                        readonly = True
                    elif (
                        "static" in tokens
                        and node.semantic_parent
                        and node.semantic_parent.kind
                        in (
                            clang.cindex.CursorKind.CLASS_DECL,
                            clang.cindex.CursorKind.STRUCT_DECL,
                        )
                        and node_dict.get("access") == "public"
                    ):
                        readonly = True
                except Exception:
                    pass

            if readonly:
                node_dict["readonly"] = True

        if node.kind in (clang.cindex.CursorKind.TYPEDEF_DECL, clang.cindex.CursorKind.TYPE_ALIAS_DECL):
            node_dict["type"] = self._normalize_cstddef_types(
                self._normalize_std_string_like(self._get_qualified_name(node))
            )

        return node_dict
