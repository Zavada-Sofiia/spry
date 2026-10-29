#!/bin/sh
if [ -z "$AWS_LAMBDA_RUNTIME_API" ]; then
    alembic upgrade head || true
    exec "$@"
else
    exec python -m awslambdaric "$@"
fi
