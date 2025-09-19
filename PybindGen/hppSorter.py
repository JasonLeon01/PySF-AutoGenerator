import os
import sys
from collections import deque, defaultdict
from clang import cindex


class Sorter:
    def __init__(self, header_paths, include_dirs, cpp_version):
        self.header_files = {os.path.abspath(p) for p in header_paths}
        self.clang_args = []
        for d in include_dirs:
            self.clang_args.append(f"-I{os.path.abspath(d)}")
        self.clang_args.append(f"-std={cpp_version}")
        self.clang_args.append("-x")
        self.clang_args.append("c++-header")
        self.clang_args.append("-fno-delayed-template-parsing")

        print("Clang arguments for parsing:")
        for arg in self.clang_args:
            print(f"  {arg}")
        print("-" * 20)

        self.dependency_graph = {h: set() for h in self.header_files}
        self.dependents_graph = {h: set() for h in self.header_files}

        self.type_definitions = {}

        self.strong_dependencies = defaultdict(set)
        self.weak_dependencies = defaultdict(set)

        self.self_references = defaultdict(int)

    def _is_in_project_headers(self, path):
        if not path:
            return False
        return os.path.abspath(path) in self.header_files

    def _get_qualified_name(self, cursor):
        try:
            if not cursor:
                return None

            parts = []
            current = cursor

            while current:
                if current.spelling:
                    parts.append(current.spelling)

                parent = current.semantic_parent
                if not parent or parent.kind == cindex.CursorKind.TRANSLATION_UNIT or parent == current:
                    break
                current = parent

            if not parts:
                return None

            parts.reverse()
            qualified_name = "::".join(parts)
            return qualified_name

        except Exception:
            return cursor.spelling if cursor and cursor.spelling else None

    def _get_type_qualified_name(self, type_obj):
        try:
            if not type_obj:
                return None

            canonical_type = type_obj.get_canonical()

            type_decl = canonical_type.get_declaration()
            if type_decl:
                qualified_name = self._get_qualified_name(type_decl)
                if qualified_name:
                    return qualified_name

            type_spelling = canonical_type.spelling
            if not type_spelling:
                return None

            if "<" in type_spelling:
                type_spelling = type_spelling.split("<")[0]

            type_spelling = type_spelling.replace("const ", "").replace("volatile ", "").strip()

            return type_spelling

        except Exception:
            return None

    def _requires_complete_type(self, type_obj):
        try:
            if not type_obj:
                return False

            canonical_type = type_obj.get_canonical()

            if canonical_type.kind in (
                cindex.TypeKind.POINTER,
                cindex.TypeKind.LVALUEREFERENCE,
            ):
                return False

            if canonical_type.kind in (
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
            ):
                return False

            try:
                _ = canonical_type.get_size()
                return True
            except cindex.TypeLayoutError as e:
                if e.code == cindex.TypeLayoutError.INCOMPLETE:
                    return False
                return True

        except Exception:
            return False

    def _collect_type_definitions(self, translation_unit):
        try:
            current_file_path = os.path.abspath(translation_unit.spelling)

            for cursor in translation_unit.cursor.walk_preorder():
                try:
                    if not cursor or not cursor.location or not cursor.location.file:
                        continue

                    cursor_file_path = os.path.abspath(cursor.location.file.name)
                    if cursor_file_path != current_file_path:
                        continue

                    if cursor.kind in (
                        cindex.CursorKind.CLASS_DECL,
                        cindex.CursorKind.STRUCT_DECL,
                        cindex.CursorKind.UNION_DECL,
                        cindex.CursorKind.ENUM_DECL,
                        cindex.CursorKind.TYPEDEF_DECL,
                    ):

                        is_definition = False
                        try:
                            if cursor.kind == cindex.CursorKind.TYPEDEF_DECL:
                                is_definition = True
                            else:
                                definition = cursor.get_definition()
                                is_definition = definition and definition == cursor
                        except:
                            continue

                        if is_definition:
                            qualified_name = self._get_qualified_name(cursor)
                            if qualified_name:
                                self.type_definitions[qualified_name] = current_file_path
                                print(
                                    f"    Found type definition: {qualified_name} in {os.path.basename(current_file_path)}"
                                )

                                simple_name = cursor.spelling
                                if simple_name and simple_name != qualified_name:
                                    fallback_key = f"{current_file_path}::{simple_name}"
                                    self.type_definitions[fallback_key] = current_file_path

                except Exception:
                    continue

        except Exception as e:
            print(f"    Warning: Error collecting type definitions: {e}")

    def _find_type_definition_file(self, type_qualified_name, current_file):
        if not type_qualified_name:
            return None

        if type_qualified_name in self.type_definitions:
            return self.type_definitions[type_qualified_name]

        if "::" in type_qualified_name:
            parts = type_qualified_name.split("::")
            for i in range(len(parts)):
                partial_name = "::".join(parts[i:])
                if partial_name in self.type_definitions:
                    return self.type_definitions[partial_name]

        simple_name = type_qualified_name.split("::")[-1] if "::" in type_qualified_name else type_qualified_name
        fallback_key = f"{current_file}::{simple_name}"

        for key, file_path in self.type_definitions.items():
            if (key.endswith(f"::{simple_name}") or key == simple_name) and file_path != current_file:
                if fallback_key in self.type_definitions:
                    continue
                return file_path

        return None

    def _analyze_dependencies(self, translation_unit):
        try:
            current_file_path = os.path.abspath(translation_unit.spelling)

            for cursor in translation_unit.cursor.get_children():
                try:
                    if cursor and cursor.kind == cindex.CursorKind.INCLUSION_DIRECTIVE:
                        included_file = cursor.get_included_file()
                        if included_file and self._is_in_project_headers(included_file.name):
                            included_path = os.path.abspath(included_file.name)

                            if included_path == current_file_path:
                                self.self_references[current_file_path] += 1
                                print(
                                    f"    Self-reference detected: {os.path.basename(current_file_path)} includes itself (ignored)"
                                )
                                continue

                            self.strong_dependencies[current_file_path].add(included_path)
                            print(
                                f"    Direct include: {os.path.basename(current_file_path)} -> {os.path.basename(included_path)}"
                            )
                except:
                    continue

            for cursor in translation_unit.cursor.walk_preorder():
                try:
                    if not cursor or not cursor.location or not cursor.location.file:
                        continue

                    cursor_file_path = os.path.abspath(cursor.location.file.name)
                    if cursor_file_path != current_file_path:
                        continue

                    dependency_file = None
                    is_strong_dependency = False

                    if cursor.kind == cindex.CursorKind.CXX_BASE_SPECIFIER:
                        definition = cursor.get_definition()
                        if definition and definition.location and definition.location.file:
                            dependency_file = os.path.abspath(definition.location.file.name)
                            is_strong_dependency = True
                            base_class_name = self._get_qualified_name(definition)
                            print(
                                f"    Inheritance dependency: {os.path.basename(current_file_path)} -> {os.path.basename(dependency_file)} (inherits from {base_class_name})"
                            )

                    elif cursor.kind == cindex.CursorKind.FIELD_DECL:
                        if cursor.type and self._requires_complete_type(cursor.type):
                            type_qualified_name = self._get_type_qualified_name(cursor.type)
                            if type_qualified_name:
                                dependency_file = self._find_type_definition_file(
                                    type_qualified_name, current_file_path
                                )
                                if dependency_file:
                                    is_strong_dependency = True
                                    print(
                                        f"    Field dependency (complete type): {os.path.basename(current_file_path)} -> {os.path.basename(dependency_file)} (field {cursor.spelling}: {type_qualified_name})"
                                    )
                        elif cursor.type:
                            type_qualified_name = self._get_type_qualified_name(cursor.type)
                            if type_qualified_name:
                                dependency_file = self._find_type_definition_file(
                                    type_qualified_name, current_file_path
                                )
                                if dependency_file:
                                    is_strong_dependency = False
                                    print(
                                        f"    Field dependency (forward decl): {os.path.basename(current_file_path)} -> {os.path.basename(dependency_file)} (field {cursor.spelling}: {type_qualified_name}*)"
                                    )

                    elif cursor.kind in (cindex.CursorKind.VAR_DECL,):
                        if cursor.type and self._requires_complete_type(cursor.type):
                            type_qualified_name = self._get_type_qualified_name(cursor.type)
                            if type_qualified_name:
                                dependency_file = self._find_type_definition_file(
                                    type_qualified_name, current_file_path
                                )
                                if dependency_file:
                                    is_strong_dependency = True
                                    print(
                                        f"    Variable dependency: {os.path.basename(current_file_path)} -> {os.path.basename(dependency_file)} (var {cursor.spelling}: {type_qualified_name})"
                                    )

                    elif cursor.kind in (
                        cindex.CursorKind.CXX_METHOD,
                        cindex.CursorKind.FUNCTION_DECL,
                    ):
                        if cursor.result_type and self._requires_complete_type(cursor.result_type):
                            type_qualified_name = self._get_type_qualified_name(cursor.result_type)
                            if type_qualified_name:
                                dependency_file = self._find_type_definition_file(
                                    type_qualified_name, current_file_path
                                )
                                if dependency_file:
                                    is_strong_dependency = True
                                    print(
                                        f"    Function return type dependency: {os.path.basename(current_file_path)} -> {os.path.basename(dependency_file)} (function {cursor.spelling} returns {type_qualified_name})"
                                    )

                        try:
                            for arg_cursor in cursor.get_children():
                                if (
                                    arg_cursor
                                    and arg_cursor.kind == cindex.CursorKind.PARM_DECL
                                    and arg_cursor.type
                                    and self._requires_complete_type(arg_cursor.type)
                                ):
                                    type_qualified_name = self._get_type_qualified_name(arg_cursor.type)
                                    if type_qualified_name:
                                        param_dep_file = self._find_type_definition_file(
                                            type_qualified_name, current_file_path
                                        )
                                        if (
                                            param_dep_file
                                            and param_dep_file != current_file_path
                                            and self._is_in_project_headers(param_dep_file)
                                        ):
                                            self.strong_dependencies[current_file_path].add(param_dep_file)
                                            print(
                                                f"    Function parameter dependency: {os.path.basename(current_file_path)} -> {os.path.basename(param_dep_file)} (param {arg_cursor.spelling}: {type_qualified_name})"
                                            )
                        except:
                            continue

                    if (
                        dependency_file
                        and dependency_file != current_file_path
                        and self._is_in_project_headers(dependency_file)
                    ):
                        if dependency_file == current_file_path:
                            self.self_references[current_file_path] += 1
                            print(
                                f"    Self-dependency detected: {os.path.basename(current_file_path)} depends on itself (ignored)"
                            )
                            continue

                        if is_strong_dependency:
                            self.strong_dependencies[current_file_path].add(dependency_file)
                        else:
                            self.weak_dependencies[current_file_path].add(dependency_file)

                except Exception:
                    continue

        except Exception as e:
            print(f"    Warning: Error analyzing dependencies: {e}")

    def build_graph(self):
        index = cindex.Index.create()
        print("Building dependency graph...")

        print("\nPhase 1: Collecting type definitions...")
        tus = {}
        for header_file in self.header_files:
            print(f"  Analyzing {os.path.basename(header_file)}...")
            try:
                tus[header_file] = index.parse(
                    header_file,
                    args=self.clang_args,
                    options=cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD,
                )
                if not tus[header_file]:
                    print(f"Warning: Failed to parse {header_file}", file=sys.stderr)
                    continue

                self._collect_type_definitions(tus[header_file])

            except Exception as e:
                print(f"Error while parsing {header_file}: {e}", file=sys.stderr)

        print("\nPhase 2: Analyzing dependencies...")
        for header_file in self.header_files:
            print(f"  Processing dependencies for {os.path.basename(header_file)}...")
            try:
                if not tus[header_file]:
                    continue

                has_errors = False
                for diag in tus[header_file].diagnostics:
                    if diag.severity >= cindex.Diagnostic.Error:
                        if "incomplete type" not in diag.spelling.lower():
                            print(
                                f"Error parsing {header_file}: {diag.spelling}",
                                file=sys.stderr,
                            )
                            has_errors = True
                if has_errors:
                    print(
                        f"  Skipping dependency analysis for {header_file} due to critical parsing errors.",
                        file=sys.stderr,
                    )
                    continue

                self._analyze_dependencies(tus[header_file])

            except Exception as e:
                print(f"Error while processing {header_file}: {e}", file=sys.stderr)

        print("\nPhase 3: Building final dependency graph (strong dependencies only, self-references filtered)...")
        for header_file in self.header_files:
            strong_deps = self.strong_dependencies[header_file]
            for dep_file in strong_deps:
                if dep_file != header_file:
                    self.dependency_graph[header_file].add(dep_file)
                    self.dependents_graph[dep_file].add(header_file)
                else:
                    self.self_references[header_file] += 1

        print("\nGraph construction complete.\n")

        if any(count > 0 for count in self.self_references.values()):
            print("Self-reference summary:")
            for header_file, count in self.self_references.items():
                if count > 0:
                    print(f"  {os.path.basename(header_file)}: {count} self-references filtered")
            print()

        print("Final dependency relationships (strong dependencies only, self-references excluded):")
        for header_file in self.header_files:
            strong_deps = self.strong_dependencies[header_file] - {header_file}
            weak_deps = self.weak_dependencies[header_file] - {header_file}

            if strong_deps:
                print(f"  {os.path.basename(header_file)} strongly depends on:")
                for dep in strong_deps:
                    print(f"    - {os.path.basename(dep)}")

            if weak_deps:
                print(f"  {os.path.basename(header_file)} weakly depends on (forward declarations):")
                for dep in weak_deps:
                    print(f"    - {os.path.basename(dep)}")

    def sort(self):
        print("\nPerforming topological sort (based on strong dependencies only, self-references excluded)...")
        in_degree = {node: len(self.dependency_graph[node]) for node in self.header_files}
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        sorted_list = []

        while queue:
            current_node = queue.popleft()
            sorted_list.append(current_node)

            for dependent in self.dependents_graph.get(current_node, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(sorted_list) != len(self.header_files):
            circular_nodes = {node for node, degree in in_degree.items() if degree > 0}
            print(
                "Error: Circular dependency detected in strong dependencies!",
                file=sys.stderr,
            )
            print(
                "Involved files:",
                {os.path.basename(f) for f in circular_nodes},
                file=sys.stderr,
            )
            for node in circular_nodes:
                deps = self.dependency_graph[node].intersection(circular_nodes)
                print(
                    f"  - {os.path.basename(node)} depends on: {[os.path.basename(d) for d in deps]}",
                    file=sys.stderr,
                )

            print("\nPossible solutions:", file=sys.stderr)
            print(
                "1. Use forward declarations instead of #include where possible",
                file=sys.stderr,
            )
            print("2. Move some class definitions to separate files", file=sys.stderr)
            print(
                "3. Use pointer/reference types instead of value types for member variables",
                file=sys.stderr,
            )

            raise RuntimeError("Circular dependency detected! Cannot sort.")

        print("Topological sort complete.\n")
        return sorted_list
