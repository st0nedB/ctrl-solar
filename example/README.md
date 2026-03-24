# Docker Compose Example

This directory is a complete example deployment for `ctrl-solar` using Docker Compose and the published container image.

Files in this directory:

- `docker-compose.yaml`
- `.env`
- `config.yaml`

## How to use it

1. Copy these files into your deployment directory.
2. Edit `.env` and update the MQTT credentials and any site-specific override values.
3. Edit `config.yaml` for the non-secret runtime settings such as battery serials, inverter topic prefixes, and panel definitions.
4. Start the service:

```bash
docker compose up -d
docker compose logs -f --tail=100
```

## What to update in `.env`

Required in most setups:

- `MQTT_USERNAME`
- `MQTT_PASSWORD`

## What to update in `config.yaml`

Set broker and runtime-specific values here, especially:

- `mqtt.host`
- `mqtt.port`
- `loop.controllers[0].inverter.topic`
- `loop.controllers[0].meter.topic`

Keep secrets in `.env`, not in `config.yaml`.
