#!/usr/bin/env bash
set -e
cd "$(dirname "$(readlink -f "$0")")"
exec "${PYTHON:-python3}" main.py "$@"
