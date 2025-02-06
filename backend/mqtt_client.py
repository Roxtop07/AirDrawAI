import cv2
import numpy as np
import paho.mqtt.client as mqtt
import json
from PIL import Image
import io

# MQTT Broker Configuration
BROKER = "mqtt.eclipseprojects.io"  # Use your MQTT broker
PORT = 1883
TOPIC_PUBLISH = "drawing/canvas"
TOPIC_SUBSCRIBE = "drawing/analysis"

# Initialize MQTT Client
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    """Callback when the client connects to the broker."""
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(TOPIC_SUBSCRIBE)

def on_message(client, userdata, msg):
    """Callback when a message is received."""
    print(f"Received message from AI: {msg.payload.decode()}")

client.on_connect = on_connect
client.on_message = on_message

# Connect to Broker
client.connect(BROKER, PORT, 60)
client.loop_start()


def publish_canvas(canvas):
    """Converts the canvas to a compressed image and sends it via MQTT."""
    _, img_encoded = cv2.imencode('.png', canvas)
    img_bytes = img_encoded.tobytes()
    client.publish(TOPIC_PUBLISH, img_bytes)
    print("Canvas sent via MQTT.")


def receive_analysis():
    """Waits for AI analysis message from MQTT."""
    client.subscribe(TOPIC_SUBSCRIBE)


if __name__ == "__main__":
    print("MQTT Client Running... Listening for AI responses.")
