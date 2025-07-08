FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN python -m pip install -r /app/requirements.txt

CMD ["python", "/app/main.py"]