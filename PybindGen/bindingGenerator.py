import os
import re
from pathlib import Path
import tempfile
from . import utils

UNARY_OPERATOR_MAP = {
    "operator-": "__neg__",
    "operator+": "__pos__",
    "operator~": "__invert__",
    "operator!": "__not__",
}
BINARY_OPERATOR_MAP = {
    "operator==": "__eq__",
    "operator!=": "__ne__",
    "operator<": "__lt__",
    "operator<=": "__le__",
    "operator>": "__gt__",
    "operator>=": "__ge__",
    "operator+": "__add__",
    "operator-": "__sub__",
    "operator*": "__mul__",
    "operator/": "__truediv__",
    "operator%": "__mod__",
    "operator[]": "__getitem__",
    "operator()": "__call__",
    "operator+=": "__iadd__",
    "operator-=": "__isub__",
    "operator*=": "__imul__",
    "operator/=": "__itruediv__",
    "operator%=": "__imod__",
    "operator&=": "__iand__",
    "operator|=": "__ior__",
    "operator^=": "__ixor__",
    "operator<<=": "__ilshift__",
    "operator>>=": "__irshift__",
    "operator&": "__and__",
    "operator|": "__or__",
    "operator^": "__xor__",
    "operator<<": "__lshift__",
    "operator>>": "__rshift__",
}
IGNORE_LIST = [
    "operator=",
    "operator++",
    "operator--",
    "operator&&",
    "operator||",
    'operator""_deg',
    'operator""_rad',
]


class Generator:
    def __init__(
        self,
        common_module_name,
        dict_root,
        REPLACE_TYPE,
        SPECIFIC_TYPE,
        IGNORE_PARAM_TYPE,
        IGNORE_RETURN_TYPE,
        SPECIFIC_RETURN_TYPE,
        REPLACE_DEFAULT,
        hpp_file,
    ):
        self._common_module_name = common_module_name
        self._dict_root = dict_root
        self._REPLACE_TYPE = REPLACE_TYPE
        self._SPECIFIC_TYPE = SPECIFIC_TYPE
        self._IGNORE_PARAM_TYPE = IGNORE_PARAM_TYPE
        self._IGNORE_RETURN_TYPE = IGNORE_RETURN_TYPE
        self._SPECIFIC_RETURN_TYPE = SPECIFIC_RETURN_TYPE
        self._REPLACE_DEFAULT = REPLACE_DEFAULT
        self._hpp_file = hpp_file

    def emit_pybind_module(self, out_file):
        all_class_types = self._get_all_class_types(self._dict_root)
        globalfreeop_map = self._handle_free_operators(self._dict_root, all_class_types)
        file_names = Path(self._hpp_file).parts[-2:]
        parent, file_name = file_names
        bind_name = f"{parent}/bind_{file_name}"

        common_def = f'def_submodule("{self._common_module_name}");\n'
        with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False) as tmp_f:
            self._emit_items(tmp_f, self._dict_root, "    ", "m", "", globalfreeop_map)
            addition_file = f"Additions/bind_{file_name.split('.')[0]}_Addition.txt"
            if os.path.exists(addition_file):
                with open(addition_file, "r", encoding="utf-8") as add_f:
                    tmp_f.write(add_f.read())
            tmp_f.flush()
            tmp_f.seek(0)
            lines = tmp_f.readlines()

        auto_lines = [line for line in lines if line.strip().startswith("auto ")]
        other_lines = [line for line in lines if not line.strip().startswith("auto ")]

        temp_auto_lines = []
        for line in auto_lines:
            if common_def in line:
                continue
            to_append = line.replace(f"m_{self._common_module_name}", "m")
            for key, value in self._REPLACE_DEFAULT.items():
                if key in to_append:
                    to_append = to_append.replace(key, f"{value} /* {key} */ ")
            temp_auto_lines.append(to_append)
        auto_lines = temp_auto_lines
        temp_other_lines = []
        for line in other_lines:
            if common_def in line:
                continue
            to_append = line.replace(f"m_{self._common_module_name}", "m")
            for key, value in self._REPLACE_DEFAULT.items():
                if key in to_append:
                    to_append = to_append.replace(key, f"{value} /* {key} */ ")
            temp_other_lines.append(to_append)
        other_lines = temp_other_lines

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(f'#include "{bind_name}"\n')
            f.write("namespace py = pybind11;\n\n")
            f.write(f"void bind_{file_name.split('.')[0]}(py::module &m) {{\n")

            for line in auto_lines:
                f.write(line)
            for line in other_lines:
                f.write(line)

            f.write("}\n")
        os.remove(tmp_f.name)
        print(f"Generated {out_file}")

    def _should_ignore_function(self, func):
        if not self._IGNORE_PARAM_TYPE:
            return False

        return_type = func.get("return_type", "void")
        if return_type in self._IGNORE_RETURN_TYPE:
            return True

        parameters = func.get("parameters", [])
        for param in parameters:
            param_type = param.get("type", "")
            normalized_param_type = re.sub(
                r"\bconst\b|\bvolatile\b", "", param_type
            ).strip()
            normalized_param_type = re.sub(r"\s+", " ", normalized_param_type)
            normalized_param_type = normalized_param_type.replace(" &", "&").replace(
                " *", "*"
            )

            for ignore_type in self._IGNORE_PARAM_TYPE:
                normalized_ignore_type = re.sub(
                    r"\bconst\b|\bvolatile\b", "", ignore_type
                ).strip()
                normalized_ignore_type = re.sub(r"\s+", " ", normalized_ignore_type)
                normalized_ignore_type = normalized_ignore_type.replace(
                    " &", "&"
                ).replace(" *", "*")

                if (
                    normalized_param_type == normalized_ignore_type
                    or normalized_ignore_type in normalized_param_type
                ):
                    return True
        return False

    def _canonical_type(self, typ):
        typ = re.sub(r"\bconst\b", "", typ)
        typ = typ.replace("&", "").replace("*", "").strip()
        typ = re.sub(r"\s+", " ", typ)
        return typ

    def _find_replace_type(self, typ):
        ctyp = self._canonical_type(typ)
        for k, v in self._REPLACE_TYPE.items():
            if self._canonical_type(k) == ctyp:
                return v
        return None

    def _get_specific_type_replacement(self, cpp_type):
        normalized_type = utils.normalize_type(cpp_type)
        normalized_type = normalized_type.replace(" &", "&").replace(" *", "*")

        for key, value in self._SPECIFIC_TYPE.items():
            if normalized_type.startswith(key):
                return value
        return None

    def _check_specific_return_type(self, return_type):
        for key, value in self._SPECIFIC_RETURN_TYPE.items():
            if key in return_type:
                return value
        return None

    def _is_void_pointer(self, typ):
        normalized_type = utils.normalize_type(typ)
        return normalized_type == "void *"

    def _lambda_argument_string(self, parameters):
        args = []
        for p in parameters:
            specific_replacement = self._get_specific_type_replacement(p["type"])
            if specific_replacement:
                pybind_type, _ = specific_replacement
                args.append(f"{pybind_type} {p['name']}")
                continue

            raw_type = p["type"]
            replacement = self._find_replace_type(raw_type)
            t = replacement if replacement else raw_type
            args.append(f"{t} {p['name']}")
        return ", ".join(args)

    def _generate_py_args_string(self, parameters):
        if not parameters:
            return ""

        arg_strings = []
        for p in parameters:
            arg_str = f'py::arg("{p["name"]}")'

            if p["default_value"] is not None:
                default_value = p["default_value"].strip()
                if default_value.startswith("="):
                    default_value = default_value[1:].strip()

                default_value = self._process_default_value(default_value, p["type"])
                arg_str += f" = {default_value}"

            arg_strings.append(arg_str)

        return ", " + ", ".join(arg_strings)

    def _process_default_value(self, default_value, param_type):
        if not default_value:
            return default_value

        default_value = self._clean_anonymous_enum_value(default_value)

        if default_value == "{}":
            clean_type = self._extract_clean_type_name(param_type)
            return f"{clean_type}()"

        if "::" in default_value and not default_value.startswith("std::"):
            corrected_value = self._correct_namespace_in_default_value(
                default_value, param_type
            )
            if corrected_value:
                return corrected_value

        if self._is_enum_like_value(default_value):
            return self._ensure_full_enum_name(default_value, param_type)

        return default_value

    def _clean_anonymous_enum_value(self, default_value):
        if not default_value or "(unnamed enum at" not in default_value:
            return default_value

        pattern = r"([^:]+::)*([^:]+)::\(unnamed enum at [^)]+\)::([^:]+)$"
        match = re.match(pattern, default_value)

        if match:
            namespace_and_class = match.group(1) or ""
            class_name = match.group(2)
            enum_value = match.group(3)

            if namespace_and_class:
                return f"{namespace_and_class}{class_name}::{enum_value}"
            else:
                return f"{class_name}::{enum_value}"

        anonymous_enum_pattern = r"\(unnamed enum at [^)]+\)::"
        cleaned_value = re.sub(anonymous_enum_pattern, "", default_value)

        return cleaned_value

    def _extract_clean_type_name(self, param_type):
        clean_type = utils.normalize_type(param_type)
        clean_type = clean_type.replace("&", "").replace("*", "").strip()
        return clean_type

    def _correct_namespace_in_default_value(self, default_value, param_type):
        param_type_clean = self._extract_clean_type_name(param_type)

        if "::" in param_type_clean:
            namespace_parts = param_type_clean.split("::")
            if len(namespace_parts) >= 2:
                namespace_prefix = "::".join(namespace_parts[:-1])
                class_name = namespace_parts[-1]

                if default_value.startswith(class_name + "::"):
                    return f"{namespace_prefix}::{default_value}"

        return None

    def _is_enum_like_value(self, value):
        return "::" in value and not "(" in value and not "=" in value

    def _ensure_full_enum_name(self, enum_value, param_type):
        param_type_clean = self._extract_clean_type_name(param_type)

        if not enum_value.startswith(param_type_clean):
            parts = enum_value.split("::")
            if len(parts) >= 2:
                class_name = parts[0]
                enum_name = parts[1]

                if param_type_clean.endswith(class_name):
                    return f"{param_type_clean}::{enum_name}"
                elif param_type_clean.endswith("::" + class_name):
                    return param_type_clean.replace(class_name, enum_value)

        return enum_value

    def _get_forward_call_arguments(self, parameters):
        callargs = []
        for p in parameters:
            specific_replacement = self._get_specific_type_replacement(p["type"])
            if specific_replacement:
                _, call_expr_template = specific_replacement
                call_expr = call_expr_template.replace("DATA", p["name"])
                callargs.append(call_expr)
                continue

            replacement = self._find_replace_type(p["type"])
            if replacement:
                real_type = p["type"]
                callargs.append(f"static_cast<{real_type}>({p['name']})")
            else:
                callargs.append(p["name"])
        return ", ".join(callargs)

    def _function_forward_call(self, selfname, funcname, parameters, is_static):
        params_string = self._get_forward_call_arguments(parameters)
        if is_static:
            return f"{selfname}::{funcname}({params_string})"
        else:
            return f"self.{funcname}({params_string})"

    def _cpp_operator_lambda_code(self, op, params):
        if len(params) == 1:
            return f"return {op}self;"
        elif len(params) == 2:
            arg2_param = params[1]
            arg2_name = arg2_param["name"]
            arg2_type = arg2_param.get("type", "")

            specific_replacement = self._get_specific_type_replacement(arg2_type)
            if specific_replacement:
                _, call_expr_template = specific_replacement
                arg2 = call_expr_template.replace("DATA", arg2_name)
            else:
                arg2 = arg2_name

            if op == "[]":
                return f"return self[{arg2}];"
            elif op == "()":
                call_args = self._get_forward_call_arguments(params[1:])
                return f"return self({call_args});"
            else:
                return f"return self {op} {arg2};"
        else:
            call_args = ", ".join(p["name"] for p in params[1:])
            return f"return self {op} {call_args};"

    def _get_all_class_types(self, items, out=None, prefix=""):
        if out is None:
            out = set()
        for item in items:
            if item["kind"] == "NAMESPACE":
                ns_prefix = prefix + item["name"] + "::" if item["name"] else prefix
                self._get_all_class_types(item.get("children", []), out, ns_prefix)
            elif item["kind"] in ("CLASS_DECL", "STRUCT_DECL"):
                cname = prefix + item["name"]
                out.add(cname)
        return out

    def _norm_typename(self, t):
        return self._canonical_type(t).replace("::", "")

    def _find_declared_class(self, items, typename, prefix=""):
        name_no_const = self._canonical_type(typename)
        for item in items:
            if item["kind"] == "NAMESPACE":
                ns_prefix = prefix + item["name"] + "::" if item["name"] else prefix
                res = self._find_declared_class(
                    item.get("children", []), typename, ns_prefix
                )
                if res:
                    return res
            elif item["kind"] in ("CLASS_DECL", "STRUCT_DECL"):
                cname = prefix + item["name"]
                if self._canonical_type(cname) == name_no_const:
                    return item
        return None

    def _emit_cpp_enum(self, f, enum_item, indent, module_var, namespace_prefix=""):
        enum_name = enum_item["name"]
        full_enum_name = f"{namespace_prefix}{enum_name}"
        var_name = f"{module_var}{enum_name}"

        f.write(
            f'{indent}auto {var_name} = py::enum_<{full_enum_name}>({module_var}, "{enum_name}");\n'
        )

        for constant in enum_item.get("constants", []):
            const_name = constant["name"]
            f.write(
                f'{indent}{var_name}.value("{const_name}", {full_enum_name}::{const_name});\n'
            )

    def _emit_cpp_class(self, f, cls, indent, module_var, namespace_prefix=""):
        class_name = cls["name"]
        full_class_name = f"{namespace_prefix}{cls['name']}"
        class_type_keyword = "struct" if cls["kind"] == "STRUCT_DECL" else "class"
        class_var = f"v_{self._norm_typename(full_class_name)}"

        if cls.get("deleted", False):
            print(f"Skipping deleted {class_type_keyword}: {full_class_name}")
            return

        holder_str = ""
        is_abstract = cls.get("is_abstract", False)
        if is_abstract:
            holder_str = f", std::unique_ptr<{full_class_name}, py::nodelete>"
            print(
                f"Info: Detected abstract class {full_class_name}, using py::nodelete holder."
            )

        base_classes = []
        for base_info in cls.get("base_classes", []):
            if base_info.get("access") == "public":
                base_name = base_info["name"]
                if "::" not in base_name and namespace_prefix:
                    base_name = f"{namespace_prefix}{base_name}"
                base_classes.append(base_name)
            else:
                print(
                    f"Info: Skipping non-public base '{base_info['name']}' of class '{full_class_name}'."
                )

        if base_classes:
            bases_str = ", ".join(f"{base}" for base in base_classes)
            f.write(
                f'{indent}auto {class_var} = py::class_<{full_class_name}, {bases_str}{holder_str}>({module_var}, "{class_name}");\n'
            )
        else:
            f.write(
                f'{indent}auto {class_var} = py::class_<{full_class_name}{holder_str}>({module_var}, "{class_name}");\n'
            )

        if not is_abstract:
            has_constructor = any(
                c["kind"] == "CONSTRUCTOR" for c in cls.get("children", [])
            )
            if cls["kind"] == "STRUCT_DECL" and not has_constructor:
                f.write(f"{indent}{class_var}.def(py::init<>());\n")

            need_unique = False
            for c in cls.get("children", []):
                if c["kind"] == "CONSTRUCTOR" and c.get("access") == "public":
                    if c.get("is_copy_constructor", False) and c.get("deleted", False):
                        print(
                            f"Detected deleted copy constructor: {full_class_name}::{c['displayname']}"
                        )
                        need_unique = True
                        break
                    if c.get("is_move_constructor", False) and c.get("deleted", False):
                        print(
                            f"Detected deleted move constructor: {full_class_name}::{c['displayname']}"
                        )
                        need_unique = True
                        break
            for c in cls.get("children", []):
                if c["kind"] == "CONSTRUCTOR" and c.get("access") == "public":
                    if c.get("is_copy_constructor", False):
                        print(f"Skipping copy constructor: {full_class_name}")
                        continue
                    if c.get("is_move_constructor", False):
                        print(f"Skipping move constructor: {full_class_name}")
                        continue
                    if c.get("deleted", False):
                        print(
                            f"Skipping deleted constructor: {full_class_name}::{c['displayname']}"
                        )
                        continue
                    if self._should_ignore_function(c):
                        print(
                            f"Ignoring constructor due to parameter type: {full_class_name}::{c['displayname']}"
                        )
                        continue

                    params = c.get("parameters", [])

                    if len(params) == 0:
                        f.write(
                            f"{indent}{class_var}.def(py::init<>()); // default constructor\n"
                        )
                        continue
                    def_args = self._lambda_argument_string(params)
                    call_args = self._get_forward_call_arguments(params)
                    py_args_str = self._generate_py_args_string(params)

                    if need_unique:
                        f.write(
                            f"{indent}{class_var}.def(py::init([]({def_args}) {{ return std::make_unique<{full_class_name}>({call_args}); }}){py_args_str});\n"
                        )
                    else:
                        f.write(
                            f"{indent}{class_var}.def(py::init([]({def_args}) {{ return new {full_class_name}({call_args}); }}){py_args_str});\n"
                        )

        for c in cls.get("children", []):
            if (
                c["kind"] == "VAR_DECL"
                and c.get("readonly")
                and c.get("access") == "public"
            ):
                var_name = c["name"]
                if var_name == "None":
                    var_name = "None_"
                full_var_name = c["value"]
                f.write(f'{indent}{class_var}.attr("{var_name}") = {full_var_name};\n')

        for c in cls.get("children", []):
            if c["kind"] == "FIELD_DECL" and c.get("access") == "public":
                field_name = c["name"]
                return_type = c.get("type", "void")
                return_sample = self._check_specific_return_type(return_type)
                if return_sample:
                    f.write(
                        f'{indent}{return_sample[1]}({class_var}, "{field_name}", &{full_class_name}::{field_name});\n'
                    )
                else:
                    f.write(
                        f'{indent}{class_var}.def_readwrite("{field_name}", &{full_class_name}::{field_name});\n'
                    )

        for c in cls.get("children", []):
            if c["kind"] == "CXX_METHOD" and c.get("access") == "public":
                if c.get("deleted", False):
                    print(
                        f"Skipping deleted method: {full_class_name}::{c['displayname']}"
                    )
                    continue
                if self._should_ignore_function(c):
                    print(
                        f"Ignoring method due to parameter type: {full_class_name}::{c['displayname']}"
                    )
                    continue

                name = c["name"]
                params = c.get("parameters", [])
                py_args_str = self._generate_py_args_string(params)
                return_type = c.get("return_type", "void")

                if name in IGNORE_LIST:
                    print(f"Ignoring method in IGNORE_LIST: {full_class_name}::{name}")
                    continue

                is_unary = len(params) == 0 and name in UNARY_OPERATOR_MAP
                is_binary = name in BINARY_OPERATOR_MAP

                if is_unary:
                    pyname = UNARY_OPERATOR_MAP[name]
                    op = name[len("operator") :]
                    lambda_body = self._cpp_operator_lambda_code(op, [{"name": "self"}])
                    f.write(
                        f'{indent}{class_var}.def("{pyname}", []({full_class_name}& self) {{ {lambda_body} }});\n'
                    )
                elif is_binary:
                    pyname = BINARY_OPERATOR_MAP[name]
                    op = name[len("operator") :]
                    all_args = (
                        f"{full_class_name}& self, {self._lambda_argument_string(params)}"
                        if params
                        else f"{full_class_name}& self"
                    )
                    lambda_body = self._cpp_operator_lambda_code(
                        op, [{"name": "self"}, *params]
                    )
                    f.write(
                        f'{indent}{class_var}.def("{pyname}", []({all_args}) {{ {lambda_body} }}{py_args_str});\n'
                    )
                else:
                    pyname = name
                    def_args = self._lambda_argument_string(params)
                    callcode = self._function_forward_call(
                        full_class_name, name, params, is_static=c.get("static", False)
                    )
                    if c.get("static", False):
                        f.write(
                            f'{indent}{class_var}.def_static("{pyname}", []({def_args}) {{ return {callcode}; }}{py_args_str});\n'
                        )
                    else:
                        all_args = (
                            f"{full_class_name}& self, {def_args}"
                            if def_args
                            else f"{full_class_name}& self"
                        )
                        return_sample = self._check_specific_return_type(return_type)
                        if return_sample:
                            callcode = return_sample[0].replace("DATA", callcode)
                        f.write(
                            f'{indent}{class_var}.def("{pyname}", []({all_args}) {{ return {callcode}; }}{py_args_str});\n'
                        )

        for c in cls.get("children", []):
            if c["kind"] == "ENUM_DECL" and c.get("access") == "public":
                nested_enum_prefix = f"{full_class_name}::"
                self._emit_cpp_enum(f, c, indent, class_var, nested_enum_prefix)

        for c in cls.get("children", []):
            if (
                c["kind"] in ("CLASS_DECL", "STRUCT_DECL")
                and c.get("access") == "public"
            ):
                nested_namespace_prefix = f"{full_class_name}::"
                self._emit_cpp_class(f, c, indent, class_var, nested_namespace_prefix)

        for opitem in cls.get("__bindfreeoperators__", []):
            func = opitem["func"]
            if func.get("deleted", False):
                print(f"Skipping deleted free operator: {func['displayname']}")
                continue
            if self._should_ignore_function(func):
                print(
                    f"Ignoring free operator due to parameter type: {func['displayname']}"
                )
                continue

            op_name = opitem["op_name"]
            pyname = opitem["pyname"]
            params = func["parameters"]
            is_unary = opitem["is_unary"]
            py_args_str = self._generate_py_args_string(params[1:])

            if op_name in IGNORE_LIST:
                print(f"Ignoring free operator in IGNORE_LIST: {op_name}")
                continue

            if is_unary:
                all_args = f"{full_class_name}& self"
                lambda_body = f"return {op_name}self;"
                f.write(
                    f'{indent}{class_var}.def("{pyname}", []({all_args}) {{ {lambda_body} }});  // from global unary operator\n'
                )
            else:
                py_args_str = self._generate_py_args_string(params[1:])
                all_args = f"{full_class_name}& self, {self._lambda_argument_string(params[1:])}"

                arg2_param = params[1]
                arg2_name = arg2_param["name"]
                arg2_type = arg2_param["type"]
                specific_replacement = self._get_specific_type_replacement(arg2_type)
                if specific_replacement:
                    _, call_expr_template = specific_replacement
                    arg2 = call_expr_template.replace("DATA", arg2_name)
                else:
                    arg2 = arg2_name

                lambda_body = f"return self {op_name} {arg2};"
                f.write(
                    f'{indent}{class_var}.def("{pyname}", []({all_args}) {{ {lambda_body} }}{py_args_str});  // from global binary operator\n'
                )

    def _process_type(self, typ, all_class_types):
        if not typ:
            return "void"

        for k, v in self._REPLACE_TYPE.items():
            if k == typ:
                return v
            elif k in typ:
                return typ.replace(k, v)

        for known_type in all_class_types:
            if known_type == typ:
                return typ

        basic_types = {"int", "float", "bool", "void", "char", "double"}
        if typ in basic_types:
            return typ

        return typ

    def _emit_cpp_function(self, f, func, indent, module_var, namespace_prefix=""):
        name = func.get("name", "")
        if name in IGNORE_LIST:
            print(f"Ignoring function in IGNORE_LIST: {namespace_prefix}{name}")
            return
        if self._should_ignore_function(func):
            print(f"Ignoring function due to parameter type: {namespace_prefix}{name}")
            return

        params = func.get("parameters", [])
        def_args = self._lambda_argument_string(params)
        py_args_str = self._generate_py_args_string(params)

        return_type = func.get("return_type", "void")

        full_func_name = f"{namespace_prefix}{func['name']}"
        call_args = self._get_forward_call_arguments(params)

        lambda_body = f"{full_func_name}({call_args})"

        return_sample = self._check_specific_return_type(return_type)
        if return_sample:
            lambda_body = return_sample[0].replace("DATA", lambda_body)

        if return_type != "void":
            lambda_body = f"return {lambda_body}"
        lambda_body = f"{lambda_body};"

        f.write(
            f'{indent}{module_var}.def("{func["name"]}", []({def_args}) {{ {lambda_body} }} {py_args_str}); // Outer class function \n'
        )

    def _handle_free_operators(
        self, items, all_class_types, bind_map=None, namespace_prefix=""
    ):
        if bind_map is None:
            bind_map = dict()

        for item in items:
            if item["kind"] == "NAMESPACE":
                ns_prefix = (
                    namespace_prefix + item["name"] + "::"
                    if item["name"]
                    else namespace_prefix
                )
                self._handle_free_operators(
                    item.get("children", []), all_class_types, bind_map, ns_prefix
                )
            elif item["kind"] == "FUNCTION_DECL":
                name = item.get("name", "")
                if not name.startswith("operator"):
                    continue

                if name in IGNORE_LIST:
                    print(
                        f"Ignoring free operator in IGNORE_LIST: {namespace_prefix}{name}"
                    )
                    continue
                if self._should_ignore_function(item):
                    print(
                        f"Ignoring free operator due to parameter type: {namespace_prefix}{name}"
                    )
                    continue

                params = item.get("parameters", [])
                if not params:
                    continue

                is_unary = len(params) == 1 and name in UNARY_OPERATOR_MAP
                is_binary = len(params) == 2 and name in BINARY_OPERATOR_MAP
                if not is_unary and not is_binary:
                    continue

                first_param_type = params[0]["type"]
                first_type = self._canonical_type(first_param_type)

                target_class_typename = None
                for q in all_class_types:
                    if self._canonical_type(q) == first_type:
                        target_class_typename = q
                        break
                    if q.endswith("::" + first_type):
                        target_class_typename = q
                        break
                if target_class_typename:
                    op_code = name[len("operator") :]
                    pyname = (
                        UNARY_OPERATOR_MAP[name]
                        if is_unary
                        else BINARY_OPERATOR_MAP[name]
                    )
                    item["namespace"] = namespace_prefix
                    item["_bound_to_class"] = True
                    bind_map.setdefault(target_class_typename, []).append(
                        {
                            "func": item,
                            "op_name": op_code,
                            "pyname": pyname,
                            "is_unary": is_unary,
                        }
                    )
                else:
                    print(
                        f"Warning: Global operator {namespace_prefix}{name}({first_param_type}...) "
                        f"could not find matching type {first_type}, skipping binding!"
                    )
                    item["_skip_binding"] = True
        return bind_map

    def _emit_items(
        self, f, items, indent, module_var, namespace_prefix, globalfreeop_map=None
    ):
        for item in items:
            if item["kind"] == "NAMESPACE":
                ns_name = item["name"]
                ns_var = ns_name if ns_name else "SELF"
                ns_cpp_prefix = namespace_prefix + (ns_name + "::" if ns_name else "")

                if ns_name:
                    ns_var_py = module_var + "_" + ns_var
                    f.write(
                        f'{indent}auto {ns_var_py} = {module_var}.def_submodule("{ns_name}");\n'
                    )
                    self._emit_items(
                        f,
                        item.get("children", []),
                        indent,
                        ns_var_py,
                        ns_cpp_prefix,
                        globalfreeop_map,
                    )
                else:
                    self._emit_items(
                        f,
                        item.get("children", []),
                        indent,
                        module_var,
                        ns_cpp_prefix,
                        globalfreeop_map,
                    )
            elif item["kind"] in ("CLASS_DECL", "STRUCT_DECL"):
                this_full = (
                    namespace_prefix + item["name"]
                    if namespace_prefix
                    else item["name"]
                )
                if (
                    globalfreeop_map is not None
                    and this_full in globalfreeop_map
                    and globalfreeop_map[this_full]
                ):
                    item = dict(item)
                    item["__bindfreeoperators__"] = globalfreeop_map[this_full]
                self._emit_cpp_class(f, item, indent, module_var, namespace_prefix)
            elif item["kind"] == "ENUM_DECL":
                self._emit_cpp_enum(f, item, indent, module_var, namespace_prefix)
            elif item["kind"] == "VAR_DECL":
                var_name = item["name"]
                if var_name in IGNORE_LIST:
                    print(
                        f"Ignoring variable in IGNORE_LIST: {namespace_prefix}{var_name}"
                    )
                    continue

                if var_name == "None":
                    var_name = "None_"

                if item.get("readonly"):
                    full_var_name = item["value"]
                    f.write(
                        f'{indent}{module_var}.attr("{var_name}") = {full_var_name};\n'
                    )
                else:
                    full_var_name = f"{namespace_prefix}{var_name}"
                    f.write(
                        f'{indent}{module_var}.attr("{var_name}") = {full_var_name};\n'
                    )
            elif item["kind"] == "FUNCTION_DECL":
                if item.get("_skip_binding", False) or item.get(
                    "_bound_to_class", False
                ):
                    continue

                name = item.get("name", "")
                if name in IGNORE_LIST:
                    print(f"Ignoring function in IGNORE_LIST: {namespace_prefix}{name}")
                    continue

                self._emit_cpp_function(f, item, indent, module_var, namespace_prefix)
