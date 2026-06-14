import firebase_admin
from firebase_admin import credentials, firestore
import uuid
import os
from datetime import datetime
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Initialize Firebase only once
if not firebase_admin._apps:
    try:
        cred_path = os.path.join("secrets", "firebase_credentials.json")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        logging.info("Firebase initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing Firebase: {e}")

# Initialize Firestore client
db = firestore.client()

def fetch_alerts():
    """
    Fetches all alerts from Firestore.

    Returns:
    - list: A list of alert dictionaries.
    """
    try:
        alerts_ref = db.collection("alerts")
        alerts = [doc.to_dict() for doc in alerts_ref.stream()]
        logging.info(f"Fetched {len(alerts)} alerts from Firestore.")
        return alerts
    except Exception as e:
        logging.error(f"Error fetching alerts: {e}")
        return []

def send_alert_to_admin(mode, help_type, user_location, notes=""):
    """
    Pushes a new alert to Firebase Firestore.

    Parameters:
    - mode: str, either "victim" or "intermediary"
    - help_type: str, the type of help needed ("Emergency Help", "Legal Help", "Shelter/Emotional Help")
    - user_location: tuple, (latitude, longitude)
    - notes: str, optional notes

    Returns:
    - bool: True if successful, False otherwise
    """
    try:
        # Ensure that the help_type values match the filter options in the admin dashboard
        alert_data = {
            "id": str(uuid.uuid4()),
            "reporterMode": mode,  # Changed key to match the admin dashboard
            "help_type": help_type,  # Changed key to match the admin dashboard
            "latitude": user_location[0],  # Changed key to match the admin dashboard
            "longitude": user_location[1],  # Changed key to match the admin dashboard
            "note": notes,  # Changed key to match the admin dashboard
            "timestamp": datetime.utcnow().isoformat(),
            "status": "New",  # Changed key to match the admin dashboard
        }

        # Add alert to Firestore
        db.collection("alerts").add(alert_data)
        logging.info("Alert sent to Firestore successfully.")
        return True

    except Exception as e:
        logging.error(f"Error sending alert: {e}")
        return False

