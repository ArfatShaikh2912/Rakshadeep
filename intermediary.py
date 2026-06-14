import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import mysql.connector
from mysql.connector import Error
import base64

from utils.geolocation_utils import get_user_location
from utils.ngo_utils import filter_ngos_by_services

# --- MYSQL CONNECTION ---
def get_mysql_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",      # <--- Replace with your MySQL username
        password="root*",  # <--- Replace with your MySQL password
        database="rakshadeep_db"
    )

# --- PAGE SETUP ---
st.set_page_config(page_title="Intermediary Mode", layout="centered")

# --- LOGO HEADER ---
logo_path = "assets/logo.png"
with open(logo_path, "rb") as img_file:
    b64_logo = base64.b64encode(img_file.read()).decode()

st.markdown(f"""
    <style>
        .block-container {{ padding-top: 1.5rem !important; }}
        .main > div {{ padding-top: 1.5rem !important; }}
    </style>
    <div style="display: flex; justify-content: space-between; align-items: flex-start; padding: 10px 0 5px 0; margin-bottom: -10px;">
        <div style="flex: 2; text-align: left;">
            <h1 style="font-size: 40px; color: #2e294e; margin: 0;">RakshaDeep</h1>
            <h4 style="color: #f5cb5c; margin-top: 5px;">A beacon of safety for women in distress.</h4>
        </div>
        <div style="flex: 1; text-align: right; margin-top: 5px;">
            <img src="data:image/png;base64,{b64_logo}" width="160" />
        </div>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# --- SESSION STATE SETUP ---
for key, default in [
    ('authenticated', False),
    ('marker_position', None),
    ('confirmed_location', None),
    ('selected_help_type', None),
    ('location_confirmed', False)
]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- PASSPHRASE LOGIN ---
if not st.session_state.authenticated:
    st.markdown("### 🔒 Intermediary Access Required")
    passphrase = st.text_input("Enter Passphrase", type="password")
    if st.button("Submit"):
        if passphrase == "RakshaAccess@2025":
            st.session_state.authenticated = True
            st.success("Access granted.")
            st.rerun()
        else:
            st.warning("❌ Invalid passphrase. Try again.")
    st.stop()

# --- CODEWORD SELECTION ---
codeword_options = {
    "Emergency Help 🟥": "Emergency Help",
    "Legal Help 🟨": "Legal Help",
    "Shelter/Emotional Help 🟩": "Shelter/Emotional Help"
}
st.markdown("### 🔍 Assistance Needed:")
selected_label = st.selectbox("Select help type", list(codeword_options.keys()))
help_type = codeword_options[selected_label]
st.session_state.selected_help_type = help_type

# --- ADDRESS INPUT ---
geolocator = Nominatim(user_agent="rakshadeep_geo")
st.markdown("### 📍 Enter Victim's Address and Pincode:")
user_address = st.text_input("Address (building, area, etc.):")
user_pincode = st.text_input("Pincode", max_chars=6)

if not user_address or not user_pincode:
    st.warning("Please enter both address and pincode to proceed.")
    st.stop()

full_address = f"{user_address}, {user_pincode}, Mumbai"
adjusted_location = None

try:
    location = geolocator.geocode(full_address, timeout=15)
    if location:
        adjusted_location = (location.latitude, location.longitude)
    else:
        fallback = geolocator.geocode(f"{user_pincode}, Mumbai", timeout=15)
        if fallback:
            adjusted_location = (fallback.latitude, fallback.longitude)
        else:
            st.error("Could not find location via pincode.")
            st.stop()
    st.session_state.marker_position = adjusted_location
except Exception as e:
    st.error("Could not connect to geolocation service.")
    st.exception(e)
    st.stop()

# --- OPTIONAL NOTE ---
st.markdown("### 📝 Optional Note")
note = st.text_area("Details (e.g., 'Victim is locked up')", max_chars=300)

# --- CONFIRM LOCATION ---
if adjusted_location:
    lat_input = st.number_input("Latitude", value=adjusted_location[0], format="%.6f")
    lon_input = st.number_input("Longitude", value=adjusted_location[1], format="%.6f")
    if st.button("Confirm Location"):
        st.session_state.confirmed_location = (lat_input, lon_input)
        st.session_state.location_confirmed = True
        st.success("📍 Location confirmed.")

# --- SHOW NGOs + MAP ---
if st.session_state.location_confirmed:
    st.markdown("### 🗺 Your Location + Nearest Support Centers")
    user_location = st.session_state.confirmed_location
    ngo_data = pd.read_csv(r"C:\Users\SHAIKH ARFAT\OneDrive\Desktop\Rakshadeep Revised\RakshaDeep\data\ngo_database.csv")
    selected_help = st.session_state.selected_help_type
    filtered_ngos, _ = filter_ngos_by_services(ngo_data, selected_help)

    if not filtered_ngos.empty:
        filtered_ngos["distance_km"] = filtered_ngos.apply(
            lambda row: geodesic(user_location, (row["Latitude"], row["Longitude"])).km, axis=1
        )
        nearby_ngos = filtered_ngos[filtered_ngos["distance_km"] <= 5]
        st.write(f"🔍 Found {len(nearby_ngos)} support centers within 5 km.")
        st.dataframe(nearby_ngos[["Support Center Name", "Services Offered", "distance_km"]])

        m = folium.Map(location=user_location, zoom_start=13)
        folium.Marker(
            location=user_location,
            tooltip="Intermediary Location",
            icon=folium.Icon(color="red", icon="glyphicon glyphicon-user")
        ).add_to(m)

        for _, row in nearby_ngos.iterrows():
            folium.Marker(
                location=(row["Latitude"], row["Longitude"]),
                popup=f"<b>{row['Support Center Name']}</b><br>{row['Services Offered']}<br>📞 {row['Phone No']}<br>📧 {row.get('Email', 'N/A')}",
                tooltip=f"{row['Support Center Name']}",
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)

        _, col, _ = st.columns([1, 3, 1])
        with col:
            st_folium(m, width=700, height=350)

        st.markdown("### 📋 Support Details")
        for _, row in nearby_ngos.iterrows():
            st.subheader(row['Support Center Name'])
            st.write(f"📍 {row['Address']}")
            st.write(f"🛠 Services: {row['Services Offered']}")
            st.write(f"📞 {row['Phone No']}")
            if pd.notna(row.get("Email")):
                st.write(f"📧 {row['Email']}")
            st.markdown("---")
    else:
        st.info("No NGOs found within 5 km.")

    # --- SUBMIT ALERT TO MYSQL ---
    st.markdown("### 🚨 Submit Alert to RakshaDeep Team")
    if st.button("🚨 Alert for Help"):
        alert_data = {
            "reporterMode": "intermediary",
            "help_type": help_type,
            "note": note,
            "latitude": user_location[0],
            "longitude": user_location[1],
            "address": user_address,
            "pincode": user_pincode,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            connection = get_mysql_connection()
            cursor = connection.cursor()
            insert_query = """
                INSERT INTO alerts
                (reporterMode, help_type, note, latitude, longitude, address, pincode, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                alert_data['reporterMode'],
                alert_data['help_type'],
                alert_data['note'],
                alert_data['latitude'],
                alert_data['longitude'],
                alert_data['address'],
                alert_data['pincode'],
                alert_data['timestamp']
            ))
            connection.commit()
            st.success("✅ Alert submitted successfully.")
        except Error as e:
            st.error("❌ Failed to submit alert.")
            st.exception(e)
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
