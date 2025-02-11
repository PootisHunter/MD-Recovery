import time
import hashlib
import json
import socket
import uuid
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests

# Configuration
CLIENT_ID = str(uuid.uuid4())  # Unique Client ID
IP_ADDRESS = socket.gethostbyname(socket.gethostname())  # Get IP address
HOSTNAME = socket.gethostname()  # Get hostname
MONITOR_PATH = "/home/"  # Folder to monitor
SERVER_URL = "http://central-server:5000/alert"  # Central detection system

class FileMonitorHandler(FileSystemEventHandler):
    def process(self, event):
        """Process file events"""
        if event.is_directory:
            return

        file_path = event.src_path
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


if __name__ == "__main__":
    # Set up file monitoring
    observer = Observer()
    event_handler = FileMonitorHandler()
    observer.schedule(event_handler, MONITOR_PATH, recursive=True)

    print(f"Monitoring {MONITOR_PATH} for changes...")
    observer.start()

    try:
        while True:
            time.sleep(10)  # Sleep to allow monitoring events
    except KeyboardInterrupt:
        observer.stop()

    observer.join()