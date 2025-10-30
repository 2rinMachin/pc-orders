#!/usr/bin/env bash
set -euo pipefail

if [ $# -eq 0 ]; then
    functions=$(find functions -maxdepth 1 -mindepth 1 -type d -exec basename {} \; | paste -sd ',' - | sed 's/,/, /')

    echo "No function name given."
    echo "Available functions: $functions"
    exit 1
fi

IMAGE="pc-users-$1"

docker build -t "$IMAGE" -f "functions/$1/Dockerfile" .
docker run -p 9000:8080 -v "$HOME/.aws/credentials:/root/.aws/credentials" "$IMAGE"
