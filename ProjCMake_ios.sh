#!/bin/zsh

set -e

IOS_DEPLOY_TARGET="15.0"
IOS_ARCH="arm64"
IOS_PYTHON_DIR="$(pwd)/ios_python"
IOS_PYTHON_VERSION="3.12"

IOS_PYTHON_INCLUDE=""
IOS_PYTHON_LIB=""
PYTHON3_EXECUTABLE=""

if [ -x "$(pwd)/PySFEnv/bin/python" ]; then
    PYTHON3_EXECUTABLE="$(pwd)/PySFEnv/bin/python"
elif command -v python3.12 >/dev/null 2>&1; then
    PYTHON3_EXECUTABLE="$(command -v python3.12)"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON3_EXECUTABLE="$(command -v python3)"
fi

if [ -d "${IOS_PYTHON_DIR}/include/python${IOS_PYTHON_VERSION}" ]; then
    IOS_PYTHON_INCLUDE="${IOS_PYTHON_DIR}/include/python${IOS_PYTHON_VERSION}"
    IOS_PYTHON_LIB="${IOS_PYTHON_DIR}/lib/libpython${IOS_PYTHON_VERSION}.a"
elif [ -d "${IOS_PYTHON_DIR}/Python.xcframework/ios-arm64" ]; then
    IOS_PYTHON_INCLUDE="${IOS_PYTHON_DIR}/Python.xcframework/ios-arm64/Headers"
    if [ -f "${IOS_PYTHON_DIR}/Python.xcframework/ios-arm64/Python" ]; then
        IOS_PYTHON_LIB="${IOS_PYTHON_DIR}/Python.xcframework/ios-arm64/Python"
    elif [ -f "${IOS_PYTHON_DIR}/Python.xcframework/ios-arm64/libPython${IOS_PYTHON_VERSION}.a" ]; then
        IOS_PYTHON_LIB="${IOS_PYTHON_DIR}/Python.xcframework/ios-arm64/libPython${IOS_PYTHON_VERSION}.a"
    fi
elif [ -d "${IOS_PYTHON_DIR}/Python.xcframework/ios-arm64/Python.framework" ]; then
    IOS_PYTHON_INCLUDE="${IOS_PYTHON_DIR}/Python.xcframework/ios-arm64/Python.framework/Headers"
    IOS_PYTHON_LIB="${IOS_PYTHON_DIR}/Python.xcframework/ios-arm64/Python.framework/Python"
fi

if [ -z "${IOS_PYTHON_INCLUDE}" ] || [ -z "${IOS_PYTHON_LIB}" ]; then
    echo "Could not locate iOS Python ${IOS_PYTHON_VERSION} development files under: ${IOS_PYTHON_DIR}" >&2
    echo "Expected one of:" >&2
    echo "  - ios_python/include/python${IOS_PYTHON_VERSION} + ios_python/lib/libpython${IOS_PYTHON_VERSION}.a" >&2
    echo "  - ios_python/Python.xcframework/ios-arm64/Headers + ios_python/Python.xcframework/ios-arm64/Python" >&2
    echo "  - ios_python/Python.xcframework/ios-arm64/Headers + ios_python/Python.xcframework/ios-arm64/libPython${IOS_PYTHON_VERSION}.a" >&2
    echo "  - ios_python/Python.xcframework/ios-arm64/Python.framework/Headers + ios_python/Python.xcframework/ios-arm64/Python.framework/Python" >&2
    exit 1
fi

if [ -z "${PYTHON3_EXECUTABLE}" ]; then
    echo "Could not locate a Python executable for configuring pybind11." >&2
    echo "Expected one of:" >&2
    echo "  - ./PySFEnv/bin/python (virtualenv created by build scripts)" >&2
    echo "  - python3.12 on PATH" >&2
    echo "  - python3 on PATH" >&2
    exit 1
fi

if [ -d build_ios ]; then
    rm -rf build_ios
fi
mkdir build_ios
if [ -d result_ios ]; then
    rm -rf result_ios
fi
mkdir -p result_ios/pysf
cd build_ios

cmake -G Xcode \
    -DCMAKE_SYSTEM_NAME=iOS \
    -DCMAKE_OSX_DEPLOYMENT_TARGET=${IOS_DEPLOY_TARGET} \
    -DCMAKE_OSX_ARCHITECTURES=${IOS_ARCH} \
    -DPython3_EXECUTABLE="${PYTHON3_EXECUTABLE}" \
    -DPYTHON_EXECUTABLE="${PYTHON3_EXECUTABLE}" \
    -DPython_EXECUTABLE="${PYTHON3_EXECUTABLE}" \
    -DPython3_INCLUDE_DIR="${IOS_PYTHON_INCLUDE}" \
    -DPython3_LIBRARY="${IOS_PYTHON_LIB}" \
    -DPYTHON_INCLUDE_DIR="${IOS_PYTHON_INCLUDE}" \
    -DPYTHON_LIBRARY="${IOS_PYTHON_LIB}" \
    ..

cmake --build . --config Release -- -quiet

setopt null_glob
if [ -d "SFML/lib/Release" ]; then
    for lib_file in SFML/lib/Release/*.a; do
        cp "$lib_file" ../result_ios/pysf/
    done
fi
unsetopt null_glob

find . -name "*.a" -path "*/Release-iphoneos/*" -exec cp {} ../result_ios/pysf/ \; 2>/dev/null
find . -name "*.so" -path "*/Release-iphoneos/*" -exec cp {} ../result_ios/pysf/ \; 2>/dev/null
find . -name "*.dylib" -path "*/Release-iphoneos/*" -exec cp {} ../result_ios/pysf/ \; 2>/dev/null

cd ..
