import base64
from datetime import date
import json
import logging
import time
from typing import Any

import jwt
from jwt import PyJWKClient

from app.ai.agenda import (
    PROMPT_VERSION,
    AgendaParseError,
    cost_usd,
    parse_agenda,
)
from app.config import settings

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_jwks_client = None


def get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        jwks_url = f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url)
    return _jwks_client


def verify_token(token: str) -> str:
    """Verify Cognito JWT and return the user identifier."""
    jwks_client = get_jwks_client()
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    expected_issuer = f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}"

    payload = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        issuer=expected_issuer,
        options={"verify_aud": False},
    )
    user_id = payload.get("sub") or payload.get("cognito:username") or payload.get("email") or "unknown"
    return str(user_id)


def handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """Lambda Function URL handler for parsing raw text into structured agendas."""
    headers = event.get("headers") or {}
    auth_header = None
    for k, v in headers.items():
        if k.lower() == "authorization":
            auth_header = v
            break

    if not auth_header or not auth_header.startswith("Bearer "):
        return {
            "statusCode": 401,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Missing or invalid authorization header"}),
        }

    token = auth_header[7:].strip()
    try:
        user_id = verify_token(token)
    except Exception as e:
        return {
            "statusCode": 401,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": f"Unauthorized: {str(e)}"}),
        }

    raw_body = event.get("body", "{}")
    if event.get("isBase64Encoded"):
        raw_body = base64.b64decode(raw_body).decode("utf-8")

    if isinstance(raw_body, str):
        try:
            body = json.loads(raw_body)
        except Exception:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Invalid JSON body"}),
            }
    elif isinstance(raw_body, dict):
        body = raw_body
    else:
        body = {}

    text = body.get("text", "")
    if not isinstance(text, str):
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Field 'text' must be a string"}),
        }

    if len(text) > 10000:
        return {
            "statusCode": 413,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Payload too large: text exceeds 10,000 characters"}),
        }

    today_val = body.get("today")
    try:
        today = date.fromisoformat(today_val) if today_val else date.today()
    except ValueError:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Field 'today' must be a valid ISO date (YYYY-MM-DD)"}),
        }

    tz = body.get("tz", "UTC")

    start_time = time.perf_counter()
    try:
        agenda, usage = parse_agenda(text, today, tz)
    except AgendaParseError as e:
        return {
            "statusCode": 422,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)}),
        }
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "ThrottlingException" in err_str or "Too many" in err_str or "rate_limit" in err_str.lower():
            return {
                "statusCode": 429,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Service busy. Please wait a moment and try again."}),
            }
        logger.error(f"Unexpected error in agenda parser: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error"}),
        }

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    cost = cost_usd(settings.PARSER_MODEL, usage)

    log_entry = {
        "event": "agenda_parsed",
        "user": user_id,
        "model": settings.PARSER_MODEL,
        "prompt_version": PROMPT_VERSION,
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "latency_ms": latency_ms,
        "cost_usd": cost,
    }
    logger.info(json.dumps(log_entry))

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "agenda": agenda.model_dump(mode="json"),
            "model": settings.PARSER_MODEL,
            "prompt_version": PROMPT_VERSION,
        }),
    }
