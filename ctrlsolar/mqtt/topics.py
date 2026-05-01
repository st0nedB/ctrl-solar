"""MQTT topic and Home Assistant autodiscovery helpers.

This module defines standard topic formats used by the project and
provides functions that generate Home Assistant discovery payloads
for the `set_power` and `hourly_forecast` sensors.

"""
from typing import Any, cast

# Discovery prefix template for HA autodiscovery topics.
DISCOVERY_TOPIC_TEMPLATE = "{discovery_prefix}/{component}/{device_id}/{object_id}/config"

# Topic templates (use str.format with device_id)
TOPICS: dict[str, str] = {
    "availability": "ctrlsolar/{device_id}/status",
    "set_power_state": "ctrlsolar/{device_id}/set_power/state",
    "set_power_attributes": "ctrlsolar/{device_id}/set_power/attributes",
}

# Hourly forecast topic template (use str.format with device_id and hour)
HOURLY_FORECAST_TOPIC_TEMPLATE: str = "ctrlsolar/{device_id}/hourly_forecast/hour_{hour}/state"

# Home Assistant discovery payload templates.
# These payloads contain placeholders (`{device_id}`, `{device_name}`, `{discovery_prefix}`) which should be filled by the caller using `.format(...)`.
DISCOVERY: dict[str, dict[str, Any]] = {
    "set_power": {
        "component": "sensor",
        "object_id": "power_target",
        "config": {
            "name": "{device_name} Power Target",
            "unique_id": "ctrlsolar_{device_id}_power_target",
            "state_topic": TOPICS["set_power_state"],
            "json_attributes_topic": TOPICS["set_power_attributes"],
            "unit_of_measurement": "W",
            "device_class": "power",
            "state_class": "measurement",
            "availability_topic": TOPICS["availability"],
            "device": {
                "identifiers": ["ctrlsolar_{device_id}"],
                "name": "{device_name}",
                "model": "ctrlsolar",
                "manufacturer": "ctrlsolar",
            },
        },
    },
}


def _fill(value: Any, device_id: str, device_name: str = "CtrlSolar") -> Any:
    if isinstance(value, str):
        return value.format(
            device_id=device_id,
            device_name=device_name,
            discovery_prefix="homeassistant",
        )
    if isinstance(value, dict):
        items = cast(dict[str, Any], value)
        return {key: _fill(item, device_id, device_name) for key, item in items.items()}
    if isinstance(value, list):
        items = cast(list[Any], value)
        return [_fill(item, device_id, device_name) for item in items]
    return value


def discovery_item(
    key: str,
    device_id: str,
    device_name: str = "CtrlSolar",
    discovery_prefix: str = "homeassistant",
) -> tuple[str, dict[str, Any]]:
    """Return (topic, payload) for a single discovery entry.

    The returned topic is formatted using `DISCOVERY_TOPIC_TEMPLATE` and the
    payload has placeholders filled with `device_id`, `device_name` and
    `discovery_prefix`.
    """
    item = DISCOVERY[key]
    topic = DISCOVERY_TOPIC_TEMPLATE.format(
        discovery_prefix=discovery_prefix,
        component=item["component"],
        device_id=f"ctrlsolar_{device_id}",
        object_id=item["object_id"],
    )
    return topic, _fill(item["config"], device_id, device_name)


def hourly_forecast_discovery_item(
    hour: int,
    device_id: str,
    device_name: str = "CtrlSolar",
    discovery_prefix: str = "homeassistant",
) -> tuple[str, dict[str, Any]]:
    """Return (topic, payload) for a single hourly forecast sensor.

    Each hour (0-23) gets its own sensor entity.
    Hour format shows the time range in the display name (e.g., "00:00-01:00").
    """
    hour_start = f"{hour:02d}:00"
    hour_end = f"{(hour + 1) % 24:02d}:00"
    time_range = f"{hour_start}-{hour_end}"
    
    object_id = f"hourly_forecast_hour_{hour}"
    topic = DISCOVERY_TOPIC_TEMPLATE.format(
        discovery_prefix=discovery_prefix,
        component="sensor",
        device_id=f"ctrlsolar_{device_id}",
        object_id=object_id,
    )
    state_topic = HOURLY_FORECAST_TOPIC_TEMPLATE.format(device_id=device_id, hour=hour)
    payload = {
        "name": f"{{device_name}} Forecast {time_range}",
        "unique_id": f"ctrlsolar_{{device_id}}_forecast_{time_range}",
        "state_topic": state_topic,
        "unit_of_measurement": "Wh",
        "device_class": "energy",
        "state_class": "measurement",
        "availability_topic": TOPICS["availability"],
        "device": {
            "identifiers": ["ctrlsolar_{device_id}"],
            "name": "{device_name}",
            "model": "ctrlsolar",
            "manufacturer": "ctrlsolar",
        },
    }
    return topic, _fill(payload, device_id, device_name)


def discovery_items(
    device_id: str,
    device_name: str = "CtrlSolar",
    discovery_prefix: str = "homeassistant",
) -> list[tuple[str, dict[str, Any]]]:
    """Return topic/payload pairs for all discovery entries.

    Includes set_power sensor and 24 hourly forecast sensors (one per hour).
    """
    items = [discovery_item("set_power", device_id, device_name, discovery_prefix)]
    items.extend(
        hourly_forecast_discovery_item(hour, device_id, device_name, discovery_prefix)
        for hour in range(24)
    )
    return items

