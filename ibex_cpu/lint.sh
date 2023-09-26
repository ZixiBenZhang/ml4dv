#!/usr/bin/env sh
set -e

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" > /dev/null && pwd -P)"
cd "$SCRIPT_DIR"

echo "$0: Running flake8"
flake8

echo "$0: Running mypy"
mypy ./*.py
