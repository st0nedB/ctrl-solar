# ctrl-solar

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> [!IMPORTANT]
> This release is not backward compatible to previous releases.
> It now requires [GroBro](https://github.com/robertzaage/GroBro) to work! 

Experimental MQTT-based power controller for NOAH2000 batteries.

## What does this project do?
Improve the rate of self-consumption for small solar plants with batteries.
Currently it supports control of NOAH2000 batteries via MQTT with [GroBro](https://github.com/robertzaage/GroBro).
The goal is simple: Ensure that by the end of the day, the battery is fully charged! 

**Controller strategy summary**
- Split the day into two phases: solar-powered and storage-powered.
- Solar phase: keep output between `power_min` and `power_max`, and reduce target only when needed to ensure the batteries end up fully charged.
- Storage phase: use battery energy to provide stable output during low/no solar periods.

Current scope is:
- Battery target: NOAH2000 only.
- Runtime dependency: GroBro instance connected to Home Assistant.

If interested, please open an issue. I'm open to extend support to other MQTT-based controllable batteries. 

## Runtime Model

1. Connect to MQTT broker.
2. Read NOAH2000 state from GroBro/Home Assistant topics.
3. Compute target output power from weather forecast + panel model.
4. Publish new NOAH2000 slot power setpoint.

## Required External System

- An MQTT broker
- Home Assistant with GroBro integration running.
- GroBro topics for the configured NOAH serial.

Expected topic pattern (serial uppercased):
- `homeassistant/grobro/{SERIAL}/availability`
- `homeassistant/grobro/{SERIAL}/state`
- `homeassistant/number/grobro/{SERIAL}/slot1_power/set`

Expected keys in `.../state` JSON payload:
- `tot_bat_soc_pct`
- `out_power`
- `bat_cnt`

## Configuration

For setup values, environment variables, and config keys, use:
- `example/README.md`
- `example/config.yaml`

## Run

Local:

```bash
python3 -m pip install -e .
set -a; source example/.env; set +a
python3 -m ctrlsolar.app --config-file example/config.yaml
```

Docker Compose:

```bash
docker compose -f example/docker-compose.yaml up -d
docker compose -f example/docker-compose.yaml logs -f --tail=100
```

## License

MIT. See [LICENSE](LICENSE).
