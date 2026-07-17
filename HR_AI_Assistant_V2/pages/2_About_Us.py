# ==========================================================
# File Name : 2_About_Us.py
# Module    : About Us
#
# Purpose:
# Display information about the Trimco Bangladesh AI Workplace Assistant, its objectives, key features,
# and the organization it supports.
# ==========================================================

import streamlit as st

# ----------------------------------------------------------
# Configure About Us Page
# ----------------------------------------------------------
st.set_page_config(
    page_title="About Us",
    page_icon="ℹ️",
    layout="wide"
)

# ----------------------------------------------------------
# Page Header
# ----------------------------------------------------------
st.title("ℹ️ About Us")

st.markdown("""
## Trimco Bangladesh AI Workplace Assistant

The **Trimco Bangladesh AI Workplace Assistant** is an intelligent workplace solution developed to provide employees with quick and accurate access to Human Resources (HR) information.

The system uses Artificial Intelligence (AI) to understand employee questions and generate answers based on the organization's official HR policy documents.

Our objective is to improve employee experience by reducing response time, increasing information accessibility, and supporting the digital transformation of HR services.
""")

st.divider()

# ----------------------------------------------------------
# Mission
# ----------------------------------------------------------
st.subheader("🎯 Our Mission")

st.write("""
To simplify HR communication by providing employees with an intelligent, secure, and easy-to-use AI assistant that delivers reliable information from official company policies.
""")

st.divider()

# ----------------------------------------------------------
# Key Features
# ----------------------------------------------------------
st.subheader("🚀 Key Features")

st.markdown("""
- 🤖 AI-powered HR question answering
- 📄 HR policy document search
- ⏱️ Instant responses
- 🔒 Secure employee access
- 📚 Knowledge-based assistance
- 💼 Supports digital HR transformation
""")

st.divider()

# ----------------------------------------------------------
# Technologies Used
# ----------------------------------------------------------
st.subheader("💻 Technologies Used")

st.markdown("""
- **Python**
- **Streamlit**
- **OpenAI**
- **SQLite Database**
- **PDFPlumber**
""")

st.divider()

# ----------------------------------------------------------
# Organization
# ----------------------------------------------------------
st.subheader("🏢 Organization")

st.write("""
**Trimco Bangladesh**

This application has been developed to support employees by providing quick access to HR policies and workplace information through Artificial Intelligence.
""")

st.divider()

# ----------------------------------------------------------
# Version Information
# ----------------------------------------------------------
st.subheader("📌 Application Information")

st.write("**Version:** 2.0")
st.write("**Deployment:** Internal Office Network")
st.write("**Environment:** Production / Pilot")
