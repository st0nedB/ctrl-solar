from zoneinfo import ZoneInfo
from typing import Optional

_TZ: Optional[ZoneInfo] = None


def set_timezone(tz_name: str) -> None:
	"""Set the global timezone. Raises ZoneInfo errors for invalid names."""
	global _TZ
	_TZ = ZoneInfo(tz_name)


def get_timezone() -> ZoneInfo:
	"""Return the configured global timezone or raise if unset."""
	if _TZ is None:
		raise RuntimeError("Timezone not configured; call set_timezone(tz_name) in app.py")
	return _TZ
