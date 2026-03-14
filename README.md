# ☀️⚡️🔋 ctrl-solar

<!-- [![PyPI version](https://img.shields.io/pypi/v/ctrl-solar.svg)](https://pypi.org/project/ctrl-solar/) -->
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A Python framework to monitor and control off-grid or grid-tied solar installations via a pluggable architecture.
Currently includes support for for Deye inverters and Noah2000 batteries via MQTT integrations, and the packaged CLI assembles a zero-consumption control loop to keep your home’s grid draw at zero and avoid over-production.

---

## 🔌 Extensible Architecture

* **Sensor/Consumer interface**

  * Abstract base classes (`Sensor`, `Consumer`) define how to read values and apply actions.
  * MQTT implementation (`MqttSensor`, `MqttConsumer`) provided as an example; add HTTP, Modbus, or other transports by subclassing.
* **Device support**

  * `Inverter` and `Battery` base classes define common interfaces.
  * Includes `DeyeSunM160G4` and `Noah2000` implementations; easily add other brands by extending these bases.
* **Controller core**

  * `ZeroConsumptionController` implements a strategy to match solar production and battery output to household load, avoiding grid draw.
  * Write new control strategies by subclassing the `Controller` base class.
* **Loop abstraction**

  * `Loop` helper schedules one or more controllers at a configurable interval.
* **Rich logging**

  * Colorized console output via [Rich](https://github.com/Textualize/rich)

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

The checked-in [docker-compose.yaml](/root/svc02.emptyvoid.xyz/ctrl-solar/docker-compose.yaml) is a consumer deployment example using the published image.

Required local files:
- `config.yaml`
- optionally `.env` for Docker Compose variable expansion

```bash
docker compose up -d
docker compose logs -f --tail=100
```

Keep sensitive values in a local `.env` file if you do not want them embedded directly in the compose file.

---

## 🧪 From Source

Cloning the repo is only needed for development or direct source runs.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
python -m ctrlsolar run --config ./config.yaml
```

---

## 🗂️ Project Structure

```
.
├── Dockerfile
├── docker-compose.yaml  # Published-image example deployment
├── config.yaml        # Sample runtime configuration
├── examples/
│   └── forecast.py    # Standalone forecast example
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

## 🛠️ Extending

This projects aims to be flexible to allow for the plethora of possible individual configurations.
The existing MQTT implementations for sensors/consumers provide a flexible start. 
Contributions are welcome! Please open an issue or submit a pull request.

* **Add new transports**

  * Subclass `Sensor`/`Consumer` in `ctrlsolar.io`.

* **Support additional inverters or batteries**

  * Extend `Inverter`/`Battery` in `ctrlsolar.controller`, wire into your transport.

* **Custom control strategies**

  * Subclass `Controller` and implement `update()` for bespoke logic.

* **Examples**

  * Standalone experiments such as the forecast demo live under [`examples/`](/root/svc02.emptyvoid.xyz/ctrl-solar/examples).

---

## 📦 Publishing

The intended release model is a published container image, for example:

```text
ghcr.io/emptyvoid/ctrl-solar:latest
```

A GitHub Actions workflow now builds the image on pull requests and publishes it to GHCR on pushes to `main` and tags like `v0.1.0`. Tagged releases can therefore pin immutable image versions instead of tracking `latest`.

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
