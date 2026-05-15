import streamlit as st

st.set_page_config(page_title="Home")

st.title("Battery Data Analysis App")
st.write("Upload your battery data in Excel format, and the app will process and display the results.")


if st.button("Go to Upload Page"):
    st.switch_page("pages/upload_data_page.py")