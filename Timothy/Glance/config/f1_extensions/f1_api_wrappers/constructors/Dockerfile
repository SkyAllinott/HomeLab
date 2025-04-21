FROM python:3.11-slim

WORKDIR /app

COPY ./constructors_cleaner.py /app/main.py

RUN pip install fastapi uvicorn requests pytz pycountry httpx fastapi-cache2

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "6344"]
