FROM python:3.13-slim

workdir /app

copy requirements.txt .
run pip install --no-cache-dir -r requirements.txt

copy . .

expose 5000

cmd ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "run:app"]
