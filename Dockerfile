FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN python -m pip install /app

CMD ["ctrlsolar", "run", "--config", "/app/config.yaml"]
