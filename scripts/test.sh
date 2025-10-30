#!/usr/bin/env bash
set -euo pipefail

BASE_URL="http://localhost:9000"
INVOCATION_URL="$BASE_URL/2015-03-31/functions/function/invocations"

DATA="${1:-"{}"}"

curl -s "$INVOCATION_URL" -d "$DATA" | jq '.body |= fromjson'
