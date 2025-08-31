import logging
from typing import Any, Union, Literal

__all__ = ["running_mean", "check_properties"]

logger = logging.getLogger(__name__)


def exponential_smoothing(values: list, alpha=0.2) -> float:
    if len(values) < 2:
        return values[-1]

    ema = values[0]
    for v in values[1:]:
        ema = alpha * v + (1 - alpha) * ema

    return ema


def running_mean(values: list) -> float:
    return sum(values) / len(values)


def check_properties(instance) -> dict:
    tmp = {}
    for prop_name in dir(instance):
        if not prop_name.startswith("_") and hasattr(instance, prop_name):
            prop_value = getattr(instance, prop_name)
            if not callable(prop_value):
                if prop_value is None:
                    tmp[prop_name] = False
                else:
                    tmp[prop_name] = True
    return tmp


def filter_dict_with_keys(
    x: dict, dkeys: list[str,], dtype: Literal["str", "float", "int"], scale: float = 1.0
) -> Union[str, float, int]:
    val: Any = x
    for key in dkeys:
        val = val[key]

    val = eval(dtype)(val)

    if dtype != "str":
        val *= scale

    return val
