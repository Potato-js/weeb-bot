from typing import Optional


@staticmethod
def parse_duration(duration: str) -> Optional[int]:
    """
    Parse a duration string (e.g., '30d', '12h', '15m') into seconds.
    Returns None for invalid formats.
    """
    units = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    try:
        unit = duration[-1]  # Get the last character (unit)
        value = int(duration[:-1])  # Get the numerical value
        if unit in units:
            return value * units[unit]
    except (ValueError, IndexError):
        return None  # Invalid format
    return None
