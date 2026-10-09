import time
from collections import defaultdict
from typing import Dict, List, Optional
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class InMemoryRateLimiter:
    """
    Sliding window in-memory rate limiter.
    Tracks timestamps of requests per client key (e.g. IP address or user ID).
    """
    def __init__(self, requests_limit: int = 100, window_seconds: int = 60):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.client_records: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, client_key: str, limit: Optional[int] = None, window: Optional[int] = None) -> tuple[bool, int, int]:
        max_requests = limit or self.requests_limit
        window_sec = window or self.window_seconds
        now = time.time()
        window_start = now - window_sec

        # Clean old timestamps outside the window
        timestamps = self.client_records[client_key]
        self.client_records[client_key] = [t for t in timestamps if t > window_start]
        current_count = len(self.client_records[client_key])

        if current_count >= max_requests:
            oldest = self.client_records[client_key][0]
            retry_after = int(oldest + window_sec - now) + 1
            return False, 0, max(1, retry_after)

        self.client_records[client_key].append(now)
        remaining = max_requests - (current_count + 1)
        return True, remaining, 0


# Global Rate Limiter Instance (100 req/min default for general API)
global_rate_limiter = InMemoryRateLimiter(requests_limit=100, window_seconds=60)

# Stricter Rate Limiter for Auth endpoints (10 login/register attempts per minute per IP)
auth_rate_limiter = InMemoryRateLimiter(requests_limit=10, window_seconds=60)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware applying global and endpoint-specific rate limiting.
    Returns HTTP 429 Too Many Requests when limits are exceeded.
    """
    async def dispatch(self, request: Request, call_next):
        # Extract client IP
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Ignore documentation and health endpoints
        if path in ("/docs", "/redoc", "/health", "/", "/api/v1/openapi.json"):
            return await call_next(request)

        # Apply strict rate limiting on /auth/login and /auth/register
        if "/auth/login" in path or "/auth/register" in path:
            allowed, remaining, retry_after = auth_rate_limiter.is_allowed(
                f"auth:{client_ip}", limit=10, window=60
            )
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": f"Too many authentication attempts. Please try again in {retry_after} seconds.",
                        "retry_after_seconds": retry_after,
                    },
                    headers={"Retry-After": str(retry_after)},
                )

        # Apply global rate limit
        allowed, remaining, retry_after = global_rate_limiter.is_allowed(
            f"global:{client_ip}", limit=120, window=60
        )
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Maximum 120 requests per minute. Retry in {retry_after} seconds.",
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = "120"
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
