#!/bin/zsh

set -e

if ! [ -f "versions.conf" ]; then
    echo "versions.conf not found." >&2
    exit 1
fi

set -a
source ./versions.conf
set +a

if ! [ -f "PySFEnv/bin/activate" ]; then
    echo "PySFEnv not found. Please run ./init.sh first." >&2
    exit 1
fi
source PySFEnv/bin/activate

python3 parse.py

./ProjCMake_ios.sh
