# PySFML-AutoGenerator

This project automatically generates PyBind11 binding files for SFML 3.0.1, enabling Python developers to use SFML graphics library seamlessly.

## Prerequisites

### Software Requirements
- **CMake**: Version < 4.0
- **Python**: Version 3.10.0
- **LLVM**: Must be installed on your system

### Python Dependencies
Install the required Python packages:
```bash
py -3.10 -m pip install clang pybind11-stubgen
```

## Setup Instructions

### 1. Clone PyBind11
Clone the PyBind11 repository into your project folder:
```bash
git clone https://github.com/pybind/pybind11.git
```

### 2. Download SFML Source Code
1. Download SFML 3.0.1 source code from: https://github.com/SFML/SFML/archive/refs/tags/3.0.1.zip
2. Extract the downloaded zip file
3. Rename the extracted folder to `SFML`
4. Place it in your project directory

### 3. Project Structure
After completing the setup, your project directory should look like this:
```
your-project/
├── pybind11/          # Cloned PyBind11 repository
├── SFML/              # Renamed SFML source folder
├── build.bat          # Build script
└── [other project files]
```


### 4. Additions Folder
The `Additions` folder contains additional binding code for declarations found in SFML's `.inl` files. These files follow the naming pattern `bind_{classname}_Addition.txt` and are automatically appended to the end of the generated binding code during the build process.

## Building
### If on Windows
Execute the `build.bat` build script to generate the binding files.

If you already have **output files**, you can just run `ProjCMake.bat` to start CMake process.

When the build is complete, the binding files will be located in the `result` folder.

### If on macOS
Source building is not supported on macOS yet. You can download `output-source` and decompress it.

Then, run `ProjCMake.sh` to start CMake process.

## Notes
- Ensure all prerequisites are properly installed before running the build script
- Make sure Python 3.10.0 is accessible via the `py -3.10` command
- LLVM must be properly configured in your system PATH

## Known Limitations
- Clang/LLVM compile checks currently fail due to attempts to bind rvalues to `sf::String&` (non-const reference), resulting in errors such as `invalid operands to binary expression`. The current auto-generated binding code includes such cases and requires adjustments.
- Visual Studio 2026 (`VS2026`) is currently not supported for CMake builds.

## Troubleshooting
- If you encounter CMake version issues, ensure you're using a version less than 4.0
- Verify that LLVM is correctly installed and accessible
- Check that all Python dependencies are installed for the correct Python version (3.10.0)

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
