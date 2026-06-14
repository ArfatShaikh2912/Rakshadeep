import streamlit as st
from PIL import Image
import base64


# Page settings
st.set_page_config(page_title="RakshaDeep", layout="centered")


# Load and encode the logo image
logo_path = "assets/logo.png"
with open(logo_path, "rb") as img_file:
    b64_logo = base64.b64encode(img_file.read()).decode()


# Load other images
victim_img = Image.open("assets/victim.png")
intermediary_img = Image.open("assets/intermediary.png")
admin_img = Image.open("assets/admin.png")


# Header layout with updated colors and spacing
st.markdown(
    f"""
    <div style="display: flex; justify-content: space-between; align-items: flex-start; padding: 20px 0;">
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


# Helper function for clickable image with label
def get_clickable_image(image_path, target_page, label):
    with open(image_path, "rb") as img_file:
        b64_img = base64.b64encode(img_file.read()).decode()
    return f"""
        <div style="text-align:center;">
            <a href="/{target_page}" target="_self" style="text-decoration: none; outline: none; border: none;">
                <img src="data:image/png;base64,{b64_img}" style="width:100%; border-radius:10px;"/>
                <div style="margin-top: 8px; font-size:18px; font-weight:600; color:#333;">{label}</div>
            </a>
        </div>
    """


# Image Links Row
col_v, col_i, col_a = st.columns(3)


with col_v:
    st.markdown(get_clickable_image("assets/victim.png", "victim_mode", "Victim Mode"), unsafe_allow_html=True)


with col_i:
    st.markdown(get_clickable_image("assets/intermediary.png", "intermediary_mode", "Intermediary Mode"), unsafe_allow_html=True)


with col_a:
    st.markdown(get_clickable_image("assets/admin.png", "admin", "Admin Dashboard"), unsafe_allow_html=True)