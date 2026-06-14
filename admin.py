import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import time
import base64
from geopy.geocoders import Nominatim
import mysql.connector
from mysql.connector import Error

# --- MYSQL CONNECTION SETUP ---
def get_mysql_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',      # Replace with your MySQL username
        password='root',  # Replace with your MySQL password
        database='rakshadeep_db'
    )

# --- PAGE SETUP ---
st.set_page_config(page_title="Admin Dashboard", layout="centered")

# --- LOAD AND ENCODE THE LOGO IMAGE ---
logo_path = "assets/logo.png"
with open(logo_path, "rb") as img_file:
    b64_logo = base64.b64encode(img_file.read()).decode()

# --- HEADER LAYOUT ---
st.markdown(
    f"""
    <style>
        .block-container {{
            padding-top: 1.5rem !important;
        }}
        .main > div {{
            padding-top: 1.5rem !important;
        }}
    </style>
    <div style="display: flex; justify-content: space-between; align-items: flex-start; padding: 10px 0 5px 0; margin-bottom: -10px;">
        <div style="flex: 2; text-align: left;">
            <h1 style="font-size: 40px; color: #2e294e; margin: 0;">RakshaDeep</h1>
            <h4 style="color: #f5cb5c; margin-top: 5px;">A beacon of safety for women in distress.</h4>
        </div>
        <div style="flex: 1; text-align: right; margin-top: 5px;">
            <img src="data:image/png;base64,{b64_logo}" width="160" style="margin-right: 10px;"/>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("---")

# --- LOGIN SECTION ---
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    st.subheader("🔐 Admin Login")
    username = st.text_input("Username:")
    password = st.text_input("Password:", type="password")

    if st.button("Login"):
        if username == "admin" and password == "Raksha123":
            st.session_state.admin_logged_in = True
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid credentials. Try again.")
    st.stop()

# --- FETCH ALERTS FROM MYSQL ---
@st.cache_data(ttl=30)
def fetch_alerts():
    try:
        connection = get_mysql_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM alerts ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        return rows
    except Error as e:
        st.error(f"MySQL Fetch Error: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

alerts = fetch_alerts()
if not alerts:
    st.info("No alerts available.")
    st.stop()

# --- FILTERS ---
codeword_display_options = ["All", "Emergency Help 🟥", "Legal Help 🟨", "Shelter/Emotional Help 🟩"]
codeword_filter = st.selectbox("🔍 Filter by Codeword", options=codeword_display_options)

codeword_filter_map = {
    "Emergency Help 🟥": "Emergency Help",
    "Legal Help 🟨": "Legal Help",
    "Shelter/Emotional Help 🟩": "Shelter/Emotional Help"
}

reporter_options = ["All", "Victim", "Intermediary"]
reporter_filter = st.selectbox("🎙 Filter by Reporter Mode", options=reporter_options)
reporter_filter_map = {
    "Victim": "victim",
    "Intermediary": "intermediary"
}

filtered_alerts = [
    a for a in alerts
    if (codeword_filter == "All" or a.get("help_type") == codeword_filter_map.get(codeword_filter))
    and (reporter_filter == "All" or a.get("reporterMode") == reporter_filter_map.get(reporter_filter))
]

# --- TABLE VIEW ---
st.markdown("### 📋 Alert Table")
columns_to_display = ["help_type", "address", "timestamp", "reporterMode", "note", "status"]
alerts_df = pd.DataFrame(filtered_alerts)[columns_to_display]
st.dataframe(alerts_df)

# --- MAP VIEW ---
st.markdown("### 🗺 Alert Map View")
m = folium.Map(location=[19.0760, 72.8777], zoom_start=11)
color_mapping = {
    "Emergency Help": "red",
    "Legal Help": "orange",
    "Shelter/Emotional Help": "green"
}
geolocator = Nominatim(user_agent="rakshadeep_geo")

for alert in filtered_alerts:
    lat = alert.get("latitude")
    lon = alert.get("longitude")
    help_type = alert.get("help_type", "Unknown") or "Unknown"
    pincode = alert.get("pincode", "")

    if not lat or not lon:
        # Use pincode to get location if lat/lon is not available
        location = geolocator.geocode(f"{pincode}, Mumbai")
        if location:
            lat, lon = location.latitude, location.longitude

    if lat and lon:
        folium.Marker(
            location=[lat, lon],
            popup=f"""
                <b>Codeword:</b> {alert.get("help_type")}<br>
                <b>Reporter:</b> {alert.get("reporterMode", "N/A")}<br>
                <b>Status:</b> {alert.get("status", "")}<br>
                <b>Time:</b> {alert.get("timestamp")}<br>
                <b>Note:</b> {alert.get("note", "")}<br>
                <b>Address:</b> {alert.get("address", "")}
            """,
            tooltip=f"{alert.get('help_type', 'Alert')} ({alert.get('reporterMode', '')})",
            icon=folium.Icon(color=color_mapping.get(help_type, "blue"), icon="exclamation-sign")
        ).add_to(m)

col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st_folium(m, width=700, height=350)

# --- UPDATE SECTION ---
st.markdown("### ✅ Update Alert Status")
def update_status(alert_id, new_status):
    try:
        connection = get_mysql_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE alerts SET status=%s WHERE id=%s", (new_status, alert_id))
        connection.commit()
        return True
    except Error as e:
        st.error(f"Failed to update status: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

if filtered_alerts:
    alert_options = [
        f"{a.get('timestamp', 'No Timestamp')} | {a.get('help_type', 'Unknown')} | {a.get('reporterMode', '')}"
        for a in filtered_alerts
    ]
    selected_alert_index = st.selectbox(
        "Choose an alert to update",
        options=range(len(filtered_alerts)),
        format_func=lambda x: alert_options[x]
    )

    selected_data = filtered_alerts[selected_alert_index]
    new_status = st.selectbox("Select new status", options=["Pending", "Acknowledged", "Resolved"])
    if st.button("Update Status"):
        if update_status(selected_data["id"], new_status):
            st.success("Status updated successfully.")
            st.rerun()
        else:
            st.error("Failed to update status.")
else:
    st.warning("No alerts available to update.")
