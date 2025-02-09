import time
import hashlib
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests

# Configuration
MONITOR_PATH = "/watched"  # Folder to monitor
SERVER_URL = "http://central-server:5000/analyze"  # Central detection system

class FileMonitorHandler(FileSystemEventHandler):
    def process(self, event):
        """Process file events"""
        if event.is_directory:
            return

        file_path = event.src_path
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return

        data = {
            "filename": file_path,
            "hash": file_hash,
            "event_type": event.event_type
        }

        # Send metadata to central system
        try:
            requests.post(SERVER_URL, json=data, timeout=5)
            print(f"Sent metadata: {data}")
        except Exception as e:
            print(f"Failed to send data: {e}")

    def on_created(self, event):
        self.process(event)

    def on_modified(self, event):
        self.process(event)

    def on_deleted(self, event):
        print(f"File deleted: {event.src_path}")

if __name__ == "__main__":
    observer = Observer()
    event_handler = FileMonitorHandler()
    observer.schedule(event_handler, MONITOR_PATH, recursive=True)

    print(f"Monitoring {MONITOR_PATH}...")
    observer.start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()