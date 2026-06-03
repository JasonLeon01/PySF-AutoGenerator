#!/bin/zsh

set -e

if ! [ -d output/build ]; then
    echo "output/build not found. Please run ./build.sh first." >&2
    exit 1
fi

rm -rf output/result
mkdir -p output/result/pysf

cp output/build/bin/*.so output/result/pysf/
cp output/build/SFML/lib/*.dylib output/result/pysf/

if ! [ -f "PySFEnv/bin/activate" ]; then
    echo "PySFEnv not found. Please run ./init.sh first." >&2
    exit 1
fi
source PySFEnv/bin/activate

python3 pyFilesGen.py
