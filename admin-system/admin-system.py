from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import requests
import os
import uvicorn
from prometheus_client import start_http_server, Counter

app = FastAPI()

# Prometheus Metrics
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", 9002))
ALERTS_RECEIVED_FROM_MONITOR = Counter("alerts_received_from_monitor_total", "Total alerts received from monitoring system")

# Alert data model
class Alert(BaseModel):
    client_id: str
    ip_address: str
    hostname: str
    filename: str
    hash: str
    event_type: str
    severity: str
    timestamp: str
    virustotal_report: Optional[dict] = None

@app.post("/receive-alert")
def receive_alert(alert: Alert):
    """Receives alerts from the file-monitoring system."""
    print(f"🔔 Received Alert from Monitoring System: {alert}")

    ALERTS_RECEIVED_FROM_MONITOR.inc()

    # Log the alert data (this can be extended to store data in DB, etc.)
    if alert.virustotal_report:
        print("🦠 VirusTotal Report:", alert.virustotal_report)
    else:
        print("🚫 No VirusTotal report available")

    return {"message": "Alert received by Admin System", "client_id": alert.client_id}

class BackupRequest(BaseModel):
    action: str
    timestamp: str

@app.post("/trigger-backup")
def trigger_backup(backup_request: BackupRequest):
    """Trigger backup request to the agent system."""
    if backup_request.action == "backup":
        print(f"Backup requested at {backup_request.timestamp}. Sending request to Agent to start backup...")

        AGENT_API_URL = "http://agent-system:8000/api/backup"  # The actual agent URL
        # Send POST request to Agent system to trigger backup
        try:
            response = requests.post(AGENT_API_URL, json=backup_request.dict(), timeout=5)
            if response.status_code == 200:
                return {"status": "success", "message": "Backup triggered successfully"}
            else:
                raise HTTPException(status_code=500, detail="Failed to trigger backup in Agent system")
        except requests.exceptions.RequestException as e:
            print(f"Error triggering backup: {e}")
            raise HTTPException(status_code=500, detail="Error connecting to Agent system")

    else:
        raise HTTPException(status_code=400, detail="Invalid action. Only 'backup' is allowed")

@app.get("/health")
def health():
    """Health check endpoint for the admin system."""
    return {"status": "Admin System is healthy"}

if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(PROMETHEUS_PORT)
    uvicorn.run(app, host="0.0.0.0", port=8001)
