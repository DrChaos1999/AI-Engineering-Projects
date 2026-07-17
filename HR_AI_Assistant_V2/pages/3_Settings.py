# ==========================================================
# File Name : 3_Settings.py
# Module    : Settings
#
# Purpose:
# Allow users to customize their AI Assistant preferences.
# These settings improve the user experience without affecting
# the organization's HR policy documents.
# ==========================================================

import streamlit as st

# ----------------------------------------------------------
# Configure Settings Page
# ----------------------------------------------------------
st.set_page_config(
    page_title="Settings",
    page_icon="⚙️",
    layout="wide"
)

# ----------------------------------------------------------
# Page Header
# ----------------------------------------------------------
st.title("⚙️ AI Assistant Settings")

st.markdown("""
Configure your personal preferences for the Trimco Bangladesh AI Workplace Assistant.
""")

st.divider()

# ----------------------------------------------------------
# Language Settings
# ----------------------------------------------------------
st.subheader("🌐 Language")

language = st.selectbox(
    "Select your preferred language",
    ["English", "বাংলা"]
)

# ----------------------------------------------------------
# AI Response Settings
# ----------------------------------------------------------
st.subheader("🤖 AI Response")

response_length = st.selectbox(
    "Preferred Response Length",
    ["Short", "Medium", "Detailed"]
)

# ----------------------------------------------------------
# Display Settings
# ----------------------------------------------------------
st.subheader("🖥️ Display")

show_sources = st.checkbox(
    "Show Source Documents",
    value=True
)

# Future Feature
dark_mode = st.checkbox(
    "Enable Dark Mode (Coming Soon)",
    value=False,
    disabled=True
)

st.divider()

# ----------------------------------------------------------
# Notification Settings
# ----------------------------------------------------------
st.subheader("🔔 Notifications")

email_notification = st.checkbox(
    "Receive HR Policy Update Notifications",
    value=True
)

st.divider()

# ----------------------------------------------------------
# Save Settings
# ----------------------------------------------------------
if st.button("💾 Save Settings", use_container_width=True):

    st.success("✅ Your settings have been saved successfully.")
