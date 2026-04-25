# Docker Compose Example

This directory is a complete example deployment for `ctrl-solar` using Docker Compose and the published container image.

Files in this directory:

- `docker-compose.yaml`
- `.env`
- `config.yaml`

## How to use it

1. Copy these files into your deployment directory.
2. Edit `.env` and set MQTT credentials.
3. Edit `config.yaml` for site settings like host, battery serial, and panels.
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

- `host`
- `port`
- `battery_sn`
- `update_interval_s`
- `panels`

Keep secrets in `.env`, not in `config.yaml`.
