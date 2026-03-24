FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md /app/
COPY ctrlsolar /app/ctrlsolar

RUN python -m pip install /app

CMD ["python", "-m", "ctrlsolar.app", "--config-path", "/app", "--config-name", "config"]
