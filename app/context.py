from contextvars import ContextVar
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Context variable to store request-scoped data
_request_context: ContextVar[Optional["RequestContext"]] = ContextVar(
    "request_context", default=None
)

# Fallback JWT token storage (for when contextvars don't propagate)
_jwt_token_fallback: ContextVar[Optional[str]] = ContextVar(
    "jwt_token_fallback", default=None
)


class RequestContext:
    """Request-scoped context for storing JWT and session info."""
    
    def __init__(self, jwt_token: str, session_id: str):
        self.jwt_token = jwt_token
        self.session_id = session_id
        self._token = None
    
    def __enter__(self):
        self._token = _request_context.set(self)
        logger.debug(f"RequestContext entered: session_id={self.session_id}, jwt_token={self.jwt_token[:20]}...")
        return self
    
    def __exit__(self, *args):
        logger.debug(f"RequestContext exited: session_id={self.session_id}")
        if self._token is not None:
            _request_context.reset(self._token)
    
    async def __aenter__(self):
        self._token = _request_context.set(self)
        # Also set fallback JWT token
        _jwt_token_fallback.set(self.jwt_token)
        logger.debug(f"RequestContext async entered: session_id={self.session_id}, jwt_token={self.jwt_token[:20]}...")
        return self
    
    async def __aexit__(self, *args):
        logger.debug(f"RequestContext async exited: session_id={self.session_id}")
        if self._token is not None:
            _request_context.reset(self._token)
        # Clear fallback
        _jwt_token_fallback.set(None)


def get_current_context() -> Optional[RequestContext]:
    """Get the current request context."""
    return _request_context.get()


def get_jwt_token() -> str:
    """Get JWT token from current context with fallback."""
    ctx = get_current_context()
    if ctx is not None:
        logger.debug(f"Retrieved JWT token from context: {ctx.jwt_token[:20]}...")
        return ctx.jwt_token
    
    # Try fallback
    fallback_token = _jwt_token_fallback.get()
    if fallback_token:
        logger.debug(f"Retrieved JWT token from fallback: {fallback_token[:20]}...")
        return fallback_token
    
    logger.error("No request context available and no fallback token")
    raise RuntimeError("No request context available")


def set_jwt_token_for_task(jwt_token: str):
    """Set JWT token for current async task (useful for sub-tasks that lose context)."""
    _jwt_token_fallback.set(jwt_token)
    logger.debug(f"Set fallback JWT token: {jwt_token[:20]}...")


def get_jwt_from_config(config: dict) -> Optional[str]:
    """Get JWT token from LangGraph config if available."""
    if config and "configurable" in config:
        return config["configurable"].get("jwt_token")
    return None

