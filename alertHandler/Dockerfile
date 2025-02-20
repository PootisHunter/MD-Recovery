# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose necessary ports (8000 for FastAPI, 9001 for Prometheus metrics)
EXPOSE 8000 9001

# Run the alert handler service
CMD ["python", "alert_handler.py"]