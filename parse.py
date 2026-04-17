import os
import sys
import shutil
from pathlib import Path
from clang import cindex
import PybindGen

hpp_root = "SFML/include"
includes = "-ISFML/include"
repo_root = "SFML"
parse_folders = ["Audio", "Graphics", "Network", "System", "Window"]
output_folder = "output"
cpp_version = "c++20"
python_version = "3.12.0"
common_module_name = "sf"
ignored_macros = [
    "SFML_GRAPHICS_API",
    "SFML_AUDIO_API",
    "SFML_NETWORK_API",
    "SFML_SYSTEM_API",
    "SFML_WINDOW_API",
]
REPLACE_TYPE = {
    "std::filesystem::path": "std::string",
}
SPECIFIC_TYPE = {
    "std::vector<std::vector<sf::String>>": ["std::vector<std::vector<std::string>>", "toVectorVectorUTF8String(DATA)"],
    "std::vector<sf::String>": ["std::vector<std::string>", "toVectorUTF8String(DATA)"],
    "sf::String": ["std::string", "toSFString(DATA)"],
    "void*": ["py::buffer", "static_cast<std::uint8_t*>(DATA.request().ptr)"],
    "short*": ["std::vector<short>&", "DATA.data()"],
    "int*": ["std::vector<int>&", "DATA.data()"],
    "float*": ["std::vector<float>&", "DATA.data()"],
    "std::int16_t*": ["std::vector<std::int16_t>&", "DATA.data()"],
    "std::uint8_t*": ["std::vector<std::uint8_t>&", "DATA.data()"],
    "sf::Vector2<float>*": ["std::vector<sf::Vector2<float>>&", "DATA.data()"],
    "sf::Vector3<float>*": ["std::vector<sf::Vector3<float>>&", "DATA.data()"],
    "sf::priv::Vector4<float>*": ["std::vector<sf::priv::Vector4<float>>&", "DATA.data()"],
    "sf::priv::Matrix<3, 3>*": ["std::vector<sf::priv::Matrix<3, 3>>&", "DATA.data()"],
    "sf::priv::Matrix<4, 4>*": ["std::vector<sf::priv::Matrix<4, 4>>&", "DATA.data()"],
    "sf::Vertex*": ["std::vector<sf::Vertex>&", "DATA.data()"],
    "unsigned char*": ["std::vector<std::uint8_t>&", "DATA.data()"],
    "char*": ["std::string&", "DATA.data()"],
    "wchar_t*": ["std::wstring&", "DATA.data()"],
    "WindowHandle": [
        "uintptr_t",
        "handleToSFMLHandle(DATA)",
    ],
}
IGNORE_TYPE = ["VkInstance_T*", "std::locale", "char32_t*"]
IGNORE_RETURN_TYPE = ["GlFunctionPointer"]
SPECIFIC_RETURN_TYPE = {
    "std::vector<std::vector<sf::String>>": ["toVectorVectorUTF8String(DATA)", "def_vector_vector_string_property"],
    "std::vector<sf::String>": ["toVectorUTF8String(DATA)", "def_vector_string_property"],
    "String": ["toUTF8String(DATA)", "def_string_property"],
    "WindowHandle": ["reinterpret_cast<uintptr_t>(DATA)", ""],
}
REPLACE_DEFAULT = {
    " = sf::Style::None": " = 0",
    " = sf::Style::Titlebar": " = 1 << 0",
    " = sf::Style::Resize": " = 1 << 1",
    " = sf::Style::Close": " = 1 << 2",
    " = sf::Style::Default": " = 7",
}
IGNORED_MODULE = ["priv"]
TAB_STR = "    "
SPECIAL_REPLACE = {
    (
        "v_sfRenderTexture",
        '"getTexture"',
    ): '{}v_sfRenderTexture.def("getTexture", [](sf::RenderTexture &self) -> const sf::Texture& {{ return self.getTexture(); }},"{}", py::return_value_policy::reference_internal);'.format(
        TAB_STR,
        "\\n".join(
            [
                "\\\\brief Get a read-only reference to the target texture",
                "",
                "After drawing to the render-texture and calling Display,",
                "you can retrieve the updated texture using this function,",
                "and draw it using a sprite (for example).",
                "The internal `sf::Texture` of a render-texture is always the",
                "same instance, so that it is possible to call this function",
                "once and keep a reference to the texture even after it is",
                "modified.",
                "",
                "\\\\return Const reference to the texture",
            ]
        ),
    ),
    (
        "v_sfTransform",
        '"getMatrix"',
    ): '{}v_sfTransform.def("getMatrix", [](sf::Transform& self) {{ const float* m = self.getMatrix(); return std::vector<float>(m, m + 16); }},"{}");'.format(
        TAB_STR,
        "\\n".join(
            [
                "\\\\brief Return the transform as a 4x4 matrix",
                "",
                "This function returns a pointer to an array of 16 floats",
                "containing the transform elements as a 4x4 matrix, which",
                "is directly compatible with OpenGL functions.",
                "\\\\code",
                "sf::Transform transform = ...;",
                "glLoadMatrixf(transform.getMatrix());",
                "\\\\endcode",
                "",
                "\\\\return Pointer to a 4x4 matri",
            ]
        ),
    ),
    (
        "v_sfImage",
        '"getPixelsPtr"',
    ): '{}v_sfImage.def("getPixelsArray", [](sf::Image& self) {{ const std::uint8_t* pixels = self.getPixelsPtr(); auto size = self.getSize(); return std::vector<std::uint8_t>(pixels, pixels + size.x * size.y * 4); }}, "{}"); // Return a copy of the pixels array, the original method is getPixelsPtr()'.format(
        TAB_STR,
        "\\n".join(
            [
                "\\\\brief Get a read-only pointer to the array of pixels",
                "",
                "The returned value points to an array of RGBA pixels made of",
                "8 bit integer components. The size of the array is",
                "`width * height * 4 (getSize().x * getSize().y * 4)`.",
                "Warning: the returned pointer may become invalid if you",
                "modify the image, so you should never store it for too long.",
                "If the image is empty, a null pointer is returned.",
                "",
                "\\\\return Read-only pointer to the array of pixels",
            ]
        ),
    ),
    (
        "v_sfShader",
        "py::init<std::string, sf::Shader::Type>()",
    ): f"{TAB_STR}// Pass construction from memory GLSL code text.",
    (
        "v_sfShader",
        "py::init<std::string, std::string>()",
    ): f"{TAB_STR}// Pass construction from memory GLSL code text.",
    (
        "v_sfShader",
        "py::init<std::string, std::string, std::string>()",
    ): f"{TAB_STR}// Pass construction from memory GLSL code text.",
    (
        "v_sfPacket",
        '"__rshift__", [](sf::Packet& self, std::string data)',
    ): f"{TAB_STR}// Pass std::string data to sf::Packet.__rshift__",
}
READWRITE_IGNORE = {"sf::SoundStream::Chunk": ["samples"]}

SELF_INCLUDE_FILES = [
    "./include/string_utils.hpp",
    "./include/wrap_utils.hpp",
    "./include/utils.hpp",
    "./include/bind_Vector.hpp",
    "./include/bind_Rect.hpp",
    "./include/bind_Matrix.hpp",
    "./include/bind_Handle.hpp",
    "./include/bind_Drawable.hpp",
]


hpp_excludes = {
    "Audio": [
        "AudioResource.hpp",
        "Export.hpp",
        "SoundFileFactory.hpp",
    ],
    "Graphics": [
        "Drawable.hpp",
        "Export.hpp",
        "Glsl.hpp",
        "Rect.hpp",
    ],
    "Network": [
        "Export.hpp",
        "SocketHandle.hpp",
    ],
    "System": [
        "Err.hpp",
        "Exception.hpp",
        "Export.hpp",
        "NativeActivity.hpp",
        "String.hpp",
        "SuspendAwareClock.hpp",
        "Utf.hpp",
        "Vector2.hpp",
        "Vector3.hpp",
    ],
    "Window": [
        "Export.hpp",
        "GlResource.hpp",
        "Vulkan.hpp",
    ],
}


if __name__ == "__main__":
    project_root = os.path.abspath(".")
    hpp_folders = PybindGen.scan_hpp_files(hpp_root, repo_root, parse_folders)
    shutil.rmtree(output_folder, ignore_errors=True)
    for folder, hpp_files in hpp_folders.items():
        output_hpp = os.path.join(project_root, output_folder, "include", folder)
        output_cpp = os.path.join(project_root, output_folder, "src", folder)
        if not os.path.exists(output_cpp):
            os.makedirs(output_cpp)
        if not os.path.exists(output_hpp):
            os.makedirs(output_hpp)
        for hpp_file in hpp_files:
            if hpp_file in hpp_excludes.get(folder, []):
                print(f"Skipping {hpp_file}")
                continue
            print(f"Processing {hpp_file}")
            read_file = os.path.join(project_root, hpp_root, repo_root, folder, hpp_file)
            output_file = os.path.join(project_root, output_cpp, f"bind_{hpp_file.split('.')[0]}.cpp")
            PybindGen.generate_binding_from_hpp(
                common_module_name,
                hpp_root,
                read_file,
                output_file,
                includes,
                cpp_version,
                ignored_macros,
                REPLACE_TYPE,
                SPECIFIC_TYPE,
                IGNORE_TYPE,
                IGNORE_RETURN_TYPE,
                SPECIFIC_RETURN_TYPE,
                REPLACE_DEFAULT,
                IGNORED_MODULE,
                SPECIAL_REPLACE,
                READWRITE_IGNORE,
            )
            PybindGen.generate_hpp_file_from_hpp(
                read_file,
                hpp_file,
                os.path.join(project_root, output_hpp, f"bind_{hpp_file}"),
            )

    headers_to_sort = []
    project_include_paths = [os.path.join(project_root, hpp_root)]
    for folder, hpp_files in hpp_folders.items():
        for hpp_file in hpp_files:
            if hpp_file in hpp_excludes.get(folder, []):
                print(f"Skipping {hpp_file}")
                continue

            headers_to_sort.append(os.path.join(project_root, hpp_root, repo_root, folder, hpp_file))

    if not headers_to_sort:
        print("No header files found to sort. Exiting.")
        sys.exit(0)

    print(f"Found {len(headers_to_sort)} header files to sort.")
    try:
        sorter = PybindGen.Sorter(headers_to_sort, project_include_paths, cpp_version)
        sorter.build_graph()
        for node, deps in sorter.dependency_graph.items():
            if deps:
                print(f"  {os.path.basename(node)} -> {[os.path.basename(d) for d in deps]}")
        sorted_files = sorter.sort()

    except (RuntimeError, cindex.LibclangError) as e:
        print(f"\nAn error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

    to_write_files = []
    for file in SELF_INCLUDE_FILES:
        file_name = Path(file).name
        to_write_files.append(file_name)
    for file in sorted_files:
        file_name_path = Path(file).parts[-2:]
        parent, file_name = file_name_path
        flag = False
        for folder, hpp_files in hpp_excludes.items():
            if file_name in hpp_files:
                flag = True
                print(f"Found {file_name} in {folder}, skipping")
                break

        if flag:
            continue
        to_write_files.append(f"{parent}/bind_{file_name}")

    print(f"Writing {len(to_write_files)} files to include folder.")

    to_write_files.remove("bind_Vector.hpp")
    to_write_files.insert(to_write_files.index("System/bind_Angle.hpp") + 1, "bind_Vector.hpp")
    PybindGen.generate_pybind_main(
        to_write_files,
        os.path.join(project_root, output_folder, "main.cpp"),
    )
    PybindGen.generate_cmakelists(to_write_files, SELF_INCLUDE_FILES, python_version)
