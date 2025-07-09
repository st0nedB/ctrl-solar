# ☀️⚡️🔋 ctrl-solar

<!-- [![PyPI version](https://img.shields.io/pypi/v/ctrl-solar.svg)](https://pypi.org/project/ctrl-solar/) -->
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A Python framework to monitor and control off-grid or grid-tied solar installations via a pluggable architecture.
Currently includes support for for Deye inverters and Noah2000 batteries via MQTT integrations, `main.py` shows how to implement a  zero-consumption control to keep your home’s grid draw at zero and avoid over-production.

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

No manual installation is required—**ctrl-solar** is packaged with \[rootutils], and the default entrypoint is configured in Docker Compose. Simply run:

```bash
docker-compose up -d
```

Logs will display colorized, real‑time updates:

```bash
docker-compose logs -f --tail=100
```

---

## ⚙️ Configuration

Create a `.env` file in the project root with your broker credentials and parameters:

```dotenv
MQTT_URL=mqtt.example.com
MQTT_PORT=1883
MQTT_USER=your_username
MQTT_PASSWD=your_password
```

> [!NOTE]
> If you are not planning to use the provided MQTT classes you can skip the `.env` file. Adapt the main.py with your own Sensor configurations. The current version contains example values.

---

## 🚀 Usage

### From source

```bash
# Ensure `.env` is in place, then:
python main.py
```

### With Docker

1. Build and run with Docker Compose:

   ```bash
   ```

docker-compose up -d

````
1. Stream logs to see colorized updates:
   ```bash
docker-compose logs -f --tail=100
````

---

## 🗂️ Project Structure

```
.
├── Dockerfile
├── docker-compose.yaml
├── main.py            # Entry point: configures transports, devices, controller, loop
├── requirements.txt
└── ctrlsolar/
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

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
