FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY detector.py .
COPY rules ./rules

CMD ["python", "detector.py"]
# Project version: SentinelX V1.6




