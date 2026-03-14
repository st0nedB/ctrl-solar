# ☀️⚡️🔋 ctrl-solar

<!-- [![PyPI version](https://img.shields.io/pypi/v/ctrl-solar.svg)](https://pypi.org/project/ctrl-solar/) -->
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A local-first solar control application for off-grid or grid-tied setups. It reads measurements from MQTT, tracks battery state, applies a control loop to limit inverter output, and can optionally use weather-based production forecasting to make better decisions.

---

## 📦 Installation & Usage

The primary deployment target is a published Docker image. You should not need to clone this repo just to run the controller.

## 🚀 Quick Start

Create a local `config.yaml`, then run:

```bash
docker run --rm \
  --name ctrl-solar \
  -v "$(pwd)/config.yaml:/app/config.yaml:ro" \
  -e CTRLSOLAR__MQTT__HOST=mqtt.example.com \
  -e CTRLSOLAR__MQTT__PORT=1883 \
  -e CTRLSOLAR__MQTT__USERNAME=your_username \
  -e CTRLSOLAR__MQTT__PASSWORD=your_password \
  ghcr.io/emptyvoid/ctrl-solar:latest
```

Logs will display colorized, real‑time updates:

```bash
docker logs -f --tail=100 ctrl-solar
```

---

## ⚙️ Configuration

Start from [`config.yaml`](/root/svc02.emptyvoid.xyz/ctrl-solar/config.yaml). It is the sample runtime configuration expected by both Docker and local source runs.

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

---

## 🐳 Docker Compose

For a human-friendly compose example, use the files under [`examples/`](/root/svc02.emptyvoid.xyz/ctrl-solar/examples):

- [`examples/README.md`](/root/svc02.emptyvoid.xyz/ctrl-solar/examples/README.md)
- [`examples/docker-compose.yaml`](/root/svc02.emptyvoid.xyz/ctrl-solar/examples/docker-compose.yaml)
- [`examples/.env`](/root/svc02.emptyvoid.xyz/ctrl-solar/examples/.env)
- [`examples/config.yaml`](/root/svc02.emptyvoid.xyz/ctrl-solar/examples/config.yaml)

Those files are meant to be copied into a deployment directory and edited by hand.

---

## 🗂️ Project Structure

```
.
├── Dockerfile
├── docker-compose.yaml  # Published-image example deployment
├── config.yaml        # Sample runtime configuration
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
    ├── batter     # Battery implementations
    ├── controller # Controller implementations
    └── loop.py    # Loop scheduler for controller(s)
```

---

## 🛠️ Development

For source development, create a local virtual environment, install the package in editable mode, and run `python -m ctrlsolar run --config ./config.yaml`. The published container image is built by GitHub Actions and pushed to GHCR, for example:

```text
ghcr.io/emptyvoid/ctrl-solar:latest
```

The codebase is structured so new transports, device integrations, and controller strategies can be added inside [`ctrlsolar/`](/root/svc02.emptyvoid.xyz/ctrl-solar/ctrlsolar). Contributions are welcome.

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
