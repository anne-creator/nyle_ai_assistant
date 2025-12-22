from contextvars import ContextVar
from typing import Optional

# Context variable to store request-scoped data
_request_context: ContextVar[Optional["RequestContext"]] = ContextVar(
    "request_context", default=None
)


class RequestContext:
    """Request-scoped context for storing JWT and session info."""
    
    def __init__(self, jwt_token: str, session_id: str):
        self.jwt_token = jwt_token
        self.session_id = session_id
    
    def __enter__(self):
        self._token = _request_context.set(self)
        return self
    
    def __exit__(self, *args):
        _request_context.reset(self._token)


def get_current_context() -> Optional[RequestContext]:
    """Get the current request context."""
    return _request_context.get()


def get_jwt_token() -> str:
    """Get JWT token from current context."""
    ctx = get_current_context()
    if ctx is None:
        raise RuntimeError("No request context available")
    return ctx.jwt_token

