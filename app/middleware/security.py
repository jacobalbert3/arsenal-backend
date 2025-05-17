from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"  # Prevents MIME-type sniffing
        response.headers["X-Frame-Options"] = "DENY"  # Prevents clickjacking
        response.headers["X-XSS-Protection"] = "1; mode=block"  # Enables XSS filtering
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"  # Forces HTTPS
        response.headers["Content-Security-Policy"] = "default-src 'self'"  # Restricts resource loading
        return response
