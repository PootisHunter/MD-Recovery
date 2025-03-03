import time
import hashlib
import json
import socket
import uuid
from prometheus_client import start_http_server, Counter
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import zipfile
import os
import uvicorn


# Prometheus Metrics
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", 9000))
FILE_EVENTS = Counter("file_events_total", "Total file events", ["event_type"])

# Configuration
CLIENT_ID = str(uuid.uuid4())  # Unique Client ID
IP_ADDRESS = socket.gethostbyname(socket.gethostname())  # Get IP address
HOSTNAME = socket.gethostname()  # Get hostname
MONITOR_PATH = "/home/"  # Folder to monitor
SERVER_URL = os.getenv("SERVER_URL", "http://alert-handler:8002/alert")
BACKUP_NODE_URL = os.getenv("BACKUP_NODE_URL", "http://backup-node:8003/api/backup")

app = FastAPI()

# Request model for receiving backup trigger
class BackupRequest(BaseModel):
    action: str  # The action to trigger backup (e.g., "backup")
    timestamp: str  # The timestamp for backup

# Monitor file events
class FileMonitorHandler(FileSystemEventHandler):
    def process(self, event):
        """Process file events"""
        if event.is_directory:
            return

        file_path = event.src_path
        event_type = event.event_type
        FILE_EVENTS.labels(event_type=event_type).inc()
        try:
            # Calculate file hash
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return

        # Prepare data to send (include client info)
        data = {
            "client_id": CLIENT_ID,
            "ip_address": IP_ADDRESS,
            "hostname": HOSTNAME,
            "filename": file_path,
            "hash": file_hash,
            "event_type": event.event_type,
            "severity": "low",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())  # Timestamp of the event
        }

        # Send metadata to central system
        try:
            response = requests.post(SERVER_URL, json=data, timeout=5)
            if response.status_code == 200:
                print(f"Sent metadata successfully: {data}")
            else:
                print(f"Failed to send metadata. Server responded with: {response.status_code}")
        except Exception as e:
            print(f"Failed to send data: {e}")

    def on_created(self, event):
        """Handle file creation event"""
        self.process(event)

    def on_modified(self, event):
        """Handle file modification event"""
        self.process(event)

    def on_deleted(self, event):
        """Handle file deletion event"""
        print(f"File deleted: {event.src_path}")

# Backup process functions
def zip_folder(folder_path, zip_filename):
    """Zip the entire folder and return the path to the zip file."""
    zip_filepath = f"/tmp/{zip_filename}"
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through the directory and add files to the zip archive
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, folder_path))
    return zip_filepath

def send_backup_to_node(zip_file_path):
    """Send the zip file to the backup node via HTTP POST request."""
    try:
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S", time.gmtime())  # Create a timestamp for the backup
        filename = os.path.basename(zip_file_path)  # Use the zip file name as the backup filename

        # Send the backup file to the backup node's /api/backup endpoint
        with open(zip_file_path, 'rb') as file:
            files = {'file': (filename, file, 'application/zip')}
            data = {'timestamp': timestamp, 'filename': filename, 'client_id': CLIENT_ID}  # Include client_id
            response = requests.post(BACKUP_NODE_URL, data=data, files=files)

        # Handle the response
        if response.status_code == 200:
            print(f"Backup sent successfully: {response.json()}")
        else:
            print(f"Failed to send backup: {response.json()}")
    except Exception as e:
        print(f"Error sending backup to node: {e}")

def backup_files():
    """Trigger the file backup."""
    zip_filename = f"backup_{time.strftime('%Y-%m-%d_%H-%M-%S', time.gmtime())}.zip"

    # Step 1: Zip the folder
    zip_file_path = zip_folder(MONITOR_PATH, zip_filename)

    # Step 2: Send the zip file to the backup node
    send_backup_to_node(zip_file_path)

    # Step 3: Optionally, remove the zip file after sending (if no longer needed)

# Backup API route
@app.post("/api/backup")
def trigger_backup(backup_request: BackupRequest):
    """Endpoint to receive backup trigger and start the backup process."""
    if backup_request.action == "backup":
        print(f"Backup requested at {backup_request.timestamp}. Triggering backup...")
        backup_files()  # Call the backup function when requested
        return {"status": "success", "message": "Backup initiated"}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

@app.get("/api/health")
def health():
    """Health check endpoint."""
    return {"status": "Client agent healthy"}

if __name__ == "__main__":
    # Set up file monitoring
    start_http_server(PROMETHEUS_PORT)
    observer = Observer()
    event_handler = FileMonitorHandler()
    observer.schedule(event_handler, MONITOR_PATH, recursive=True)

    print(f"Monitoring {MONITOR_PATH} for changes...")
    observer.start()

    # Start FastAPI server for backup listening
    uvicorn.run(app, host="0.0.0.0", port=8000)

    try:
        while True:
            time.sleep(10)  # Sleep to allow monitoring events
    except KeyboardInterrupt:
        observer.stop()

    observer.join()