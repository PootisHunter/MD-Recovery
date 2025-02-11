# Use a lightweight Python base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the script and requirements
COPY requirements.txt .
COPY agent.py .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the file monitor script
CMD ["python", "agent.py"]