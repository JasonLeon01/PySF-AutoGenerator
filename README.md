# PySFML-AutoGenerator

This project automatically generates PyBind11 binding files for SFML 3.1.0, enabling Python developers to use SFML graphics library seamlessly.

## Prerequisites

### Software Requirements
- **Python**: Version 3.12
- **LLVM**: Must be installed on your system

## Setup Instructions
Download `SFML 3.1.0` source code from: https://github.com/SFML/SFML/archive/refs/tags/3.1.0.zip

Extract the downloaded zip file

Rename the extracted folder to `SFML`

- On Windows
    ```bash
    .\build.bat
    ```
- On macOS
    Download `output-source` and decompress it.
    ```bash
    chmod +x ./build.sh
    chmod +x ./ProjCMake.sh
    ./build.sh
    ```

## Additions Folder
The `Additions` folder contains additional binding code for declarations found in SFML's `.inl` files. These files follow the naming pattern `bind_{classname}_Addition.txt` and are automatically appended to the end of the generated binding code during the build process.

## Notes
- Ensure all prerequisites are properly installed before running the build script
- Make sure Python 3.12 is accessible via the `py -3.12` or `python3.12` command
- LLVM must be properly configured in your system PATH

## Troubleshooting
- Verify that LLVM is correctly installed and accessible
- Check that all Python dependencies are installed for the correct Python version (3.12)

### Common Errors
- **Error:** clang.cindex.LibclangError: [WinError 193] %1
    **Cause:**
    This usually happens when multiple `libclang.dll` files exist on your system, and Python loads the wrong one (e.g., a 32-bit version instead of the 64-bit LLVM version).

    **Solution:**
    1. Locate the correct `libclang.dll` in your LLVM installation (e.g.
    `C:\Program Files\LLVM\bin\libclang.dll`).
    2. Explicitly set the path in your script before using `clang.cindex`:
    ```python
    from clang.cindex import Config
    Config.set_library_file(r"C:\Program Files\LLVM\bin\libclang.dll")
    ```

## Licensing and Acknowledgements
This project, PySFML-AutoGenerator, is licensed under the MIT License.

### Acknowledgements
This project is built upon the excellent work of the following libraries, and we comply with their respective licensing terms:

- SFML (Simple and Fast Multimedia Library): Used as the core graphical library. SFML is distributed under the highly permissive Zlib License.

- pybind11: Used for automatic C++ to Python binding generation. pybind11 is distributed under the BSD 3-Clause License.

For the complete text of all third-party licenses and required notices, please see [THIRD-PARTY.txt](THIRD-PARTY.txt) in this repository.
