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

# Create a backup storage directory
RUN mkdir -p backups

# Expose necessary ports (9000 for Flask API)
EXPOSE 9000

# Run the backup node service
CMD ["python", "backup_node.py"]
