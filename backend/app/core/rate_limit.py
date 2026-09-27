"""API rate limiting (slowapi / token-bucket per client IP)."""
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.app.config import get_settings

settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.api_rate_limit_per_minute}/minute"])
