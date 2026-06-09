#!/usr/bin/env bash
# Run the same lint checks as .github/workflows/linting.yml (pre-commit hooks).
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/pre-commit run --all-files --show-diff-on-failure
