#!/bin/zsh

set -e

IOS_DEPLOY_TARGET="15.0"
IOS_ARCH="arm64"
IOS_PYTHON_DIR="$(pwd)/ios_python"
IOS_PYTHON_VERSION="3.12"

IOS_PYTHON_INCLUDE=""
IOS_PYTHON_LIB=""

if [ -d "${IOS_PYTHON_DIR}/include/python${IOS_PYTHON_VERSION}" ]; then
    IOS_PYTHON_INCLUDE="${IOS_PYTHON_DIR}/include/python${IOS_PYTHON_VERSION}"
    IOS_PYTHON_LIB="${IOS_PYTHON_DIR}/lib/libpython${IOS_PYTHON_VERSION}.a"
elif [ -d "${IOS_PYTHON_DIR}/Python.xcframework/ios-arm64" ]; then
    IOS_PYTHON_INCLUDE="${IOS_PYTHON_DIR}/Python.xcframework/ios-arm64/Headers"
    IOS_PYTHON_LIB="${IOS_PYTHON_DIR}/Python.xcframework/ios-arm64/Python"
elif [ -d "${IOS_PYTHON_DIR}/Python.xcframework/ios-arm64/Python.framework" ]; then
    IOS_PYTHON_INCLUDE="${IOS_PYTHON_DIR}/Python.xcframework/ios-arm64/Python.framework/Headers"
    IOS_PYTHON_LIB="${IOS_PYTHON_DIR}/Python.xcframework/ios-arm64/Python.framework/Python"
fi

if [ -z "${IOS_PYTHON_INCLUDE}" ] || [ -z "${IOS_PYTHON_LIB}" ]; then
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
    -DPython3_INCLUDE_DIR="${IOS_PYTHON_INCLUDE}" \
    -DPython3_LIBRARY="${IOS_PYTHON_LIB}" \
    -DPYTHON_INCLUDE_DIR="${IOS_PYTHON_INCLUDE}" \
    -DPYTHON_LIBRARY="${IOS_PYTHON_LIB}" \
    ..

cmake --build . --config Release -- -quiet

find . -name "*.a" -path "*/Release-iphoneos/*" -exec cp {} ../result_ios/pysf/ \; 2>/dev/null
find . -name "*.so" -path "*/Release-iphoneos/*" -exec cp {} ../result_ios/pysf/ \; 2>/dev/null
find . -name "*.dylib" -path "*/Release-iphoneos/*" -exec cp {} ../result_ios/pysf/ \; 2>/dev/null

cd ..
