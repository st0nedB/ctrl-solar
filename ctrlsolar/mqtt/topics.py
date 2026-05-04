"""MQTT topic and Home Assistant autodiscovery helpers.

This module defines standard topic formats used by the project and
provides functions that generate Home Assistant discovery payloads
for the `set_power`, `hourly_forecast`, `hourly_solar_production`,
and `hourly_ac_production` sensors.

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

# Hourly forecast topic templates (one HA sensor; hidden 24-hour payload)
HOURLY_FORECAST_STATE_TOPIC_TEMPLATE: str = "ctrlsolar/{device_id}/hourly_forecast/state"
HOURLY_FORECAST_ATTRIBUTES_TOPIC_TEMPLATE: str = "ctrlsolar/{device_id}/hourly_forecast/attributes"

# Hourly production topic templates (one HA sensor per channel; hidden 24-hour payload)
HOURLY_SOLAR_PRODUCTION_STATE_TOPIC_TEMPLATE: str = "ctrlsolar/{device_id}/hourly_solar_production/state"
HOURLY_SOLAR_PRODUCTION_ATTRIBUTES_TOPIC_TEMPLATE: str = "ctrlsolar/{device_id}/hourly_solar_production/attributes"
HOURLY_AC_PRODUCTION_STATE_TOPIC_TEMPLATE: str = "ctrlsolar/{device_id}/hourly_ac_production/state"
HOURLY_AC_PRODUCTION_ATTRIBUTES_TOPIC_TEMPLATE: str = "ctrlsolar/{device_id}/hourly_ac_production/attributes"

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
    "hourly_solar_production": {
        "component": "sensor",
        "object_id": "hourly_solar_production",
        "config": {
            "name": "{device_name} Hourly Solar Production",
            "unique_id": "ctrlsolar_{device_id}_hourly_solar_production",
            "state_topic": HOURLY_SOLAR_PRODUCTION_STATE_TOPIC_TEMPLATE,
            "json_attributes_topic": HOURLY_SOLAR_PRODUCTION_ATTRIBUTES_TOPIC_TEMPLATE,
            "device_class": "date",
            "availability_topic": TOPICS["availability"],
            "device": {
                "identifiers": ["ctrlsolar_{device_id}"],
                "name": "{device_name}",
                "model": "ctrlsolar",
                "manufacturer": "ctrlsolar",
            },
        },
    },
    "hourly_ac_production": {
        "component": "sensor",
        "object_id": "hourly_ac_production",
        "config": {
            "name": "{device_name} Hourly AC Production",
            "unique_id": "ctrlsolar_{device_id}_hourly_ac_production",
            "state_topic": HOURLY_AC_PRODUCTION_STATE_TOPIC_TEMPLATE,
            "json_attributes_topic": HOURLY_AC_PRODUCTION_ATTRIBUTES_TOPIC_TEMPLATE,
            "device_class": "date",
            "availability_topic": TOPICS["availability"],
            "device": {
                "identifiers": ["ctrlsolar_{device_id}"],
                "name": "{device_name}",
                "model": "ctrlsolar",
                "manufacturer": "ctrlsolar",
            },
        },
    },
    "hourly_forecast": {
        "component": "sensor",
        "object_id": "hourly_forecast",
        "config": {
            "name": "{device_name} Hourly Forecast",
            "unique_id": "ctrlsolar_{device_id}_hourly_forecast",
            "state_topic": HOURLY_FORECAST_STATE_TOPIC_TEMPLATE,
            "json_attributes_topic": HOURLY_FORECAST_ATTRIBUTES_TOPIC_TEMPLATE,
            "device_class": "date",
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


def discovery_items(
    device_id: str,
    device_name: str = "CtrlSolar",
    discovery_prefix: str = "homeassistant",
) -> list[tuple[str, dict[str, Any]]]:
    """Return topic/payload pairs for all discovery entries.

    Includes set_power, hourly forecast, hourly solar production,
    and hourly AC production sensors.
    """
    items = [
        discovery_item("set_power", device_id, device_name, discovery_prefix),
        discovery_item("hourly_forecast", device_id, device_name, discovery_prefix),
        discovery_item("hourly_solar_production", device_id, device_name, discovery_prefix),
        discovery_item("hourly_ac_production", device_id, device_name, discovery_prefix),
    ]
    return items

