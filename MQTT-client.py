import paho.mqtt.client as mqtt
import json

# Broker configuration
BROKER = "localhost"
PORT = 1883
CLIENT_ID = "client1"  # Unique client identifier

# Callback when a message is received
def on_message(client, userdata, message):
    print(f"Response from host: {message.payload.decode()}")

# Start the client
def start_client():
    client = mqtt.Client(CLIENT_ID)
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)

    # Subscribe to the client's "receive" topic
    client.subscribe(f"clients/{CLIENT_ID}/receive")

    # Example: Send a message to the host
    message = {"action": "get_logs", "details": "Requesting my logs"}
    client.publish(f"clients/{CLIENT_ID}/send", json.dumps(message))

    print(f"Message sent to host: {message}")
    client.loop_forever()

start_client()
