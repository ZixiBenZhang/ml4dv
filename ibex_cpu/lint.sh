#!/usr/bin/env sh
# Copyright lowRISC contributors.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

set -e

SCRIPT_DIR="$(cd -- "$(dirname -- "$0")" > /dev/null && pwd -P)"
cd "$SCRIPT_DIR"

echo "$0: Running flake8"
flake8

echo "$0: Running mypy"
mypy ./*.py
