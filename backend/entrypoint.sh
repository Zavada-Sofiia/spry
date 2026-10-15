#!/bin/sh
if [ -z "$AWS_LAMBDA_RUNTIME_API" ]; then
    exec "$@"
else
    exec python -m awslambdaric "$@"
fi
