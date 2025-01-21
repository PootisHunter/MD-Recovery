import paho.mqtt.client as mqtt
import json

# Broker configuration
BROKER = "localhost"
PORT = 1883

# Callback for when a message is received
def on_message(client, userdata, message):
    try:
        # Parse the incoming message
        client_id = message.topic.split('/')[1]  # Extract client ID from topic
        payload = json.loads(message.payload.decode())

        # *Response handling here*

        # Send response to the client's "receive" topic
        response_topic = f"clients/{client_id}/receive"
        client.publish(response_topic, json.dumps(response))
        #print(f"Sent response to {response_topic}")

    except Exception as e:
        print(f"Error processing message: {e}")

def start_host():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)

    # Subscribe to all client send topics
    client.subscribe("clients/+/send")

    print("Host is running and listening...")
    client.loop_forever()

start_host()