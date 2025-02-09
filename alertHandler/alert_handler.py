from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests

app = FastAPI()

# Administrator API URL (replace with actual endpoint)
ADMIN_API_URL = os.getenv("ADMIN_API_URL", "http://admin-system/receive-alert")

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
    """Receives alerts from file-monitoring agents."""
    print(f"🔔 Received Alert: {alert}")

    # Forward alert to the admin REST API
    response = forward_to_admin(alert)

    return {"message": "Alert received", "admin_response": response}

def forward_to_admin(alert: Alert):
    """Sends alert details to the administrator REST API."""
    try:
        payload = alert.dict()
        response = requests.post(ADMIN_API_URL, json=payload, timeout=5)

        if response.status_code == 200:
            print("✅ Alert successfully forwarded to administrator.")
            return response.json()
        else:
            print(f"❌ Failed to send alert: {response.status_code}")
            return {"error": "Failed to send alert", "status_code": response.status_code}
    except Exception as e:
        print(f"❌ Exception in forwarding alert: {e}")
        return {"error": str(e)}