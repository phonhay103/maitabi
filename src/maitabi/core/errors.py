"""Uniform error payloads returned inside successful HTTP responses.

Upstream failures never raise: services embed these shapes in the JSON body so
MCP clients, CLI scripts, and raw-HTTP consumers all read the same contract:
`{"error": <human message>, "detail": <technical cause>, "retry_hint": <optional>}`.
"""

RATE_LIMIT_ERROR = "Rate limited by www.maitabi.jp (60 requests/min per IP)"
RATE_LIMIT_RETRY_HINT = "wait ~60s and retry manually"
THROTTLED_BODY_MESSAGE = "Too Many Attempts."


def upstream_http_error(status_code: int, detail: str) -> dict[str, str]:
    """Non-2xx upstream response."""
    return {
        "error": f"Upstream service returned error: {status_code}",
        "detail": detail,
    }


def connection_error(detail: str) -> dict[str, str]:
    """Network-level failure reaching the upstream host."""
    return {
        "error": "Failed to connect to Maitabi server",
        "detail": detail,
    }


def rate_limit_error() -> dict[str, str]:
    """www.maitabi.jp throttling (HTTP 200 + 'Too Many Attempts.' body)."""
    return {
        "error": RATE_LIMIT_ERROR,
        "detail": THROTTLED_BODY_MESSAGE,
        "retry_hint": RATE_LIMIT_RETRY_HINT,
    }


def is_rate_limited_body(data: object) -> bool:
    """Detect www.maitabi.jp's HTTP-200 throttle body (no Retry-After header)."""
    if not isinstance(data, dict):
        return False
    errors = data.get("errors")
    if not isinstance(errors, dict):
        return False
    return bool(errors.get("message") == THROTTLED_BODY_MESSAGE)


def is_error_payload(data: object) -> bool:
    """True when a service result carries an error instead of data."""
    return isinstance(data, dict) and "error" in data
