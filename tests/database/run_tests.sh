#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
python -m pytest --confcutdir=tests/database tests/database -q
