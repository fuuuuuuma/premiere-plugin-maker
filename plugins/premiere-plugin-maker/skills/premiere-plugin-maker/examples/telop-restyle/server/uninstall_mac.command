#!/bin/bash
set -eu
LC_ALL=C
DIR="$(cd "$(dirname "${0}")" && pwd)"
exec /usr/bin/env python3 "${DIR}/install.py" --uninstall
