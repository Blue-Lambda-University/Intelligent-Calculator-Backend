#!/bin/sh
set -eu
NAMESPACE="${NAMESPACE:-calculator-staging}"
echo "Restoring previous API Deployment revision in $NAMESPACE"
kubectl -n "$NAMESPACE" rollout undo deployment/calculator-api
kubectl -n "$NAMESPACE" rollout status deployment/calculator-api --timeout=180s
