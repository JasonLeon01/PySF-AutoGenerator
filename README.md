# PySFML-AutoGenerator

This project automatically generates PyBind11 binding files for SFML, enabling Python developers to use SFML graphics library seamlessly.

## Prerequisites

### Software Requirements
- **Python**: Version configured by `PYTHON_VERSION` in `versions.conf`
- **LLVM**: Must be installed on your system

## Setup Instructions
Configure `SFML_VERSION` and `PYTHON_VERSION` in `versions.conf`. The init scripts download the matching SFML source into `SFML/` if it is not already present.

- On Windows
    ```bash
    .\init.bat
    .\build.bat
    .\collect.bat
    ```
- On macOS
    Download `output-source` and decompress it.
    ```bash
    chmod +x *.sh
    ./init.sh
    ./build.sh
    ./collect.sh
    ```

    Output will be in `output/result/pysf/`.

- On iOS (cross-compile from macOS)

    **Requirements:**
    - macOS with Xcode installed (including iOS SDK)
    - A Python static library built for iOS arm64 matching `PYTHON_VERSION`

    **Step 1: Prepare iOS Python framework**

    Create the `ios_python` directory in the project root and place an iOS build matching `PYTHON_VERSION` inside it.

    Option A - [Python-Apple-support](https://github.com/beeware/Python-Apple-support/releases) (recommended):
    ```bash
    mkdir -p ios_python
    # Download Python-${PYTHON_VERSION}-iOS-support.b*.tar.gz
    tar xzf Python-${PYTHON_VERSION}-iOS-support.*.tar.gz -C ios_python/
    ```
    Expected layout: `ios_python/Python.xcframework/ios-arm64/`

    Option B - [python-build-standalone](https://github.com/astral-sh/python-build-standalone/releases/tag/20231002):
    ```bash
    mkdir -p ios_python
    # Download cpython-${PYTHON_VERSION}.*-aarch64-apple-ios-install_only.tar.gz
    tar xzf cpython-${PYTHON_VERSION}.*-aarch64-apple-ios-*.tar.gz -C ios_python/
    ```
    Expected layout: `ios_python/include/python${PYTHON_VERSION}/` and `ios_python/lib/libpython${PYTHON_VERSION}.a`

    **Step 2: Build**
    ```bash
    chmod +x *.sh
    ./init.sh
    ./build_ios.sh
    ```

    **Step 3: Collect**
    ```bash
    ./collect_ios.sh
    ```

    Output will be in `output/result_ios/pysf/`. The build produces static libraries (`.a`) by default. On iOS, extension modules must either be statically linked into the Python interpreter or packaged as signed Embedded Frameworks within the App Bundle.

## Additions Folder
The `Additions` folder contains additional binding code for declarations found in SFML's `.inl` files. These files follow the naming pattern `bind_{classname}_Addition.txt` and are automatically appended to the end of the generated binding code during the build process.

## Notes
- Ensure all prerequisites are properly installed before running the build script
- Make sure the configured Python version is accessible via the `py -<version>` or `python<version>` command
- LLVM must be properly configured in your system PATH

## Troubleshooting
- Verify that LLVM is correctly installed and accessible
- Check that all Python dependencies are installed for the configured Python version

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
