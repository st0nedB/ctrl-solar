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

- `CTRLSOLAR__MQTT__HOST`
- `CTRLSOLAR__MQTT__PORT`
- `CTRLSOLAR__MQTT__USERNAME`
- `CTRLSOLAR__MQTT__PASSWORD`

Optional overrides:

- `CTRLSOLAR__SITE__LATITUDE`
- `CTRLSOLAR__SITE__LONGITUDE`
- `CTRLSOLAR__SITE__TIMEZONE`

## What to update in `config.yaml`

Check the `defaults.yaml` file for the most useful available options. 
The total config is composed with `hydra`.
Keep secrets in `.env`, not in `config.yaml`.
