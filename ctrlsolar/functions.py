
__all__ = ["exponential_smoothing"]

def exponential_smoothing(values: list, alpha=0.5):
    if len(values) < 2:
        return values[-1]

    ema = values[0]
    for v in values[1:]:
        ema = alpha * v + (1 - alpha) * ema

    return ema