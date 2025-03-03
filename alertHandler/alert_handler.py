from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import requests
from prometheus_client import start_http_server, Counter
import uvicorn
from datetime import datetime, timedelta, timezone
import openai
from collections import deque

app = FastAPI()

# Prometheus Metrics
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", 9001))
ALERTS_RECEIVED = Counter("alerts_received_total", "Total alerts received", ["severity"])
ALERTS_SENT_TO_ADMIN = Counter("alerts_sent_to_admin_total", "Total alerts successfully sent to admin")
ALERTS_SPIKE_DETECTED = Counter("alerts_spike_detected_total", "Total spike alerts detected and sent to admin")
# Environment Variables
ADMIN_API_URL = os.getenv("ADMIN_API_URL", "http://admin-system/receive-alert")
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY", "YOUR_API_KEY")  # Change this
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")

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

# Track alert timestamps to detect spikes
alert_timestamps = deque()
ALERT_THRESHOLD = 100  # Set the threshold for spike (e.g., 100 alerts in 5 minutes)
TIME_WINDOW = timedelta(minutes=5)  # 5-minute window for spike detection

@app.post("/alert")
def receive_alert(alert: Alert):
    """Receives alerts from file-monitoring agents and checks VirusTotal."""
    print(f"🔔 Received Alert: {alert}")

    ALERTS_RECEIVED.labels(severity=alert.severity).inc()

    current_time = datetime.now(timezone.utc)
    alert_timestamps.append((alert, current_time))

    while alert_timestamps and alert_timestamps[0] < current_time - TIME_WINDOW:
        alert_timestamps.popleft()
    # Check file hash in VirusTotal
    vt_report = check_virustotal(alert.hash)

    cutoff_time = datetime.now(timezone.utc) - TIME_WINDOW
    alert_timestamps[:] = [timestamp for timestamp in alert_timestamps if timestamp > cutoff_time]

    if len(alert_timestamps) > ALERT_THRESHOLD:
        print("⚠️ Spike detected! More than 10 alerts in the last 5 minutes.")
        spike_response = notify_admin_of_spike()
        ALERTS_SPIKE_DETECTED.inc()  # Increment the spike metric
        return {"message": "Alert spike detected and admin notified", "spike_alert_response": spike_response}

    # Forward alert to admin with VT report if VT report is returned
    if vt_report is not None:
        response = forward_to_admin(alert, vt_report)
        return {"message": "Alert received", "admin_response": response}
    else:
        print("⚠️ No VirusTotal match found, alert will not be forwarded to admin.")
        return {"message": "Alert received, but no VirusTotal match found. Not forwarded to admin."}  

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

def notify_admin_of_spike():
    """Uses OpenAI API to create a spike alert message and forwards it to the admin."""
    # Define a time window and count the alerts
    spike_start_time = datetime.now(timezone.utc) - TIME_WINDOW
    spike_alerts = [alert for alert, timestamp in alert_timestamps if timestamp > spike_start_time]
    num_alerts_in_spike = len(spike_alerts)

    # Create a detailed spike alert message
    spike_message = (
        f"⚠️ Urgent Alert: A spike has been detected in the last {TIME_WINDOW} minutes.\n"
        f"- Total alerts received: {num_alerts_in_spike}\n"
        f"- Severity levels: {', '.join(set([alert.severity for alert in spike_alerts]))}\n"
        f"- Time window: From {spike_start_time} to {datetime.utcnow()}\n"
        f"- Event Types: {', '.join(set([alert.event_type for alert in spike_alerts]))}\n"
        f"- Client Information: {', '.join(set([alert.client_id for alert in spike_alerts]))}\n"
        f"\nPlease investigate the situation immediately."
    )

    # Generate the alert message using OpenAI
    openai.api_key = OPENAI_API_KEY

    prompt = f"Generate an alert message for the admin about an alert spike in the system. Include details like the number of alerts, severity levels, event types, and affected clients:\n\n{spike_message}"

    try:
        # Generate the spike message using OpenAI's API
        response = openai.Completion.create(
            engine="text-davinci-003",  # You can choose the engine that fits your use case
            prompt=prompt,
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.7
        )
        message = response.choices[0].text.strip()
        print("Generated Spike Alert Message:", message)

        # Send the generated message to the admin system
        response = requests.post(ADMIN_API_URL, json={"message": message}, timeout=5)

        if response.status_code == 200:
            print("✅ Spike alert message sent to admin.")
            return response.json()
        else:
            print(f"❌ Failed to send spike alert message: {response.status_code}")
            return {"error": "Failed to send spike alert", "status_code": response.status_code}

    except Exception as e:
        print(f"❌ Error in generating spike alert message: {e}")
        return {"error": str(e)}

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
    start_http_server(PROMETHEUS_PORT)
    uvicorn.run(app, host="0.0.0.0", port=8002)