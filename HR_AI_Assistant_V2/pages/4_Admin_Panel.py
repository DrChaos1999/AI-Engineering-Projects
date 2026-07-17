# ==========================================================
# File Name : 4_Admin_Panel.py
# Module    : Administration
#
# Purpose:
# Allow authorized administrators to manage HR policy documents used by the AI Assistant.
#
# Functions:
# • Upload HR policy PDF documents
# • View uploaded documents
# • Delete existing documents
# • Refresh the AI knowledge base automatically
# ==========================================================

import os
import streamlit as st


# ----------------------------------------------------------
# User Authentication
# Verify that the user is logged in before allowing access.
# ----------------------------------------------------------

if not st.session_state.get("logged_in", False):
    st.error("Please login first.")
    st.stop()

# ----------------------------------------------------------
# Administrator Authorization
# Only users with administrator privileges are allowed to access this page.
# ----------------------------------------------------------

if not st.session_state.get("is_admin", False):
    st.error("⛔ Access Denied")
    st.info("This page is available only for administrators.")
    st.stop()

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Admin Panel",
    page_icon="🔐",
    layout="wide"
)

st.title("🔐 Admin Panel")
st.write("Manage HR Policy documents for the AI Assistant.")
st.info("Administrator Access Only")

# ----------------------------------------------------------
# Upload HR Policy Documents
#
# Administrators can upload new HR policy PDF files.
# After upload, the knowledge base is automatically refreshed so the AI can answer using the latest documents.
# ----------------------------------------------------------

st.write("---")
st.subheader("📤 Upload HR Policy Documents")

uploaded_file = st.file_uploader(
    "Upload PDF",
    type="pdf"
)

if uploaded_file is not None:

    os.makedirs("data", exist_ok=True)

    file_path = os.path.join("data", uploaded_file.name)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Reload all documents
    st.session_state.all_text = read_all_pdfs("data")

    st.success("✅ File uploaded successfully.")

    st.rerun()

# ----------------------------------------------------------
# Uploaded Documents
# Display all available HR policy documents stored in the data folder.
# ----------------------------------------------------------

st.write("---")
st.subheader("📄 Uploaded Documents")

os.makedirs("data", exist_ok=True)

pdf_files = [
    file
    for file in os.listdir("data")
    if file.lower().endswith(".pdf")
]

if len(pdf_files) == 0:

    st.info("No HR policy documents found.")

else:

    st.success(f"Total Documents : {len(pdf_files)}")

    for file in pdf_files:

        col1, col2 = st.columns([6, 1])

        with col1:
            st.write(f"📄 {file}")

        with col2:

            if st.button("🗑️", key=file):

                # Delete the selected HR policy document.
                os.remove(os.path.join("data", file))

                # Reload all HR policy documents after upload or deletion.
                st.session_state.all_text = read_all_pdfs("data")

                st.success(f"{file} deleted successfully.")

                st.rerun()
