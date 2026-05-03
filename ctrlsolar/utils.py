from typing import Any
import logging

logger = logging.getLogger(__name__)

def any_is_none(*args: Any) -> bool:
    is_none = any([x is None for x in args])
    if is_none: 
        logger.warning(f"Found at least one required value to be `None`.")

    return is_none