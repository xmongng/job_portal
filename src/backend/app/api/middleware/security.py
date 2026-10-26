"""Basic single-process limits; no tokens/request bodies in logs."""

import logging
import time
from collections import OrderedDict, deque
from threading import Lock
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import get_settings

logger = logging.getLogger("jobportal.requests")


class RequestSecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.buckets = OrderedDict()
        self.lock = Lock()

    # Không tin X-Forwarded-For; reverse proxy phải cấu hình trusted proxy ở ASGI server.
    async def dispatch(self, request, call_next):
        settings = get_settings()
        request_id = uuid4().hex
        path = request.url.path
        group = (
            "auth"
            if path in ["/api/auth/login", "/api/auth/register", "/api/auth/refresh"]
            else "ai"
            if path.startswith("/api/ai/")
            else None
        )
        if group:
            now = time.monotonic()
            key = (request.client.host if request.client else "unknown", group)
            limit = (
                settings.auth_rate_limit_per_minute
                if group == "auth"
                else settings.ai_rate_limit_per_minute
            )
            with self.lock:
                bucket = self.buckets.setdefault(key, deque())
                while bucket and bucket[0] <= now - 60:
                    bucket.popleft()
                if len(bucket) >= limit:
                    return JSONResponse(
                        {"detail": "Too many requests"},
                        status_code=429,
                        headers={"Retry-After": "60", "X-Request-ID": request_id},
                    )
                bucket.append(now)
                self.buckets.move_to_end(key)
                while len(self.buckets) > 10000:
                    self.buckets.popitem(last=False)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        if path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        # Log route template thay vì query/ID chứa dữ liệu cá nhân.
        route = getattr(request.scope.get("route"), "path", "unmatched")
        logger.info(
            "request_id=%s method=%s route=%s status=%s",
            request_id,
            request.method,
            route,
            response.status_code,
        )
        return response
