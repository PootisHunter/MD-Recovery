# Use lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy the script
COPY agent.py .

# Install dependencies
RUN pip install watchdog requests

# Create a volume for monitoring
VOLUME ["/watched"]

# Run the script
CMD ["python", "agent.py"]