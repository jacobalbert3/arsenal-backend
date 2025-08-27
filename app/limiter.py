from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Create a global limiter instance
limiter = Limiter(key_func=get_remote_address)
# This will be set when the app is created
app = None

def get_limiter():
    """Get the limiter instance that's attached to the app"""
    if app is None:
        raise RuntimeError("App not initialized yet")
    return app.state.limiter

