#!/bin/zsh

set -e

if ! [ -d output/build_ios ]; then
    echo "output/build_ios not found. Please run ./build_ios.sh first." >&2
    exit 1
fi

rm -rf output/result_ios
mkdir -p output/result_ios/pysf
cd output/build_ios

setopt null_glob
if [ -d "SFML/lib/Release" ]; then
    for lib_file in SFML/lib/Release/*.a; do
        cp "$lib_file" ../../output/result_ios/pysf/
    done
fi
unsetopt null_glob

find . -name "*.a" -path "*/Release-iphoneos/*" -exec cp {} ../../output/result_ios/pysf/ \; 2>/dev/null
find . -name "*.so" -path "*/Release-iphoneos/*" -exec cp {} ../../output/result_ios/pysf/ \; 2>/dev/null
find . -name "*.dylib" -path "*/Release-iphoneos/*" -exec cp {} ../../output/result_ios/pysf/ \; 2>/dev/null

cd ../..
