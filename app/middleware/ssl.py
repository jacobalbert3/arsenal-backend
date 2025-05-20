from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
from starlette.responses import Response

class SSLMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        forwarded_proto = request.headers.get("x-forwarded-proto", "")
        origin = request.headers.get("origin", "")
        host = request.headers.get("host", "")

        # Allow localhost and 127.0.0.1
        if request.url.hostname in ["localhost", "127.0.0.1"]:
            return await call_next(request)

        # Allow vscode-webview
        if origin.startswith("vscode-webview://"):
            return await call_next(request)

        # Trust x-forwarded-proto from proxy
        if forwarded_proto == "https":
            return await call_next(request)

        # Fall back to FastAPI's view of the scheme (usually http behind a proxy)
        if request.url.scheme == "https":
            return await call_next(request)

        raise HTTPException(status_code=400, detail="SSL required")

