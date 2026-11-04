#!/usr/bin/env bash
set -euo pipefail
roboln_root="$(cd "$(dirname "$0")/.." && pwd)"
roboln_python="$roboln_root/.venv/bin/python"
if [[ ! -x "$roboln_python" ]]; then
  echo 'Create .venv and install backend/requirements.lock first.' >&2
  exit 1
fi
cd "$roboln_root/backend"
"$roboln_python" -m alembic upgrade head
"$roboln_python" -m uvicorn app.api:app --host 127.0.0.1 --port 8000 &
roboln_api_pid=$!
trap 'kill "$roboln_api_pid" 2>/dev/null || true' EXIT
cd "$roboln_root/frontend"
npm run dev
