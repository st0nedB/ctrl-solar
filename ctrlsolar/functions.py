import logging

__all__ = ["exponential_smoothing", "running_mean", "check_properties"]

logger = logging.getLogger(__name__)

def exponential_smoothing(values: list, alpha=0.5) -> float:
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
        if not prop_name.startswith('_') and hasattr(instance, prop_name):
            prop_value = getattr(instance, prop_name)
            if not callable(prop_value):
                if prop_value is None:
                    tmp[prop_name] = False
                else:
                    tmp[prop_name] = True
    return tmp