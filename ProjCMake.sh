#!/bin/zsh

set -e

if ! [ -d output ]; then
    echo "output not found. Please run ./build.sh to generate bindings first." >&2
    exit 1
fi

PYSF_PYTHON_EXECUTABLE="$(pwd)/PySFEnv/bin/python"
if ! [ -x "${PYSF_PYTHON_EXECUTABLE}" ]; then
    echo "PySFEnv Python not found: ${PYSF_PYTHON_EXECUTABLE}" >&2
    exit 1
fi

mkdir -p output/include output/src
cp -R include/. output/include/
cp -R src/. output/src/

if [ -d output/SFML ]; then
    rm -rf output/SFML
fi
mkdir -p output/SFML
rsync -a --exclude .git SFML/ output/SFML/

if [ -d output/build ]; then
    rm -rf output/build
fi
mkdir output/build
cd output/build

cmake \
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
    -DCMAKE_BUILD_TYPE=Release \
    -DPython3_EXECUTABLE="${PYSF_PYTHON_EXECUTABLE}" \
    ..
cmake --build . -- -j$(sysctl -n hw.ncpu)

cd ../..
