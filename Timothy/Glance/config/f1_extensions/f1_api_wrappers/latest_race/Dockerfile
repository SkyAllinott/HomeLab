FROM python:3.11-slim

WORKDIR /app

COPY ./current_race_cleaner.py /app/main.py

RUN pip install fastapi uvicorn requests pytz

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "4463"]
