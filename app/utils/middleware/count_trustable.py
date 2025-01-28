"""
统计 Trustable 请求
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.metric import TRUSTABLE_RESPONSE_COUNT, UNRELIABLE_RESPONSE_COUNT


class CountTrustableMiddleware(BaseHTTPMiddleware):
    """
    统计 Trustable 请求
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        route = request.scope.get("route")
        if route:
            if response.headers.get("Trustable") == "True":
                TRUSTABLE_RESPONSE_COUNT.labels(route=route.name).inc()
            else:
                UNRELIABLE_RESPONSE_COUNT.labels(route=route.name).inc()
        return response