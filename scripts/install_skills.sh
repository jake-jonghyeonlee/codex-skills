#!/usr/bin/env bash
# Install the Python dependencies for .agents/skills into an isolated venv and verify them.
#
# Works from Git Bash on Windows (CPython 3.12 x64) and from bash on macOS/Linux.
#
#   PIP_INDEX_URL=https://<corporate-pypi>/simple scripts/install_skills.sh
#   scripts/install_skills.sh --index-url https://<corporate-pypi>/simple
#   scripts/install_skills.sh --python "py -3.12"        # choose the interpreter
#   scripts/install_skills.sh --venv .venv-skills        # default location (git-ignored)
#   scripts/install_skills.sh --with-optional            # also install requirements-optional.txt (optional/skills)
#   scripts/install_skills.sh --no-verify
#
# Nothing is downloaded except wheels from the given index. No admin rights needed.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REQUIREMENTS="$REPO_ROOT/requirements-skills.txt"
OPTIONAL_REQ="$REPO_ROOT/requirements-optional.txt"
WITH_OPTIONAL=0
INDEX_URL="${PIP_INDEX_URL:-${UV_DEFAULT_INDEX:-}}"
PYTHON_CMD=""
VENV="$REPO_ROOT/.venv-skills"
VERIFY=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --index-url) INDEX_URL="${2:-}"; shift 2 ;;
    --python)    PYTHON_CMD="${2:-}"; shift 2 ;;
    --venv)      VENV="${2:-}"; shift 2 ;;
    --with-optional) WITH_OPTIONAL=1; shift ;;
    --no-verify) VERIFY=0; shift ;;
    -h|--help)   sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "error: unknown option $1" >&2; exit 1 ;;
  esac
done

[[ -f "$REQUIREMENTS" ]] || { echo "error: $REQUIREMENTS not found" >&2; exit 1; }
if [[ -z "$INDEX_URL" ]]; then
  echo "error: set PIP_INDEX_URL (or pass --index-url) to the corporate PyPI simple index" >&2; exit 1
fi
case "$INDEX_URL" in
  https://*) ;;
  *) echo "error: the index URL must use https: $INDEX_URL" >&2; exit 1 ;;
esac

# Pick a CPython 3.12. On Windows prefer the py launcher; elsewhere python3.12, then python3.
pick_python() {
  local c
  for c in "py -3.12" python3.12 python3 python; do
    # shellcheck disable=SC2086
    if $c -c 'import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)' >/dev/null 2>&1; then
      echo "$c"; return 0
    fi
  done
  return 1
}
if [[ -z "$PYTHON_CMD" ]]; then
  PYTHON_CMD="$(pick_python)" || { echo "error: no CPython 3.12 found (install it or pass --python)" >&2; exit 1; }
fi

if [[ -x "$VENV/Scripts/python.exe" ]]; then
  VENV_PY="$VENV/Scripts/python.exe"          # Windows layout
elif [[ -x "$VENV/bin/python" ]]; then
  VENV_PY="$VENV/bin/python"                  # POSIX layout
else
  echo "creating $VENV with '$PYTHON_CMD'"
  # shellcheck disable=SC2086
  $PYTHON_CMD -m venv "$VENV"
  if [[ -x "$VENV/Scripts/python.exe" ]]; then VENV_PY="$VENV/Scripts/python.exe"; else VENV_PY="$VENV/bin/python"; fi
fi
"$VENV_PY" -I -c 'import sys; assert sys.version_info[:2] == (3, 12), sys.version'

export PIP_DISABLE_PIP_VERSION_CHECK=1
echo "installing skill dependencies from $INDEX_URL"
"$VENV_PY" -I -m pip install --index-url "$INDEX_URL" --only-binary=:all: --require-virtualenv -r "$REQUIREMENTS"
if [[ "$WITH_OPTIONAL" -eq 1 ]]; then
  echo "installing optional skill dependencies (optional/skills)"
  "$VENV_PY" -I -m pip install --index-url "$INDEX_URL" --only-binary=:all: --require-virtualenv -r "$OPTIONAL_REQ"
fi
"$VENV_PY" -I -m pip check

if [[ "$VERIFY" -eq 1 ]]; then
  "$VENV_PY" -I "$REPO_ROOT/scripts/verify_skills.py"
fi
