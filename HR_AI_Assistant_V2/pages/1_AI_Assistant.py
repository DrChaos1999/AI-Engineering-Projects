# ==========================================================
# File Name : 1_AI_Assistant.py
# Module    : Dashboard
#
# Purpose:
# Display the main dashboard page after the user logs in.
# This page serves as the landing page of the
# Trimco Bangladesh AI Workplace Assistant.
# ==========================================================

import streamlit as st
from datetime import datetime
import os

# ----------------------------------------------------------
# Configure the Dashboard Page
# ----------------------------------------------------------
st.set_page_config(
    page_title="Dashboard",
    page_icon="🏠",
    layout="wide"
)

# ----------------------------------------------------------
# Dashboard Header
# ----------------------------------------------------------
st.title("🏠 Dashboard")

st.markdown("""
## Welcome to Trimco Bangladesh AI Workplace Assistant

The **Trimco Bangladesh AI Workplace Assistant** is an AI-powered platform designed to help employees quickly access HR policies, company guidelines, and workplace information.

Our goal is to provide **fast, accurate, and intelligent HR support**, enabling employees to receive instant answers to HR-related questions.
""")

st.divider()

# ----------------------------------------------------------
# User Information
# ----------------------------------------------------------

st.subheader("👤 User Information")

# Get current date and time
now = datetime.now()

# Get logged-in user information
username = st.session_state.get("username", "Guest")
role = "Administrator" if st.session_state.get("is_admin", False) else "Employee"

col1, col2 = st.columns(2)

with col1:
    st.write(f"**👤 Logged-in User:** {username}")
    st.write(f"**🔑 Role:** {role}")

with col2:
    st.write(f"**📅 Today:** {now.strftime('%A, %d %B %Y')}")
    st.write(f"**🕒 Current Time:** {now.strftime('%I:%M %p')}")

st.divider()


# ----------------------------------------------------------
# Count HR Policy Documents
# ----------------------------------------------------------

pdf_count = len(
    [file for file in os.listdir("data") if file.endswith(".pdf")]
)

# ----------------------------------------------------------
# System Overview
# ----------------------------------------------------------

st.subheader("📊 System Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📄 HR Policies",
        value=pdf_count
    )

with col2:
    st.metric(
        label="🤖 AI Status",
        value="🟢 Online"
    )

with col3:
    st.metric(
        label="💬 Today's Queries",
        value="0"
    )

with col4:
    st.metric(
        label="👥 Users",
        value="20"
    )

st.divider()


st.divider()
