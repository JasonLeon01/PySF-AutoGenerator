import os
import sys
from collections import defaultdict, deque

from clang import cindex


TYPE_DEFINITION_KINDS = (
    cindex.CursorKind.CLASS_DECL,
    cindex.CursorKind.STRUCT_DECL,
    cindex.CursorKind.UNION_DECL,
    cindex.CursorKind.ENUM_DECL,
    cindex.CursorKind.TYPEDEF_DECL,
)

BUILTIN_TYPE_KINDS = (
    cindex.TypeKind.VOID,
    cindex.TypeKind.BOOL,
    cindex.TypeKind.CHAR_U,
    cindex.TypeKind.UCHAR,
    cindex.TypeKind.CHAR16,
    cindex.TypeKind.CHAR32,
    cindex.TypeKind.USHORT,
    cindex.TypeKind.UINT,
    cindex.TypeKind.ULONG,
    cindex.TypeKind.ULONGLONG,
    cindex.TypeKind.UINT128,
    cindex.TypeKind.CHAR_S,
    cindex.TypeKind.SCHAR,
    cindex.TypeKind.WCHAR,
    cindex.TypeKind.SHORT,
    cindex.TypeKind.INT,
    cindex.TypeKind.LONG,
    cindex.TypeKind.LONGLONG,
    cindex.TypeKind.INT128,
    cindex.TypeKind.FLOAT,
    cindex.TypeKind.DOUBLE,
    cindex.TypeKind.LONGDOUBLE,
)


class Sorter:
    def __init__(self, header_paths, translation_unit):
        self.header_files = {self._normalise_path(path) for path in header_paths}
        self.translation_unit = translation_unit
        self.dependency_graph = {header: set() for header in self.header_files}
        self.dependents_graph = {header: set() for header in self.header_files}
        self.type_definitions = {}
        self.strong_dependencies = defaultdict(set)
        self.weak_dependencies = defaultdict(set)
        self.self_references = defaultdict(int)

    @staticmethod
    def _normalise_path(path):
        return os.path.abspath(path)

    def _cursor_file(self, cursor):
        if not cursor.location or not cursor.location.file:
            return None
        return self._normalise_path(cursor.location.file.name)

    def _get_qualified_name(self, cursor):
        if cursor is None:
            return None

        parts = []
        current = cursor
        while current is not None and current.kind != cindex.CursorKind.TRANSLATION_UNIT:
            if current.spelling:
                parts.append(current.spelling)
            parent = current.semantic_parent
            if parent is None or parent == current:
                break
            current = parent
        return "::".join(reversed(parts)) or None

    def _get_type_qualified_name(self, type_obj):
        if type_obj is None or type_obj.kind == cindex.TypeKind.INVALID:
            return None

        canonical_type = type_obj.get_canonical()
        type_decl = canonical_type.get_declaration()
        qualified_name = self._get_qualified_name(type_decl)
        if qualified_name:
            return qualified_name

        type_spelling = canonical_type.spelling
        if not type_spelling:
            return None
        if "<" in type_spelling:
            type_spelling = type_spelling.split("<", 1)[0]
        return type_spelling.replace("const ", "").replace("volatile ", "").strip()

    @staticmethod
    def _requires_complete_type(type_obj):
        if type_obj is None or type_obj.kind == cindex.TypeKind.INVALID:
            return False

        canonical_type = type_obj.get_canonical()
        if canonical_type.kind in (
            cindex.TypeKind.POINTER,
            cindex.TypeKind.LVALUEREFERENCE,
        ):
            return False
        if canonical_type.kind in BUILTIN_TYPE_KINDS:
            return False

        try:
            canonical_type.get_size()
            return True
        except cindex.TypeLayoutError as error:
            return error.code != cindex.TypeLayoutError.INCOMPLETE

    def _collect_type_definitions(self):
        print("Collecting type definitions from shared AST...")
        for cursor in self.translation_unit.cursor.walk_preorder():
            current_file = self._cursor_file(cursor)
            if current_file not in self.header_files or cursor.kind not in TYPE_DEFINITION_KINDS:
                continue

            if cursor.kind == cindex.CursorKind.TYPEDEF_DECL:
                is_definition = True
            else:
                definition = cursor.get_definition()
                is_definition = definition is not None and definition == cursor
            if not is_definition:
                continue

            qualified_name = self._get_qualified_name(cursor)
            if not qualified_name:
                continue
            self.type_definitions[qualified_name] = current_file

            simple_name = cursor.spelling
            if simple_name and simple_name != qualified_name:
                self.type_definitions[f"{current_file}::{simple_name}"] = current_file

    def _find_type_definition_file(self, type_qualified_name, current_file):
        if not type_qualified_name:
            return None
        if type_qualified_name in self.type_definitions:
            return self.type_definitions[type_qualified_name]

        if "::" in type_qualified_name:
            parts = type_qualified_name.split("::")
            for index in range(len(parts)):
                partial_name = "::".join(parts[index:])
                if partial_name in self.type_definitions:
                    return self.type_definitions[partial_name]

        simple_name = type_qualified_name.rsplit("::", 1)[-1]
        fallback_key = f"{current_file}::{simple_name}"
        if fallback_key in self.type_definitions:
            return None

        for key, file_path in self.type_definitions.items():
            if file_path != current_file and (key.endswith(f"::{simple_name}") or key == simple_name):
                return file_path
        return None

    def _collect_transitive_include_dependencies(self):
        include_graph = defaultdict(set)
        for cursor in self.translation_unit.cursor.get_children():
            if cursor.kind != cindex.CursorKind.INCLUSION_DIRECTIVE:
                continue
            owner = self._cursor_file(cursor)
            included_file = cursor.get_included_file()
            if owner is None or included_file is None:
                continue
            include_graph[owner].add(self._normalise_path(included_file.name))

        for header_file in self.header_files:
            pending = list(include_graph.get(header_file, ()))
            visited = set()
            while pending:
                included_file = pending.pop()
                if included_file in visited:
                    continue
                visited.add(included_file)
                pending.extend(include_graph.get(included_file, ()))

            for dependency_file in visited.intersection(self.header_files):
                if dependency_file == header_file:
                    self.self_references[header_file] += 1
                else:
                    self.strong_dependencies[header_file].add(dependency_file)

    def _remember_dependency(self, current_file, dependency_file, strong):
        if dependency_file is None:
            return
        dependency_file = self._normalise_path(dependency_file)
        if dependency_file not in self.header_files:
            return
        if dependency_file == current_file:
            self.self_references[current_file] += 1
            return
        if strong:
            self.strong_dependencies[current_file].add(dependency_file)
        else:
            self.weak_dependencies[current_file].add(dependency_file)

    def _dependency_for_type(self, type_obj, current_file):
        type_name = self._get_type_qualified_name(type_obj)
        return self._find_type_definition_file(type_name, current_file)

    def _analyze_type_dependencies(self):
        print("Analyzing dependencies from shared AST...")
        for cursor in self.translation_unit.cursor.walk_preorder():
            current_file = self._cursor_file(cursor)
            if current_file not in self.header_files:
                continue

            if cursor.kind == cindex.CursorKind.CXX_BASE_SPECIFIER:
                definition = cursor.get_definition()
                dependency_file = self._cursor_file(definition) if definition is not None else None
                if dependency_file is None:
                    dependency_file = self._dependency_for_type(cursor.type, current_file)
                if dependency_file is None and cursor.spelling:
                    raw_name = cursor.spelling
                    for prefix in ("class ", "struct "):
                        if raw_name.startswith(prefix):
                            raw_name = raw_name[len(prefix) :]
                            break
                    dependency_file = self._find_type_definition_file(raw_name, current_file)
                self._remember_dependency(current_file, dependency_file, True)

            elif cursor.kind == cindex.CursorKind.FIELD_DECL:
                self._remember_dependency(
                    current_file,
                    self._dependency_for_type(cursor.type, current_file),
                    self._requires_complete_type(cursor.type),
                )

            elif cursor.kind == cindex.CursorKind.VAR_DECL:
                if self._requires_complete_type(cursor.type):
                    self._remember_dependency(
                        current_file,
                        self._dependency_for_type(cursor.type, current_file),
                        True,
                    )

            elif cursor.kind in (
                cindex.CursorKind.CXX_METHOD,
                cindex.CursorKind.FUNCTION_DECL,
            ):
                if self._requires_complete_type(cursor.result_type):
                    self._remember_dependency(
                        current_file,
                        self._dependency_for_type(cursor.result_type, current_file),
                        True,
                    )
                for argument in cursor.get_arguments() or ():
                    if self._requires_complete_type(argument.type):
                        self._remember_dependency(
                            current_file,
                            self._dependency_for_type(argument.type, current_file),
                            True,
                        )

    def build_graph(self):
        errors = [
            diagnostic
            for diagnostic in self.translation_unit.diagnostics
            if diagnostic.severity >= cindex.Diagnostic.Error
            and "incomplete type" not in diagnostic.spelling.lower()
        ]
        if errors:
            details = "\n".join(f"  - {diagnostic}" for diagnostic in errors)
            raise RuntimeError(f"Clang failed to parse the shared SFML translation unit:\n{details}")

        print("Building dependency graph from shared translation unit...")
        self._collect_type_definitions()
        self._collect_transitive_include_dependencies()
        self._analyze_type_dependencies()

        for header_file in self.header_files:
            for dependency_file in self.strong_dependencies[header_file]:
                if dependency_file != header_file:
                    self.dependency_graph[header_file].add(dependency_file)
                    self.dependents_graph[dependency_file].add(header_file)
        print("Dependency graph construction complete.")

    def sort(self):
        print("Performing topological sort...")
        in_degree = {node: len(self.dependency_graph[node]) for node in self.header_files}
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        sorted_list = []

        while queue:
            current_node = queue.popleft()
            sorted_list.append(current_node)
            for dependent in self.dependents_graph.get(current_node, ()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(sorted_list) != len(self.header_files):
            circular_nodes = {node for node, degree in in_degree.items() if degree > 0}
            print("Error: Circular dependency detected in strong dependencies!", file=sys.stderr)
            for node in circular_nodes:
                dependencies = self.dependency_graph[node].intersection(circular_nodes)
                print(
                    f"  - {os.path.basename(node)} depends on: "
                    f"{[os.path.basename(dependency) for dependency in dependencies]}",
                    file=sys.stderr,
                )
            raise RuntimeError("Circular dependency detected! Cannot sort.")

        print("Topological sort complete.")
        return sorted_list
