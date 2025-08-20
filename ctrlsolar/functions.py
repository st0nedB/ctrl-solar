import logging

__all__ = ["asymmetric_exponential_smoothing", "running_mean", "check_properties", "compute_asymmetric_alphas"]

logger = logging.getLogger(__name__)


def asymmetric_exponential_smoothing(
    values: list, alpha_up: float, alpha_down: float
) -> float:
    """
    Asymmetric EMA:
    - If the new value is higher than the current estimate, use alpha_up (slower reaction).
    - If the new value is lower, use alpha_down (faster reaction).
    """
    if not values:
        raise ValueError("Values list must not be empty")

    ema = values[0]
    for v in values[1:]:
        alpha = alpha_down if v < ema else alpha_up
        ema = alpha * v + (1 - alpha) * ema

    return ema


def compute_asymmetric_alphas(
    sample_interval: float, half_life_up: float = 20.0, half_life_down: float = 6.0
) -> tuple[float, float]:
    """
    Compute asymmetric EMA alphas for given sampling rate and half-lives.

    Parameters
    ----------
    sample_interval : float
        Time between samples in seconds.
    half_life_up : float
        Half-life (seconds) for upward moves (slower).
    half_life_down : float
        Half-life (seconds) for downward moves (faster).

    Returns
    -------
    (alpha_up, alpha_down) : tuple of floats
        Smoothing parameters for upward vs downward moves.

    Example usage
    -------------
    alpha_up, alpha_down = compute_asymmetric_alphas(sample_interval=1.0)
    """

    def alpha_from_half_life(half_life: float) -> float:
        return 1 - (0.5 ** (sample_interval / half_life))

    alpha_up = alpha_from_half_life(half_life_up)
    alpha_down = alpha_from_half_life(half_life_down)
    return alpha_up, alpha_down


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
