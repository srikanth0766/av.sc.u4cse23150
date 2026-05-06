import json
import os
import time
from typing import Any
from urllib import error, request


DEFAULT_BASE_URL = "http://20.207.122.201/evaluation-service"
BASE_URL = os.getenv("EVAL_BASE_URL", DEFAULT_BASE_URL)
ACCESS_TOKEN = os.getenv("EVAL_ACCESS_TOKEN", "")
LOG_URL = f"{BASE_URL}/logs"
STACKS = {"backend", "frontend"}
LEVELS = {"debug", "info", "warn", "error", "fatal"}
PACKAGE_BY_STACK = {
    "backend": {
        "cache",
        "controller",
        "cron_job",
        "db",
        "domain",
        "handler",
        "repository",
        "route",
        "service",
        "auth",
        "config",
        "middleware",
        "utils",
    },
    "frontend": {
        "api",
        "component",
        "hook",
        "page",
        "state",
        "style",
        "auth",
        "config",
        "middleware",
        "utils",
    },
}


def _build_request(url: str, method: str = "GET", body: dict[str, Any] | None = None) -> request.Request:
    data = None
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    return request.Request(url=url, data=data, headers=headers, method=method)


def _send_json(url: str, method: str = "GET", body: dict[str, Any] | None = None) -> dict[str, Any]:
    req = _build_request(url=url, method=method, body=body)
    with request.urlopen(req, timeout=15) as response:
        raw = response.read().decode("utf-8")
        if not raw:
            return {}
        return json.loads(raw)


def _validate_log_input(stack: str, level: str, package: str, message: str) -> None:
    if stack not in STACKS:
        raise ValueError("invalid stack for log event")
    if level not in LEVELS:
        raise ValueError("invalid level for log event")
    if package not in PACKAGE_BY_STACK[stack]:
        raise ValueError("invalid package for selected stack")
    if not isinstance(message, str) or not message.strip():
        raise ValueError("message must be a non-empty string")


def log_event(stack: str, level: str, package: str, message: str) -> dict[str, Any]:
    _validate_log_input(stack, level, package, message)
    payload = {
        "stack": stack,
        "level": level,
        "package": package,
        "message": message,
    }
    if not ACCESS_TOKEN.strip():
        return {
            "message": "log delivery failed",
            "failedPayload": payload,
            "error": "missing bearer token",
        }
    last_error = None
    for attempt in range(3):
        try:
            return _send_json(LOG_URL, method="POST", body=payload)
        except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            time.sleep(0.4 * (attempt + 1))
    return {
        "message": "log delivery failed",
        "failedPayload": payload,
        "error": last_error,
    }


def Log(stack: str, level: str, package: str, message: str) -> dict[str, Any]:
    return log_event(stack, level, package, message)
