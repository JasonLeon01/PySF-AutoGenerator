#!/bin/zsh

if [ -d build ]; then
    rm -rf build
fi
mkdir build
if [ -d result ]; then
    rm -rf result
fi
mkdir result
mkdir result/pysf
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

cp bin/pysf.so ../result/pysf/
if [ $? -ne 0 ]; then
    echo "Failed to copy pysf.so, exiting..."
    exit 1
fi

cp sfml_libs/*.dylib ../result/pysf/
if [ $? -ne 0 ]; then
    echo "Failed to copy dependencies, exiting..."
    exit 1
fi

cd ..

python3.10 pyFilesGen.py
if [ $? -ne 0 ]; then
    echo "python3.10 pyFilesGen.py Failed to generate python files"
    exit 1
fi

cd result/pysf
python3.10 -m pybind11_stubgen --output-dir=. pysf.sf

mv pysf/sf/* . 2>/dev/null
rm -rf pysf

echo "Script completed successfully!"
