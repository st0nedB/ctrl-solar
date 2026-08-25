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

The dashboard is disabled by default in `config.yaml`. If enabled, expose it only on trusted networks or behind a reverse proxy.

History uses SQLite and is disabled by default. Enable `history.enabled` to store runtime snapshots for dashboard history.

Calibration learns hourly forecast factors from stored history. Enable `calibration.enabled` to learn factors, and set `calibration.apply: true` only when you want learned factors applied to future forecasts.
