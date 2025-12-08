import os
from typing import Optional
import dotenv
dotenv.load_dotenv()


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
	
	value = os.getenv(name)
	return value if value is not None else default


def get_timeout_seconds() -> int:
	val = get_env("HTTP_TIMEOUT_SECONDS", "15")
	try:
		return max(1, int(val))
	except Exception:
		return 15


def get_calendly_config() -> dict:
	"""Get Calendly OAuth configuration"""
	return {
		"client_id": get_env("CALENDLY_CLIENT_ID"),
		"client_secret": get_env("CALENDLY_CLIENT_SECRET"),
		"redirect_uri": get_env("CALENDLY_REDIRECT_URI", "http://localhost:8000/calendly/auth/callback"),
	}
