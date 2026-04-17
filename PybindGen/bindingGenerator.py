import os
import re
from pathlib import Path
import tempfile
from .utils import normalize_type

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
    "operator[]": ("__getitem__", "__setitem__"),
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
        IGNORED_MODULE,
        SPECIAL_REPLACE,
        READWRITE_IGNORE,
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
        self._IGNORED_MODULE = IGNORED_MODULE
        self._SPECIAL_REPLACE = SPECIAL_REPLACE
        self._READWRITE_IGNORE = READWRITE_IGNORE
        self._hpp_file = hpp_file
        self._short_type_to_qualified = self._build_short_type_map(self._dict_root)
        self._namespaces = self._build_namespace_set(self._dict_root)
        self._cpp_scope_stack = []

    def _build_short_type_map(self, items, prefix="", out=None):
        if out is None:
            out = {}

        for item in items:
            kind = item.get("kind")

            if kind == "NAMESPACE":
                ns_name = item.get("name", "")
                ns_prefix = f"{prefix}{ns_name}::" if ns_name else prefix
                self._build_short_type_map(item.get("children", []), ns_prefix, out)
                continue

            if kind in ("CLASS_DECL", "STRUCT_DECL", "ENUM_DECL"):
                short_name = item.get("name", "")
                if short_name:
                    full_name = f"{prefix}{short_name}" if prefix else short_name
                    out.setdefault(short_name, set()).add(full_name)
                else:
                    full_name = prefix.rstrip(":")

                nested_prefix = f"{full_name}::" if full_name else prefix
                self._build_short_type_map(item.get("children", []), nested_prefix, out)
                continue

            if kind in ("TYPEDEF_DECL", "TYPE_ALIAS_DECL"):
                short_name = item.get("name", "")
                if short_name:
                    full_name = f"{prefix}{short_name}" if prefix else short_name
                    out.setdefault(short_name, set()).add(full_name)
                continue

            self._build_short_type_map(item.get("children", []), prefix, out)

        return out

    def _build_namespace_set(self, items, prefix="", out=None):
        if out is None:
            out = set()

        for item in items:
            kind = item.get("kind")

            if kind == "NAMESPACE":
                ns_name = item.get("name", "")
                if ns_name:
                    full_ns = f"{prefix}{ns_name}" if prefix else ns_name
                    out.add(full_ns)
                    ns_prefix = f"{full_ns}::"
                else:
                    ns_prefix = prefix
                self._build_namespace_set(item.get("children", []), ns_prefix, out)
                continue

            self._build_namespace_set(item.get("children", []), prefix, out)

        return out

    def _extract_std_function_signature(self, cpp_type):
        if not cpp_type or "std::function" not in cpp_type:
            return None

        start = cpp_type.find("std::function")
        lt_pos = cpp_type.find("<", start)
        if lt_pos == -1:
            return None

        depth = 0
        for i in range(lt_pos, len(cpp_type)):
            ch = cpp_type[i]
            if ch == "<":
                depth += 1
            elif ch == ">":
                depth -= 1
                if depth == 0:
                    return cpp_type[lt_pos + 1 : i].strip()
        return None

    def _normalize_function_signature(self, signature):
        if not signature:
            return signature

        signature = re.sub(r"\s+", " ", signature).strip()
        signature = signature.replace(" *", "*").replace("& ", "&").replace(" &", "&")
        signature = re.sub(r"\s+\(", "(", signature, count=1)
        signature = signature.replace("( ", "(").replace(" )", ")")
        return signature

    def _qualify_signature_types(self, signature):
        if not signature:
            return signature

        result = signature
        for short_name in sorted(self._short_type_to_qualified.keys(), key=len, reverse=True):
            qualified_names = self._short_type_to_qualified.get(short_name, set())
            if len(qualified_names) != 1:
                continue

            qualified_name = next(iter(qualified_names))
            if qualified_name == short_name:
                continue

            pattern = rf"(?<![:\w]){re.escape(short_name)}(?!\w)"
            result = re.sub(pattern, qualified_name, result)

        result = self._qualify_signature_with_enclosing_namespace(result)
        return result

    def _push_cpp_scope(self, scope_prefix):
        self._cpp_scope_stack.append(scope_prefix or "")

    def _pop_cpp_scope(self):
        if self._cpp_scope_stack:
            self._cpp_scope_stack.pop()

    def _current_cpp_scope(self):
        return self._cpp_scope_stack[-1] if self._cpp_scope_stack else ""

    def _enclosing_namespace_prefix(self, scope_prefix):
        if not scope_prefix:
            return ""

        s = scope_prefix.strip()
        s = s.rstrip(":")
        if not s:
            return ""

        parts = [p for p in s.split("::") if p]
        for i in range(len(parts), 0, -1):
            candidate = "::".join(parts[:i])
            if candidate in self._namespaces:
                return candidate + "::"
        return ""

    def _qualify_signature_with_enclosing_namespace(self, signature):
        scope = self._current_cpp_scope()
        ns_prefix = self._enclosing_namespace_prefix(scope)
        if not ns_prefix:
            return signature

        skip = {
            "void",
            "bool",
            "char",
            "signed",
            "unsigned",
            "short",
            "int",
            "long",
            "float",
            "double",
            "wchar_t",
            "char8_t",
            "char16_t",
            "char32_t",
            "const",
            "volatile",
            "auto",
            "size_t",
            "ssize_t",
            "std",
        }

        def repl(m):
            name = m.group(1)
            if name in skip:
                return name
            if not name or not name[0].isupper():
                return name
            return f"{ns_prefix}{name}"

        pattern = r"(?<![:\w])([A-Za-z_]\w*)(?!\w)"
        return re.sub(pattern, repl, signature)

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

        seen = set()
        lines = [line for line in lines if not (line in seen or seen.add(line))]

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
            for key, value in self._SPECIAL_REPLACE.items():
                (key_word1, key_word2) = key
                if key_word1 in to_append and key_word2 in to_append:
                    to_append = value
                    if not to_append.endswith("\n"):
                        to_append += "\n"
            if "def_submodule" in to_append:
                need_continue = False
                for module in self._IGNORED_MODULE:
                    if module in to_append:
                        need_continue = True
                        break
                if need_continue:
                    continue
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
            for key, value in self._SPECIAL_REPLACE.items():
                (key_word1, key_word2) = key
                if key_word1 in to_append and key_word2 in to_append:
                    to_append = value
                    if not to_append.endswith("\n"):
                        to_append += "\n"
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
            normalized_param_type = re.sub(r"\bconst\b|\bvolatile\b", "", param_type).strip()
            normalized_param_type = re.sub(r"\s+", " ", normalized_param_type)
            normalized_param_type = normalized_param_type.replace(" &", "&").replace(" *", "*")

            for ignore_type in self._IGNORE_PARAM_TYPE:
                normalized_ignore_type = re.sub(r"\bconst\b|\bvolatile\b", "", ignore_type).strip()
                normalized_ignore_type = re.sub(r"\s+", " ", normalized_ignore_type)
                normalized_ignore_type = normalized_ignore_type.replace(" &", "&").replace(" *", "*")

                if normalized_param_type == normalized_ignore_type or normalized_ignore_type in normalized_param_type:
                    return True
        return False

    def _canonical_type(self, typ):
        typ = re.sub(r"\bconst\b", "", typ)
        typ = typ.replace("&", "").replace("*", "").strip()
        typ = re.sub(r"\s+", " ", typ)
        return typ

    def _signature_type_key(self, typ):
        typ = re.sub(r"\s+", " ", typ).strip()
        typ = typ.replace(" &", "&").replace("& ", "&")
        typ = typ.replace(" *", "*").replace("* ", "*")
        return typ

    def _method_overload_key(self, method):
        name = method.get("name", "")
        params = method.get("parameters", [])
        param_key = tuple(self._signature_type_key(p.get("raw_type") or p.get("type", "")) for p in params)
        return (name, param_key)

    def _find_replace_type(self, typ):
        ctyp = self._canonical_type(typ)
        for k, v in self._REPLACE_TYPE.items():
            if self._canonical_type(k) == ctyp:
                return v
        return None

    def _get_specific_type_replacement(self, cpp_type, raw_type=None):
        normalized_type = normalize_type(cpp_type)
        normalized_type = normalized_type.replace(" &", "&").replace(" *", "*")
        if raw_type:
            normalized_raw_type = normalize_type(raw_type)
            normalized_raw_type = normalized_raw_type.replace(" &", "&").replace(" *", "*")
        else:
            normalized_raw_type = None
        for key, value in self._SPECIFIC_TYPE.items():
            if (normalized_raw_type and normalized_raw_type == key) or normalized_type.startswith(key):
                return value
        return None

    def _get_function_replacement(self, cpp_type, raw_type=None):
        type_ = cpp_type
        if "std::function" in type_:
            if not raw_type is None and "std::" in raw_type:
                type_ = raw_type
            signature = self._extract_std_function_signature(type_)
            signature = self._normalize_function_signature(signature)
            signature = self._qualify_signature_types(signature)
            wrap_call = f"wrap_pyfunction<{signature}>(DATA)"
            empty_fallback = f"std::function<{signature}>{{}}"
            return ["py::function", f"(DATA ? {wrap_call} : {empty_fallback})"]
        return None

    def _check_specific_return_type(self, return_type):
        for key, value in self._SPECIFIC_RETURN_TYPE.items():
            if key in return_type:
                return value
        return None

    def _is_void_pointer(self, typ):
        normalized_type = normalize_type(typ)
        return normalized_type == "void *"

    def _lambda_argument_string(self, parameters):
        args = []
        for p in parameters:
            specific_replacement = self._get_specific_type_replacement(p["type"], p.get("raw_type", None))
            if not specific_replacement:
                specific_replacement = self._get_function_replacement(p["type"], p.get("raw_type", None))
            if specific_replacement:
                pybind_type, _ = specific_replacement
                args.append(f"{pybind_type} {p['name']}")
                continue

            raw_type = p["type"]
            replacement = self._find_replace_type(raw_type)
            t = replacement if replacement else raw_type
            args.append(f"{t} {p['name']}")
        return ", ".join(args)

    def _lambda_argument_string_for_default_constructor(self, parameters):
        args = []
        for p in parameters:
            raw_type = p["type"]
            replacement = self._find_replace_type(raw_type)
            t = replacement if replacement else raw_type
            args.append(t)
        return ", ".join(args)

    def _is_simple_default_value(self, default_value):
        if default_value is None:
            return True

        dv = default_value.strip()
        if not dv:
            return True

        if dv in {"true", "false", "nullptr", "NULL", "std::nullopt"}:
            return True

        if dv.startswith("py::"):
            return True

        if dv.startswith('"') or dv.startswith('u8"') or dv.startswith('L"'):
            return True

        if re.match(r"^[+-]?\d+$", dv):
            return True
        if re.match(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?[fF]?$", dv):
            return True
        if re.match(r"^0x[0-9A-Fa-f]+$", dv):
            return True

        if "::" in dv:
            return False
        if "(" in dv or ")" in dv:
            return False
        if "{" in dv or "}" in dv:
            return False

        return True

    def _needs_default_overload(self, parameters):
        for p in parameters or []:
            if p.get("default_value") is None:
                continue
            default_value = p["default_value"].strip()
            if default_value.startswith("="):
                default_value = default_value[1:].strip()

            raw_default_value = default_value
            function_replacement = self._get_function_replacement(p["type"], p.get("raw_type", None))
            if function_replacement and raw_default_value == "{}":
                default_value = "py::function()"
            else:
                default_value = self._process_default_value(default_value, p["type"])

            if not self._is_simple_default_value(default_value):
                return True
        return False

    def _default_overload_parameter_sets(self, parameters):
        if not parameters:
            return [parameters]

        first_default_index = None
        for i, p in enumerate(parameters):
            if p.get("default_value") is not None:
                first_default_index = i
                break

        if first_default_index is None:
            return [parameters]

        if not self._needs_default_overload(parameters):
            return [parameters]

        return [parameters[:n] for n in range(first_default_index, len(parameters) + 1)]

    def _generate_py_args_string(self, parameters, include_defaults=True):
        if not parameters:
            return ""

        arg_strings = []
        for p in parameters:
            arg_str = f'py::arg("{p["name"]}")'

            if include_defaults and p["default_value"] is not None:
                default_value = p["default_value"].strip()
                if default_value.startswith("="):
                    default_value = default_value[1:].strip()

                raw_default_value = default_value
                function_replacement = self._get_function_replacement(p["type"], p.get("raw_type", None))
                if function_replacement and raw_default_value == "{}":
                    default_value = "py::function()"
                else:
                    default_value = self._process_default_value(default_value, p["type"])
                if (
                    "::" in default_value
                    and not default_value.startswith("sf::")
                    and not default_value.startswith("std::")
                    and not default_value.startswith("py::")
                    and not default_value.startswith("(sf::")
                    and not default_value.startswith("(std::")
                    and not default_value.startswith("(py::")
                ):
                    optional_pattern = r"^std::optional<([^<>]+)>$"
                    match_ = re.match(optional_pattern, p["type"])
                    if match_:
                        default_value = self._process_default_value(default_value, match_.group(1))
                if (
                    "::" in default_value
                    and not default_value.startswith("sf::")
                    and not default_value.startswith("std::")
                    and not default_value.startswith("py::")
                    and not default_value.startswith("(sf::")
                    and not default_value.startswith("(std::")
                    and not default_value.startswith("(py::")
                ):
                    clean_param_type = self._extract_clean_type_name(p["type"])
                    if "|" in default_value:
                        has_brackets = default_value.startswith("(") and default_value.endswith(")")
                        brackets_pattern = r"^\((.*)\)$"
                        match_ = re.match(brackets_pattern, default_value)
                        if match_:
                            default_value = match_.group(1).strip()
                        results = []
                        for str_ in default_value.split("|"):
                            str_ = str_.strip()
                            if "::" in str_ and not str_.startswith("sf::") and not str_.startswith("std::"):
                                results.append(f"{clean_param_type}(sf::{str_})")
                            else:
                                results.append(str_)
                        default_value = "|".join(results)
                        if has_brackets:
                            default_value = f"({default_value})"
                    else:
                        default_value = f"{clean_param_type}(sf::{default_value})"
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

        qualified_callable = self._qualify_unqualified_default_callable(default_value, param_type)
        if qualified_callable:
            return qualified_callable

        if "::" in default_value and not default_value.startswith("std::"):
            corrected_value = self._correct_namespace_in_default_value(default_value, param_type)
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
        clean_type = normalize_type(param_type)
        clean_type = clean_type.replace("&", "").replace("*", "").strip()
        return clean_type

    def _extract_namespace_prefix(self, param_type):
        clean_type = self._extract_clean_type_name(param_type)
        if "::" not in clean_type:
            return ""
        parts = [p for p in clean_type.split("::") if p]
        if len(parts) < 2:
            return ""
        return "::".join(parts[:-1])

    def _qualify_unqualified_default_callable(self, default_value, param_type):
        if not default_value or "::" in default_value:
            return None

        match = re.match(r"^\s*([A-Za-z_]\w*)\s*\(", default_value)
        if not match:
            return None

        callable_name = match.group(1)
        if callable_name in {
            "static_cast",
            "reinterpret_cast",
            "const_cast",
            "dynamic_cast",
            "sizeof",
            "alignof",
        }:
            return None

        namespace_prefix = self._extract_namespace_prefix(param_type)
        if not namespace_prefix:
            return None

        start, end = match.span(1)
        return f"{default_value[:start]}{namespace_prefix}::{default_value[start:end]}{default_value[end:]}"

    def _is_top_level_const_field_type(self, cpp_type):
        if not cpp_type:
            return False

        normalized = re.sub(r"\s+", " ", cpp_type).strip()
        if not normalized:
            return False

        if re.search(r"\bconst\b\s*$", normalized):
            return True

        if normalized.startswith("const "):
            tail = normalized[len("const ") :].strip()
            if "*" in tail:
                return False
            return True

        return False

    def _is_pointer_to_const_field_type(self, cpp_type):
        if not cpp_type:
            return False

        normalized = re.sub(r"\s+", " ", cpp_type).strip()
        if "*" not in normalized:
            return False

        return normalized.startswith("const ") or bool(re.search(r"\bconst\b\s*\*", normalized))

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
            specific_replacement = self._get_specific_type_replacement(p["type"], p.get("raw_type", None))
            if not specific_replacement:
                specific_replacement = self._get_function_replacement(p["type"], p.get("raw_type", None))
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
            if not specific_replacement:
                specific_replacement = self._get_function_replacement(arg2_type)
            if specific_replacement:
                _, call_expr_template = specific_replacement
                arg2 = call_expr_template.replace("DATA", arg2_name)
            else:
                arg2 = arg2_name

            if op == "[]":
                return (f"return &self[{arg2}];", f"self[{arg2}] = v;")
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
                res = self._find_declared_class(item.get("children", []), typename, ns_prefix)
                if res:
                    return res
            elif item["kind"] in ("CLASS_DECL", "STRUCT_DECL"):
                cname = prefix + item["name"]
                if self._canonical_type(cname) == name_no_const:
                    return item
        return None

    def _get_docstring_parse(self, item):
        if "doc" in item:
            docs = item.get("doc")
            if "text" in docs:
                text = docs.get("text").replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
                return f', "{text}"'
        return ""

    def _emit_cpp_enum(self, f, enum_item, indent, module_var, namespace_prefix=""):
        enum_name = enum_item["name"]
        full_enum_name = f"{namespace_prefix}{enum_name}"
        var_name = f"{module_var}{enum_name}"

        f.write(
            f'{indent}auto {var_name} = py::enum_<{full_enum_name}>({module_var}, "{enum_name}"{self._get_docstring_parse(enum_item)});\n'
        )

        for constant in enum_item.get("constants", []):
            const_name = constant["name"]
            f.write(
                f'{indent}{var_name}.value("{const_name}", {full_enum_name}::{const_name}{self._get_docstring_parse(constant)});\n'
            )

    def _emit_cpp_class(self, f, cls, indent, module_var, namespace_prefix=""):
        class_name = cls["name"]
        full_class_name = f"{namespace_prefix}{cls['name']}"
        class_type_keyword = "struct" if cls["kind"] == "STRUCT_DECL" else "class"
        class_var = f"v_{self._norm_typename(full_class_name)}"

        self._push_cpp_scope(f"{full_class_name}::")
        if cls.get("deleted", False):
            print(f"Skipping deleted {class_type_keyword}: {full_class_name}")
            self._pop_cpp_scope()
            return

        holder_str = ""
        is_abstract = cls.get("is_abstract", False)
        if is_abstract:
            holder_str = f", std::unique_ptr<{full_class_name}, py::nodelete>"
            print(f"Info: Detected abstract class {full_class_name}, using py::nodelete holder.")

        base_classes = []
        for base_info in cls.get("base_classes", []):
            if base_info.get("access") == "public":
                base_name = base_info["name"]
                if "::" not in base_name and namespace_prefix:
                    base_name = f"{namespace_prefix}{base_name}"
                base_classes.append(base_name)
            else:
                print(f"Info: Skipping non-public base '{base_info['name']}' of class '{full_class_name}'.")

        if base_classes:
            bases_str = ", ".join(f"{base}" for base in base_classes)
            f.write(
                f'{indent}auto {class_var} = py::class_<{full_class_name}, {bases_str}{holder_str}>({module_var}, "{class_name}"{self._get_docstring_parse(cls)});\n'
            )
        else:
            f.write(
                f'{indent}auto {class_var} = py::class_<{full_class_name}{holder_str}>({module_var}, "{class_name}"{self._get_docstring_parse(cls)});\n'
            )

        if not is_abstract:
            has_constructor = any(c["kind"] == "CONSTRUCTOR" for c in cls.get("children", []))
            if not has_constructor:
                f.write(f"{indent}{class_var}.def(py::init<>(){self._get_docstring_parse(cls)});\n")

            need_unique = False
            no_copy_constructor = False
            no_move_constructor = True
            has_public_copy_ctor = False
            for c in cls.get("children", []):
                if c["kind"] == "CONSTRUCTOR" and c.get("access") == "public":
                    if c.get("is_copy_constructor", False) and c.get("deleted", False):
                        print(f"Detected deleted copy constructor: {full_class_name}::{c['displayname']}")
                        no_copy_constructor = True
                    if c.get("is_copy_constructor", False) and not c.get("deleted", False):
                        has_public_copy_ctor = True
                    if c.get("is_move_constructor", False) and not c.get("deleted", False):
                        print(f"Detected non-deleted move constructor: {full_class_name}::{c['displayname']}")
                        no_move_constructor = False
            if no_copy_constructor and no_move_constructor:
                need_unique = True

            for c in cls.get("children", []):
                if c["kind"] == "CONSTRUCTOR" and c.get("access") == "public":
                    if c.get("is_copy_constructor", False):
                        print(f"Skipping copy constructor: {full_class_name}")
                        continue
                    if c.get("is_move_constructor", False):
                        print(f"Skipping move constructor: {full_class_name}")
                        continue
                    if c.get("deleted", False):
                        print(f"Skipping deleted constructor: {full_class_name}::{c['displayname']}")
                        continue
                    if self._should_ignore_function(c):
                        print(f"Ignoring constructor due to parameter type: {full_class_name}::{c['displayname']}")
                        continue
                    if c.get("is_template", False):
                        print(f"Skipping template constructor: {full_class_name}::{c['displayname']}")
                        continue

                    params = c.get("parameters", [])
                    param_sets = self._default_overload_parameter_sets(params)
                    for sub_params in param_sets:
                        force_lambda = len(param_sets) > 1
                        include_defaults = not force_lambda

                        if len(sub_params) == 0 and len(params) == 0:
                            f.write(
                                f"{indent}{class_var}.def(py::init<>(){self._get_docstring_parse(c)}); // Default constructor\n"
                            )
                            continue

                        need_switch = force_lambda
                        for p in sub_params:
                            if self._get_specific_type_replacement(p["type"], p.get("raw_type", None)):
                                need_switch = True
                                break
                            if self._get_function_replacement(p["type"], p.get("raw_type", None)):
                                need_switch = True
                                break
                            if self._find_replace_type(p["type"]):
                                need_switch = True
                                break
                            if self._check_specific_return_type(p["type"]):
                                need_switch = True
                                break

                        def_args = self._lambda_argument_string(sub_params)
                        call_args = self._get_forward_call_arguments(sub_params)
                        py_args_str = self._generate_py_args_string(sub_params, include_defaults=include_defaults)

                        if need_unique:
                            f.write(
                                f"{indent}{class_var}.def(py::init([]({def_args}) {{ return std::make_unique<{full_class_name}>({call_args}); }}){self._get_docstring_parse(c)}{py_args_str});\n"
                            )
                        else:
                            if need_switch:
                                f.write(
                                    f"{indent}{class_var}.def(py::init([]({def_args}) {{ return new {full_class_name}({call_args}); }}){self._get_docstring_parse(c)}{py_args_str});\n"
                                )
                            else:
                                def_args = self._lambda_argument_string_for_default_constructor(sub_params)
                                f.write(
                                    f"{indent}{class_var}.def(py::init<{def_args}>(){self._get_docstring_parse(c)}{py_args_str});\n"
                                )

            if has_public_copy_ctor:
                f.write(
                    f'{indent}{class_var}.def("__copy__", [](const {full_class_name}& self) {{ return {full_class_name}(self); }});\n'
                )
                f.write(
                    f'{indent}{class_var}.def("__deepcopy__", [](const {full_class_name}& self, py::dict memo) {{ (void)memo; return {full_class_name}(self); }});\n'
                )

        f.write(
            f'{indent}{class_var}.def("getPtr", []({full_class_name}& self) {{ return reinterpret_cast<uintptr_t>(&self); }});\n'
        )

        for c in cls.get("children", []):
            if c["kind"] == "VAR_DECL" and c.get("readonly") and c.get("access") == "public":
                var_name = c["name"]
                if var_name == "None":
                    var_name = "None_"
                full_var_name = c["value"]
                f.write(f'{indent}{class_var}.attr("{var_name}") = {full_var_name};\n')

        for c in cls.get("children", []):
            if c["kind"] == "FIELD_DECL" and c.get("access") == "public":
                field_name = c["name"]
                return_type = c.get("type", "void")
                top_level_const = self._is_top_level_const_field_type(return_type)
                pointer_to_const = self._is_pointer_to_const_field_type(return_type)
                is_readonly_field = c.get("readonly", False) or top_level_const
                if pointer_to_const and not top_level_const:
                    is_readonly_field = False
                return_sample = self._check_specific_return_type(return_type)
                helper = return_sample[1] if return_sample else ""
                if helper:
                    if is_readonly_field and helper in ["def_string_property", "def_vector_string_property"]:
                        helper = helper + "_readonly"
                    f.write(
                        f'{indent}{helper}({class_var}, "{field_name}", &{full_class_name}::{field_name}{self._get_docstring_parse(c)});\n'
                    )
                else:
                    jump = False
                    if full_class_name in self._READWRITE_IGNORE:
                        for ignore_field in self._READWRITE_IGNORE[full_class_name]:
                            if ignore_field == field_name:
                                jump = True
                                break
                    if jump:
                        continue
                    if is_readonly_field:
                        f.write(
                            f'{indent}{class_var}.def_readonly("{field_name}", &{full_class_name}::{field_name}{self._get_docstring_parse(c)});\n'
                        )
                    else:
                        f.write(
                            f'{indent}{class_var}.def_readwrite("{field_name}", &{full_class_name}::{field_name}{self._get_docstring_parse(c)});\n'
                        )

        const_method_overloads_to_skip = set()
        method_overload_presence = {}
        for c in cls.get("children", []):
            if c["kind"] != "CXX_METHOD" or c.get("access") != "public":
                continue
            if c.get("static", False):
                continue
            key = self._method_overload_key(c)
            seen = method_overload_presence.setdefault(key, {"const": False, "nonconst": False})
            if c.get("const_method", False):
                seen["const"] = True
            else:
                seen["nonconst"] = True
        for key, seen in method_overload_presence.items():
            if seen["const"] and seen["nonconst"]:
                const_method_overloads_to_skip.add(key)

        for c in cls.get("children", []):
            if c["kind"] == "CXX_METHOD" and c.get("access") == "public":
                if c.get("deleted", False):
                    print(f"Skipping deleted method: {full_class_name}::{c['displayname']}")
                    continue
                if self._should_ignore_function(c):
                    print(f"Ignoring method due to parameter type: {full_class_name}::{c['displayname']}")
                    continue

                name = c["name"]
                params = c.get("parameters", [])
                return_type = c.get("return_type", "void")
                full_return_type = c.get("full_return_type", return_type)

                if c.get("const_method", False) and self._method_overload_key(c) in const_method_overloads_to_skip:
                    continue

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
                        f'{indent}{class_var}.def("{pyname}", []({full_class_name}& self) {{ {lambda_body} }}{self._get_docstring_parse(c)});\n'
                    )
                elif is_binary:
                    pyname = BINARY_OPERATOR_MAP[name]
                    op = name[len("operator") :]
                    py_args_str = self._generate_py_args_string(params)
                    all_args = (
                        f"{full_class_name}& self, {self._lambda_argument_string(params)}"
                        if params
                        else f"{full_class_name}& self"
                    )
                    lambda_body = self._cpp_operator_lambda_code(op, [{"name": "self"}, *params])
                    if name == "operator[]":
                        pyname1, pyname2 = pyname
                        lambda_body1, lambda_body2 = lambda_body
                        f.write(
                            f'{indent}{class_var}.def("{pyname1}", []({all_args}) {{ {lambda_body1} }}{self._get_docstring_parse(c)}{py_args_str}, py::return_value_policy::reference_internal);\n'
                        )
                        set_item_type = full_return_type.replace("const ", "")
                        f.write(
                            f'{indent}{class_var}.def("{pyname2}", []({all_args}, const {set_item_type} v) {{ {lambda_body2} }}{self._get_docstring_parse(c)}{py_args_str}, py::arg("v"));\n'
                        )
                    else:
                        f.write(
                            f'{indent}{class_var}.def("{pyname}", []({all_args}) {{ {lambda_body} }}{self._get_docstring_parse(c)}{py_args_str});\n'
                        )
                else:
                    pyname = name
                    param_sets = self._default_overload_parameter_sets(params)
                    force_overloads = len(param_sets) > 1
                    for sub_params in param_sets:
                        include_defaults = not force_overloads
                        def_args = self._lambda_argument_string(sub_params)
                        py_args_str = self._generate_py_args_string(sub_params, include_defaults=include_defaults)
                        callcode = self._function_forward_call(
                            full_class_name, name, sub_params, is_static=c.get("static", False)
                        )
                        if c.get("static", False):
                            f.write(
                                f'{indent}{class_var}.def_static("{pyname}", []({def_args}) {{ return {callcode}; }}{self._get_docstring_parse(c)}{py_args_str});\n'
                            )
                        else:
                            all_args = (
                                f"{full_class_name}& self, {def_args}" if def_args else f"{full_class_name}& self"
                            )
                            return_sample = self._check_specific_return_type(return_type)
                            if return_sample:
                                callcode = return_sample[0].replace("DATA", callcode)
                            f.write(
                                f'{indent}{class_var}.def("{pyname}", []({all_args}) {{ return {callcode}; }}{self._get_docstring_parse(c)}{py_args_str});\n'
                            )

        for c in cls.get("children", []):
            if c["kind"] == "ENUM_DECL" and c.get("access") == "public":
                nested_enum_prefix = f"{full_class_name}::"
                self._emit_cpp_enum(f, c, indent, class_var, nested_enum_prefix)

        for c in cls.get("children", []):
            if c["kind"] in ("CLASS_DECL", "STRUCT_DECL") and c.get("access") == "public":
                nested_namespace_prefix = f"{full_class_name}::"
                self._emit_cpp_class(f, c, indent, class_var, nested_namespace_prefix)

        for opitem in cls.get("__bindfreeoperators__", []):
            func = opitem["func"]
            if func.get("deleted", False):
                print(f"Skipping deleted free operator: {func['displayname']}")
                continue
            if self._should_ignore_function(func):
                print(f"Ignoring free operator due to parameter type: {func['displayname']}")
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
                if not specific_replacement:
                    specific_replacement = self._get_function_replacement(arg2_type)
                if specific_replacement:
                    _, call_expr_template = specific_replacement
                    arg2 = call_expr_template.replace("DATA", arg2_name)
                else:
                    arg2 = arg2_name

                lambda_body = f"return self {op_name} {arg2};"
                f.write(
                    f'{indent}{class_var}.def("{pyname}", []({all_args}) {{ {lambda_body} }}{py_args_str});  // from global binary operator\n'
                )
        self._pop_cpp_scope()

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

        self._push_cpp_scope(namespace_prefix)
        params = func.get("parameters", [])
        param_sets = self._default_overload_parameter_sets(params)
        force_overloads = len(param_sets) > 1

        return_type = func.get("return_type", "void")
        full_func_name = f"{namespace_prefix}{func['name']}"

        for sub_params in param_sets:
            include_defaults = not force_overloads
            def_args = self._lambda_argument_string(sub_params)
            py_args_str = self._generate_py_args_string(sub_params, include_defaults=include_defaults)

            call_args = self._get_forward_call_arguments(sub_params)
            lambda_body = f"{full_func_name}({call_args})"

            return_sample = self._check_specific_return_type(return_type)
            if return_sample:
                lambda_body = return_sample[0].replace("DATA", lambda_body)

            if return_type != "void":
                lambda_body = f"return {lambda_body}"
            lambda_body = f"{lambda_body};"

            f.write(
                f'{indent}{module_var}.def("{func["name"]}", []({def_args}) {{ {lambda_body} }}{self._get_docstring_parse(func)}{py_args_str}); // Outer class function \n'
            )
        self._pop_cpp_scope()

    def _handle_free_operators(self, items, all_class_types, bind_map=None, namespace_prefix=""):
        if bind_map is None:
            bind_map = dict()

        for item in items:
            if item["kind"] == "NAMESPACE":
                ns_prefix = namespace_prefix + item["name"] + "::" if item["name"] else namespace_prefix
                self._handle_free_operators(item.get("children", []), all_class_types, bind_map, ns_prefix)
            elif item["kind"] == "FUNCTION_DECL":
                name = item.get("name", "")
                if not name.startswith("operator"):
                    continue

                if name in IGNORE_LIST:
                    print(f"Ignoring free operator in IGNORE_LIST: {namespace_prefix}{name}")
                    continue
                if self._should_ignore_function(item):
                    print(f"Ignoring free operator due to parameter type: {namespace_prefix}{name}")
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
                    pyname = UNARY_OPERATOR_MAP[name] if is_unary else BINARY_OPERATOR_MAP[name]
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

    def _emit_items(self, f, items, indent, module_var, namespace_prefix, globalfreeop_map=None):
        for item in items:
            if item["kind"] == "NAMESPACE":
                ns_name = item["name"]
                ns_var = ns_name if ns_name else "SELF"
                ns_cpp_prefix = namespace_prefix + (ns_name + "::" if ns_name else "")

                if ns_name:
                    ns_var_py = module_var + "_" + ns_var
                    f.write(f'{indent}auto {ns_var_py} = {module_var}.def_submodule("{ns_name}");\n')
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
                this_full = namespace_prefix + item["name"] if namespace_prefix else item["name"]
                if globalfreeop_map is not None and this_full in globalfreeop_map and globalfreeop_map[this_full]:
                    item = dict(item)
                    item["__bindfreeoperators__"] = globalfreeop_map[this_full]
                self._emit_cpp_class(f, item, indent, module_var, namespace_prefix)
            elif item["kind"] == "ENUM_DECL":
                self._emit_cpp_enum(f, item, indent, module_var, namespace_prefix)
            elif item["kind"] == "VAR_DECL":
                var_name = item["name"]
                if var_name in IGNORE_LIST:
                    print(f"Ignoring variable in IGNORE_LIST: {namespace_prefix}{var_name}")
                    continue

                if var_name == "None":
                    var_name = "None_"

                if item.get("readonly"):
                    full_var_name = item["value"]
                    f.write(f'{indent}{module_var}.attr("{var_name}") = {full_var_name};\n')
                else:
                    full_var_name = f"{namespace_prefix}{var_name}"
                    f.write(f'{indent}{module_var}.attr("{var_name}") = {full_var_name};\n')
            elif item["kind"] == "FUNCTION_DECL":
                if item.get("_skip_binding", False) or item.get("_bound_to_class", False):
                    continue

                name = item.get("name", "")
                if name in IGNORE_LIST:
                    print(f"Ignoring function in IGNORE_LIST: {namespace_prefix}{name}")
                    continue

                self._emit_cpp_function(f, item, indent, module_var, namespace_prefix)
