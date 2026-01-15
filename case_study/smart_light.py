import tkinter as tk
from tkinter import ttk, messagebox
import paho.mqtt.client as mqtt
import os
import sys
from dotenv import load_dotenv

# Load environment variables from parent directory if not found in current
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
env_path = os.path.join(parent_dir, '.env')
load_dotenv(env_path)

# Configuration
BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", 1883))
TOPIC_SET = "home/livingroom/light/set"
TOPIC_STATUS = "home/livingroom/light/status"

class SmartLightApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Light Simulator")
        self.root.geometry("300x400")
        self.root.configure(bg="#333")

        self.is_on = False
        self.client = None
        
        self.create_widgets()
        self.connect_mqtt()

    def create_widgets(self):
        # Title
        ttk.Label(self.root, text="Living Room Light", font=("Arial", 16, "bold"), background="#333", foreground="white").pack(pady=20)

        # Light Bulb Indicator (Canvas)
        self.canvas = tk.Canvas(self.root, width=150, height=150, bg="#333", highlightthickness=0)
        self.canvas.pack(pady=10)
        
        # Draw Bulb (Circle)
        self.bulb = self.canvas.create_oval(25, 25, 125, 125, fill="#555", outline="white", width=2)
        
        # Status Label
        self.status_label = ttk.Label(self.root, text="OFF", font=("Arial", 14), background="#333", foreground="#aaa")
        self.status_label.pack(pady=10)

        # Connection Status
        self.conn_label = ttk.Label(self.root, text="Connecting...", font=("Arial", 9), background="#333", foreground="orange")
        self.conn_label.pack(side="bottom", pady=10)

    def update_light_visual(self):
        if self.is_on:
            self.canvas.itemconfig(self.bulb, fill="#FFD700", outline="#FFD700") # Gold/Yellow
            self.canvas.itemconfig(self.bulb, width=0)
            # Add glow effect (simple circles)
            self.status_label.config(text="ON", foreground="#FFD700")
        else:
            self.canvas.itemconfig(self.bulb, fill="#555", outline="white") # Dark Grey
            self.canvas.itemconfig(self.bulb, width=2)
            self.status_label.config(text="OFF", foreground="#aaa")

    def toggle_light(self, state):
        self.is_on = state
        self.update_light_visual()
        # Publish new status
        if self.client:
            payload = "ON" if self.is_on else "OFF"
            self.client.publish(TOPIC_STATUS, payload, retain=True)
            print(f"Published Status: {payload}")

    def connect_mqtt(self):
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            
            print(f"Connecting to {BROKER}:{PORT}...")
            self.client.connect(BROKER, PORT, 60)
            self.client.loop_start()
        except Exception as e:
            self.conn_label.config(text=f"Error: {e}", foreground="red")

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.conn_label.config(text="Connected to MQTT", foreground="#00FF00")
            client.subscribe(TOPIC_SET)
            print(f"Subscribed to {TOPIC_SET}")
            
            # Publish initial status
            self.toggle_light(self.is_on)
        else:
            self.conn_label.config(text=f"Failed to Connect: {reason_code}", foreground="red")

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        self.conn_label.config(text="Disconnected", foreground="red")

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode().upper()
        print(f"Received Command: {payload}")
        if payload == "ON":
            self.root.after(0, lambda: self.toggle_light(True))
        elif payload == "OFF":
            self.root.after(0, lambda: self.toggle_light(False))

if __name__ == "__main__":
    root = tk.Tk()
    app = SmartLightApp(root)
    root.mainloop()
