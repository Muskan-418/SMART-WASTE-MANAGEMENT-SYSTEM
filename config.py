# config.py
# Centralized configuration - edit values as required.

import os

# Database (SQLite file path)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("SWM_DB_PATH", os.path.join(BASE_DIR, "swm.db"))

# Sensor settings
BIN_HEIGHT_CM_DEFAULT = float(os.environ.get("BIN_HEIGHT_CM", "40"))

# Polling interval (seconds)
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "5"))

# Alert threshold percentage
ALERT_THRESHOLD = float(os.environ.get("ALERT_THRESHOLD", "80.0"))

# SSE queue max size (not strict)
EVENT_QUEUE_MAX = int(os.environ.get("EVENT_QUEUE_MAX", "1000"))

# MQTT (optional)
MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC_BASE = os.environ.get("MQTT_TOPIC_BASE", "smartwaste")

# Notification (placeholder) config
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "ops@example.com")
NOTIFY_SMS_NUMBER = os.environ.get("NOTIFY_SMS_NUMBER", "+911234567890")
