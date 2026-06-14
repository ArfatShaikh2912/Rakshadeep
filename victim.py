import streamlit as st
from PIL import Image
import pandas as pd
import folium
from streamlit_folium import st_folium
import base64
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from datetime import datetime
import mysql.connector
from mysql.connector import Error

from utils.geolocation_utils import get_user_location
from utils.ngo_utils import load_ngo_data, filter_ngos_by_services

# --- MYSQL SETUP ---
def get_mysql_connection():
    return mysql.connector.connect(
        host="localhost",           # Change as needed
        user="root", # Update with your MySQL username
        password="root*", # Update with your MySQL password
        database="rakshadeep_db"
    )

# --- PAGE SETUP ---
st.set_page_config(page_title="Victim Mode", layout="centered")

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

# --- CODEWORD DROPDOWN ---
codeword_options = {
    "Emergency Help 🟥": "Emergency Help",
    "Legal Help 🟨": "Legal Help",
    "Shelter/Emotional Help 🟩": "Shelter/Emotional Help"
}

st.markdown("### 🔍 Choose the Type of Assistance You Need:")
selected_label = st.selectbox("Select an option", list(codeword_options.keys()))
help_type = codeword_options[selected_label]

# --- GET APPROX LOCATION ---
st.markdown("### 📍 Detecting Your Location...")
location = get_user_location()

if location != (None, None):
    st.success(f"Approximate location detected! Latitude: {location[0]:.4f}, Longitude: {location[1]:.4f}")
    adjusted_location = location
else:
    st.error("Unable to detect location. Please check browser permissions or internet.")
    adjusted_location = None

# --- ADDRESS INPUT ---
geolocator = Nominatim(user_agent="rakshadeep_geo")

st.markdown("### 🏠 Enter Your Address and Pincode:")
user_address = st.text_input("Address (including flat/building number, area, etc.):")
user_pincode = st.text_input("Pincode (Required):", max_chars=6)

# Check if address and pincode are provided
if not user_address or not user_pincode:
    st.warning("Please enter both address and pincode to proceed.")
    st.stop()

if user_address and user_pincode:
    full_address = f"{user_address}, {user_pincode}, Mumbai"
    try:
        location = geolocator.geocode(full_address, timeout=10)
        if location:
            new_location = (location.latitude, location.longitude)
            st.session_state.marker_position = new_location
            adjusted_location = new_location
        else:
            st.warning("Could not detect exact address. Trying pincode...")
            pincode_location = geolocator.geocode(f"{user_pincode}, Mumbai")
            if pincode_location:
                fallback_location = (pincode_location.latitude, pincode_location.longitude)
                st.session_state.marker_position = fallback_location
                adjusted_location = fallback_location
            else:
                st.error("Unable to find location. Please adjust marker manually.")
    except Exception as e:
        st.error("Error occurred while fetching location.")
        st.exception(e)

# --- LOCATION CONFIRMATION ---
if adjusted_location:
    if 'marker_position' not in st.session_state:
        st.session_state.marker_position = adjusted_location

    lat_input = st.number_input("Latitude", value=st.session_state.marker_position[0], format="%.6f")
    lon_input = st.number_input("Longitude", value=st.session_state.marker_position[1], format="%.6f")

    if st.button("Confirm Location"):
        st.session_state.confirmed_location = (lat_input, lon_input)
        st.session_state.selected_help_type = help_type
        st.session_state.location_confirmed = True
        st.success(f"📍 Location confirmed: Latitude {lat_input:.4f}, Longitude {lon_input:.4f}")

        if geodesic(st.session_state.confirmed_location, adjusted_location).km > 1:
            st.warning("Marker and address seem far apart. Please verify the location.")

# --- SHOW MAP & NEARBY NGOs ---
if st.session_state.get("location_confirmed"):
    st.markdown("### 🗺 Map: Your Location + Nearby Support Centers")

    ngo_data = pd.read_csv(r"C:\Users\SHAIKH ARFAT\OneDrive\Desktop\Rakshadeep Revised\RakshaDeep\data\ngo_database.csv")
    user_location = st.session_state.confirmed_location
    selected_help = st.session_state.selected_help_type

    filtered_ngos, _ = filter_ngos_by_services(ngo_data, selected_help)

    if not filtered_ngos.empty:
        filtered_ngos["distance_km"] = filtered_ngos.apply(
            lambda row: geodesic(user_location, (row["Latitude"], row["Longitude"])).km,
            axis=1
        )
        nearby_ngos = filtered_ngos[filtered_ngos["distance_km"] <= 5]
        st.write(f"🔎 Found {nearby_ngos.shape[0]} support center(s) within 5 km.")
        st.dataframe(nearby_ngos[["Support Center Name", "Services Offered", "distance_km"]])

        m = folium.Map(location=user_location, zoom_start=13)

        folium.Marker(
            location=user_location,
            tooltip="You are here",
            icon=folium.Icon(color="red", icon="glyphicon glyphicon-user")
        ).add_to(m)

        for _, row in nearby_ngos.iterrows():
            folium.Marker(
                location=(row["Latitude"], row["Longitude"]),
                popup=f"<b>{row['Support Center Name']}</b><br>{', '.join(row['Services Offered'].split(','))}<br>📞 {row['Phone No']}<br>📧 {row.get('Email', 'N/A')}",
                tooltip=f"{row['Support Center Name']} - {', '.join(row['Services Offered'].split(','))}",
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(m)

        col1, col2, col3 = st.columns([1, 3, 1])

        with col2:
            st_folium(m, width=700, height=325)

        st.markdown("### 📋 NGO Details")
        for _, row in nearby_ngos.iterrows():
            st.markdown(f"{row['Support Center Name']} – {', '.join(row['Services Offered'].split(','))}")
            st.write(f"📍 {row['Address']}")
            st.write(f"📞 {row['Phone No']}")
            if pd.notna(row.get('Email')):
                st.write(f"📧 {row['Email']}")
            st.markdown("---")
    else:
        st.info("No nearby support centers found within 5 km for your selected assistance type.")

    # --- ALERT BUTTON ---
    st.markdown("## ⚠ Optional Alert: Notify Admin")
    st.write("In danger or need help? Tap below to alert the RakshaDeep team with your location.")
    alert_note = st.text_area("📝 Optional Note (e.g., 'Can’t call right now. I’m in danger.')", max_chars=300)

    if st.button("🚨 Alert RakshaDeep for Help"):
        alert_data = {
            "reporterMode": "victim",
            "help_type": help_type,
            "note": alert_note,
            "latitude": st.session_state.confirmed_location[0],
            "longitude": st.session_state.confirmed_location[1],
            "address": user_address,
            "pincode": user_pincode,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        try:
            connection = get_mysql_connection()
            cursor = connection.cursor()
            insert_query = (
                "INSERT INTO alerts "
                "(reporterMode, help_type, note, latitude, longitude, address, pincode, timestamp) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            )
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
            st.success("✅ Your alert has been sent to the RakshaDeep admin team.")
        except Error as e:
            st.error(f"Failed to log alert: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()
