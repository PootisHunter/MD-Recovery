FROM python:3.10-slim

WORKDIR /app

COPY alert_handler.py .

RUN pip install fastapi uvicorn requests

EXPOSE 8000

CMD ["uvicorn", "alert_handler:app", "--host", "0.0.0.0", "--port", "8000"]