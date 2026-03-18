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
cmake --build . -- -j$(sysctl -n hw.ncpu)

cp bin/pysf.so ../result/pysf/
cp sfml_libs/*.dylib ../result/pysf/

cd ..
python3 pyFilesGen.py
