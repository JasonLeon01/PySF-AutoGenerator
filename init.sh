#!/bin/zsh

set -e

if ! [ -f "versions.conf" ]; then
    echo "versions.conf not found." >&2
    exit 1
fi

set -a
source ./versions.conf
set +a

: ${SFML_VERSION:?"SFML_VERSION not set in versions.conf."}
: ${PYTHON_VERSION:?"PYTHON_VERSION not set in versions.conf."}

if ! [ -d "SFML" ]; then
    SFML_ARCHIVE="SFML-${SFML_VERSION}.tar.gz"
    curl -L -o "${SFML_ARCHIVE}" "https://github.com/SFML/SFML/archive/refs/tags/${SFML_VERSION}.tar.gz"
    tar xzf "${SFML_ARCHIVE}"
    mv "SFML-${SFML_VERSION}" SFML
    rm "${SFML_ARCHIVE}"
fi

if ! [ -d "PySFEnv" ]; then
    "python${PYTHON_VERSION}" -m venv PySFEnv
fi
source PySFEnv/bin/activate
pip install -r requirements.txt
