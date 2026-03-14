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

Use the example files in [`examples/`](examples/):

- [`examples/README.md`](examples/README.md)
- [`examples/docker-compose.yaml`](examples/docker-compose.yaml)
- [`examples/.env`](examples/.env)
- [`examples/config.yaml`](examples/config.yaml)

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

Start from [`config.yaml`](config.yaml). It is the sample runtime configuration expected by both Docker and local source runs.

For deployment-specific overrides, environment variables can override nested config values using the `CTRLSOLAR__...` prefix:

```dotenv
CTRLSOLAR__MQTT__HOST=mqtt.example.com
CTRLSOLAR__MQTT__PORT=1883
CTRLSOLAR__MQTT__USERNAME=your_username
CTRLSOLAR__MQTT__PASSWORD=your_password
CTRLSOLAR__SITE__LATITUDE=42.46903090913205
CTRLSOLAR__SITE__LONGITUDE=-71.35063628495487
CTRLSOLAR__SITE__TIMEZONE=America/New_York
```

Typical split:
- keep non-secret runtime settings in `config.yaml`
- pass secrets and installation-specific values through environment variables
- mount `config.yaml` into the container at `/app/config.yaml`

### Minimum Required Values

Review at least these fields for a working installation:

- `mqtt.host`, `mqtt.port`, `mqtt.username`, `mqtt.password`
- `site.latitude`, `site.longitude`, `site.timezone`
- `batteries[*].serial`
- `batteries[*].panels`
- `powermeter.topic`
- `inverter.topic_prefix`

### How To Adapt It To Your System

Typical installation-specific changes:

- change `powermeter.topic` to your actual meter topic
- change `powermeter.filter.path` if the numeric power value lives elsewhere in the JSON payload
- change `inverter.topic_prefix` if your Deye topics use another prefix
- change `batteries[*].serial` to your actual battery serials
- change `batteries[*].panels` to match your real panel geometry
- change `site.*` or override it through environment variables

### MQTT Topic Expectations

The built-in integrations assume:

- the powermeter topic publishes JSON and `powermeter.filter.path` resolves to a numeric value
- the Deye inverter uses the configured `inverter.topic_prefix` for production telemetry and limit commands
- each Noah2000 battery serial maps to the expected MQTT topics for state, limits, production, and mode switching

If your topics or payloads differ from that shape, update the configuration where possible. If the built-in integration does not match your payload structure, code changes will be required.

---
## 🐳 Docker Compose

For a compose example, use the files under [`examples/`](examples/):

- [`examples/README.md`](examples/README.md)
- [`examples/docker-compose.yaml`](examples/docker-compose.yaml)
- [`examples/.env`](examples/.env)
- [`examples/config.yaml`](examples/config.yaml)

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
- check that `powermeter.filter.path` matches the actual JSON payload
- check that `batteries[*].serial` matches the serials exposed on MQTT

### The inverter limit never changes

- check `inverter.topic_prefix`
- confirm the inverter control topics exist on the broker
- confirm the meter signal is valid and not permanently missing

### Forecast output is wrong or missing

- check `site.latitude`, `site.longitude`, and `site.timezone`
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
├── config.yaml          # Sample runtime configuration
├── examples/
│   ├── README.md
│   ├── docker-compose.yaml
│   ├── .env
│   └── config.yaml
└── ctrlsolar/
    ├── assembly   # Runtime assembly from configuration
    ├── config     # Config defaults, models, and loader
    ├── io         # Sensor, Consumer abstractions and MQTT examples
    ├── inverter   # Inverter implementations
    ├── battery    # Battery implementations
    ├── controller # Controller implementations
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
python -m ctrlsolar run --config ./config.yaml
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
