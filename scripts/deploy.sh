#!/usr/bin/env bash
set -euo pipefail

if [ $# -eq 0 ]; then
    functions=$(find functions -maxdepth 1 -mindepth 1 -type d -exec basename {} \; | paste -sd ',' - | sed 's/,/, /')

    echo "No function name given."
    echo "Available functions: $functions"
    exit 1
fi

image="pc-users-$1"
repo="$AWS_USER_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

docker build -t "$image" -f "functions/$1/Dockerfile" .
docker tag "$image" "$repo/$image"
docker push "$repo/$image"
