# Use the official Python image
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

# Expose ports (9000 for Prometheus metrics, 8000 for FastAPI)
EXPOSE 9000 8000

# Command to run the application
CMD ["python", "agent.py"]