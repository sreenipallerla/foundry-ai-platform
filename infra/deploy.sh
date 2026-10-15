#!/usr/bin/env bash
# Usage: infra/deploy.sh dev|qa|prod [location]
set -euo pipefail
ENV="${1:?env: dev|qa|prod}"
LOC="${2:-swedencentral}"
RG="rg-fai-${ENV}"
az group create -n "$RG" -l "$LOC" --tags app=foundry-ai-platform env="$ENV" >/dev/null
az deployment group create -g "$RG" -f infra/main.bicep -p env="$ENV" --query properties.outputs
