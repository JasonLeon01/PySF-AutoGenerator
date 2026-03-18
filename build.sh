#!/bin/zsh

if ! [ -d "PySFEnv" ]; then
    python3.12 -m venv PySFEnv
fi
source PySFEnv/bin/activate
pip install -r requirements.txt

python3 parse.py

./ProjCMake.sh
