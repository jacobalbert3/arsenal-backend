from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request
import time
from collections import defaultdict
import asyncio

class RateLimitMiddleware:
    def __init__(self, app: ASGIApp, requests_per_minute: int = 50000):
        self.app = app
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self._cleanup_task = None

    # async def __call__(self, scope: Scope, receive: Receive, send: Send):
    #     if scope["type"] != "http":
    #         return await self.app(scope, receive, send)

    #     request = Request(scope)
    #     client_ip = request.client.host if request.client else "unknown"

    #     # Clean old requests
    #     now = time.time()
    #     self.requests[client_ip] = [req_time for req_time in self.requests[client_ip] 
    #                               if now - req_time < 60]

    #     # Check rate limit
    #     if len(self.requests[client_ip]) >= self.requests_per_minute:
    #         response = Response(
    #             status_code=429,
    #             content="Too many requests",
    #             media_type="text/plain"
    #         )
    #         await response(scope, receive, send)
    #         return

    #     # Add current request
    #     self.requests[client_ip].append(now)
    #     await self.app(scope, receive, send)
