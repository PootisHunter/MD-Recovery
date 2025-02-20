from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
from prometheus_client import start_http_server, Counter
import uvicorn

app = FastAPI()

# Prometheus Metrics
ALERTS_RECEIVED = Counter("alerts_received_total", "Total alerts received", ["severity"])
ALERTS_SENT_TO_ADMIN = Counter("alerts_sent_to_admin_total", "Total alerts successfully sent to admin")

# Environment Variables
ADMIN_API_URL = os.getenv("ADMIN_API_URL", "http://admin-system/receive-alert")
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "YOUR_API_KEY")  # Change this

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

@app.post("/alert")
def receive_alert(alert: Alert):
    """Receives alerts from file-monitoring agents and checks VirusTotal."""
    print(f"🔔 Received Alert: {alert}")

    ALERTS_RECEIVED.labels(severity=alert.severity).inc()

    # Check file hash in VirusTotal
    vt_report = check_virustotal(alert.hash)

    # Forward alert to admin with VT report if available
    response = forward_to_admin(alert, vt_report)

    return {"message": "Alert received", "admin_response": response}

def check_virustotal(hash_value: str):
    """Checks the file hash in VirusTotal."""
    url = f"https://www.virustotal.com/api/v3/files/{hash_value}"
    headers = {"x-apikey": VIRUSTOTAL_API_KEY}

    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()  # Return the VirusTotal response if found
        else:
            print("⚠️ Hash not found in VirusTotal or API limit reached.")
            return None
    except Exception as e:
        print(f"❌ Error querying VirusTotal: {e}")
        return None

def forward_to_admin(alert: Alert, vt_report: dict):
    """Sends alert details (including VirusTotal report) to the administrator REST API."""
    alert_data = alert.model_dump()
    
    # Include VirusTotal report if available
    if vt_report:
        alert_data["virustotal_report"] = vt_report

    try:
        response = requests.post(ADMIN_API_URL, json=alert_data, timeout=5)

        if response.status_code == 200:
            ALERTS_SENT_TO_ADMIN.inc()
            print("✅ Alert successfully forwarded to administrator.")
            return response.json()
        else:
            print(f"❌ Failed to send alert: {response.status_code}")
            return {"error": "Failed to send alert", "status_code": response.status_code}
    except Exception as e:
        print(f"❌ Exception in forwarding alert: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    start_http_server(9001)
    uvicorn.run(app, host="0.0.0.0", port=8000)