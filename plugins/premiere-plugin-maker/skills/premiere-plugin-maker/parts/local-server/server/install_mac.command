#!/bin/bash
# ターミナルで「bash 」（後ろに空白）と打ち、このファイルをドラッグして Enter で実行する
set -eu
LC_ALL=C
DIR="$(cd "$(dirname "${0}")" && pwd)"
exec /usr/bin/env python3 "${DIR}/install.py" "$@"
