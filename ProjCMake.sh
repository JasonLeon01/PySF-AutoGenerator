#!/bin/zsh

if [ -d build ]; then
    rm -rf build
fi
mkdir build
cd build

cmake -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DCMAKE_BUILD_TYPE=Release .. --trace-expand
if [ $? -ne 0 ]; then
    echo "CMake failed to create project"
    exit 1
fi

cmake --build . -- -j$(sysctl -n hw.ncpu)
if [ $? -ne 0 ]; then
    echo "Failed to build"
    exit 1
fi

cd ..

python3 pyFilesGen.py
if [ $? -ne 0 ]; then
    echo "python3 pyFilesGen.py Failed to generate python files"
    exit 1
fi

cp -r required_libs/*.so result/pysf/
cd build/bin

cp pysf.so ../../result/pysf/
if [ $? -ne 0 ]; then
    echo "Failed to copy pysf.so, exiting..."
    exit 1
fi

python3 -m pybind11_stubgen --output-dir=. pysf
if [ $? -ne 0 ]; then
    echo "pybind11_stubgen failed, exiting..."
    exit 1
fi

cp -r pysf/sf/* ../../result/pysf/
rm -rf pysf

echo "Script completed successfully!"
