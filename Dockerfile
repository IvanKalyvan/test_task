FROM python:3.12.4-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

WORKDIR /app/app

CMD alembic -c alembic.ini upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000
