import streamlit as st

st.title("Bulk PDF DSC Portal")

uploaded = st.file_uploader(
    "Upload PDF files",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded:
    st.success(f"{len(uploaded)} PDF uploaded successfully")
