#!/usr/bin/env bash
set -euo pipefail

HEALTH_URL="${MADAR_HEALTH_URL:-https://madar-test.r8787m.cc/api/method/madar.api.health.ping}"
TIMEOUT_SECONDS="${MADAR_HEALTH_TIMEOUT_SECONDS:-10}"

response="$(curl -fsS --max-time "$TIMEOUT_SECONDS" "$HEALTH_URL")"

python3 - "$response" <<'PY'
import json
import sys

raw = sys.argv[1]
try:
    payload = json.loads(raw)
except json.JSONDecodeError:
    print("CRITICAL health_check invalid_json")
    raise SystemExit(2)

message = payload.get("message", payload)
if message.get("ok") is True and message.get("app") == "madar":
    print("OK health_check ok=true app=madar")
    raise SystemExit(0)

print("CRITICAL health_check unexpected_response")
raise SystemExit(2)
PY
