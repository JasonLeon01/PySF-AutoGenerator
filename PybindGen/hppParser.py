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

    def _get_function_parameters(self, node):
        params = []
        anonymous_param_counter = 0
        for c in node.get_children():
            if c.kind == clang.cindex.CursorKind.PARM_DECL:
                full_type = c.type.get_canonical().spelling

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
            return node.result_type.spelling
        return ""

    def _get_full_return_type(self, node):
        if hasattr(node, "result_type"):
            try:
                return node.result_type.get_canonical().spelling
            except Exception:
                return node.result_type.spelling
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
            node_dict["type"] = node.type.spelling
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
