# ☀️⚡️🔋 ctrl-solar

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A local-first solar control application for off-grid or grid-tied setups. It reads measurements from MQTT, tracks battery state, applies a control loop to limit inverter output, and can optionally use weather-based production forecasting.

---
## ✅ Supported Setup

The current release is intended for this setup:

- MQTT as the runtime transport
- Deye microinverter telemetry and power-limit control
- Noah2000 battery telemetry and mode control
- Docker Compose as the primary deployment method

If your setup differs significantly from that, expect to adapt topics, payload handling, or device integrations.

---
## 📦 Installation & Usage

The primary deployment target is a published Docker image. You should not need to clone this repo just to run the controller.

## 🚀 Quick Start

Use the example files in [`example/`](example/):

- [`example/README.md`](example/README.md)
- [`example/docker-compose.yaml`](example/docker-compose.yaml)
- [`example/.env`](example/.env)
- [`example/config.yaml`](example/config.yaml)

Copy them into your deployment directory, update `.env` and `config.yaml`, then run:

```bash
docker compose up -d
```

Make sure everything works properly by monitoring the logs:
```bash
docker compose logs -f --tail=100
```

---
## ⚙️ Configuration

Use [`example/config.yaml`](example/config.yaml) as the canonical sample configuration.

Use `.env` for MQTT credentials:

```dotenv
MQTT_USERNAME=your_username
MQTT_PASSWORD=your_password
```

Typical split:
- keep non-secret runtime settings in `config.yaml`
- pass secrets through environment variables
- mount `config.yaml` into the container at `/app/config.yaml`

### Minimum Required Values

Review at least these fields for a working installation:

- `.env`: `MQTT_USERNAME`, `MQTT_PASSWORD`
- `config.yaml`: `mqtt.host`, `mqtt.port`
- `config.yaml`: `loop.controllers[0].inverter.topic`
- `config.yaml`: `loop.controllers[0].meter.topic`

### How To Adapt It To Your System

Typical installation-specific changes:

- change `mqtt.host` and `mqtt.port` to your broker
- set `.env` `MQTT_USERNAME` and `MQTT_PASSWORD`
- change `loop.controllers[0].meter.topic` to your powermeter topic
- adjust the meter filter (`loop.controllers[0].meter.filter`) to match your JSON payload shape
- change `loop.controllers[0].inverter.topic` if your Deye topics use another prefix

### MQTT Topic Expectations

The built-in integrations assume:

- the powermeter topic publishes JSON and the configured meter filter resolves to a numeric value
- the Deye inverter uses `loop.controllers[0].inverter.topic` for production telemetry and limit commands

If your topics or payloads differ from that shape, update the configuration where possible. If the built-in integration does not match your payload structure, code changes will be required.

---
## 🐳 Docker Compose

For a compose example, use the files under [`example/`](example/):

- [`example/README.md`](example/README.md)
- [`example/docker-compose.yaml`](example/docker-compose.yaml)
- [`example/.env`](example/.env)
- [`example/config.yaml`](example/config.yaml)

Those files are meant to be copied into a deployment directory and edited.

---
## 🔎 Verify Your Installation

After startup, confirm the installation with these checks:

- `docker compose logs -f --tail=100` shows regular controller updates
- meter, inverter, and battery values are no longer `N/A`
- battery serials shown in logs match your actual devices
- inverter production limits change when sustained import or export occurs
- forecast output appears when site coordinates and timezone are correct

If these checks pass, the setup is usually wired correctly.

---
## 🛠️ Troubleshooting

### No updates appear in the logs

- confirm the container is running
- confirm MQTT credentials are correct
- confirm the broker is reachable from the container

### Values stay `N/A`

- check the configured MQTT topics
- check that `loop.controllers[0].meter.filter` matches the actual JSON payload

### The inverter limit never changes

- check `loop.controllers[0].inverter.topic`
- confirm the inverter control topics exist on the broker
- confirm the meter signal is valid and not permanently missing

### Forecast output is wrong or missing

- check `loop.controllers[1].forecast.latitude`, `longitude`, and `timezone`
- confirm the runtime can reach the weather API

### Compose starts, but it behaves like the wrong installation

- check whether `.env` overrides are replacing values from `config.yaml`
- confirm you copied the intended `config.yaml` into the deployment directory

---
## 🗂️ Project Structure

```text
.
├── Dockerfile
├── docker-compose.yaml  # Published-image example deployment
├── example/
│   ├── README.md
│   ├── docker-compose.yaml
│   ├── .env
│   └── config.yaml
└── ctrlsolar/
    ├── abstracts  # Core interfaces
    ├── io         # Sensor, Consumer abstractions and MQTT examples
    ├── inverter   # Inverter implementations
    ├── battery    # Battery implementations
    ├── controller # Controller implementations
    ├── panels     # Forecast and panel models
    └── loop.py    # Loop scheduler for controller(s)
```

---
## 🛠️ Development

For source development:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
python -m unittest discover -s tests -v
python -m ctrlsolar.app --config-path ./example --config-name config
```

The published container image is built by GitHub Actions and pushed to GHCR, for example:

```text
ghcr.io/emptyvoid/ctrl-solar:latest
```

Use pinned tags such as `ghcr.io/emptyvoid/ctrl-solar:v0.1.0` for stable deployments instead of tracking `latest`.

The codebase is structured so new transports, device integrations, and controller strategies can be added inside [`ctrlsolar/`](ctrlsolar/). Contributions are welcome.

---
## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
