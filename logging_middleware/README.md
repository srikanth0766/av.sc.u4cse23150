# Logging Middleware

Reusable logging client for the Affordmed evaluation service.

## Responsibilities

- Validates `stack`, `level`, and `package` before sending
- Injects the bearer token automatically
- Retries transient failures
- Returns a fallback payload instead of crashing callers

## Main API

```python
from logging_middleware import log_event
```

Implementation: [client.py](/Users/ramkey03/Desktop/test/logging_middleware/client.py)
