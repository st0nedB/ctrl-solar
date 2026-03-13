# ☀️⚡️🔋 ctrl-solar

<!-- [![PyPI version](https://img.shields.io/pypi/v/ctrl-solar.svg)](https://pypi.org/project/ctrl-solar/) -->
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A Python framework to monitor and control off-grid or grid-tied solar installations via a pluggable architecture.
Currently includes support for for Deye inverters and Noah2000 batteries via MQTT integrations, and the packaged CLI assembles a zero-consumption control loop to keep your home’s grid draw at zero and avoid over-production.

> [!IMPORTANT]
> This project is work-in-progress. Expect errors and bugs. I'll try to support on a best-effort basis.

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

No manual installation is required. The application runs through the packaged `ctrlsolar` entrypoint, and Docker Compose uses that same entrypoint. Simply run:

```bash
docker-compose up -d
```

Logs will display colorized, real‑time updates:

```bash
docker-compose logs -f --tail=100
```

---

## ⚙️ Configuration

Edit [`config.yaml`](/root/svc02.emptyvoid.xyz/ctrl-solar/config.yaml) for the main runtime configuration. For deployment-specific overrides, environment variables can override nested config values using the `CTRLSOLAR__...` prefix:

```dotenv
CTRLSOLAR__MQTT__HOST=mqtt.example.com
CTRLSOLAR__MQTT__PORT=1883
CTRLSOLAR__MQTT__USERNAME=your_username
CTRLSOLAR__MQTT__PASSWORD=your_password
CTRLSOLAR__SITE__LATITUDE=47.1234
CTRLSOLAR__SITE__LONGITUDE=12.5678
CTRLSOLAR__SITE__TIMEZONE=Europe/Berlin
```

> [!NOTE]
> The application no longer depends on `rootutils` or YAML `!env` tags. Local runs and Docker use the same packaged entrypoint, and sensitive deployment values such as plant coordinates can stay out of the checked-in config via env overrides.

---

## 🚀 Usage

### From source

```bash
python -m ctrlsolar run --config ./config.yaml
```

### With Docker

1. Adapt `config.yaml` with your own setup

2. Build and run with Docker Compose:

```bash
  docker compose up -d
```

---

## 🗂️ Project Structure

```
.
├── Dockerfile
├── docker-compose.yaml
├── main.py            # Compatibility wrapper for the packaged CLI
├── requirements.txt
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

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
