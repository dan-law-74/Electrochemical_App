import streamlit as st

from Processing.data_processing import process_data, load_data


st.set_page_config(page_title="Upload Data")
# Initialize session state for data storage
if "data" not in st.session_state:
    st.session_state["data"] = {}


#Upload files
uploaded_files = st.file_uploader("Choose an Excel file(s)", type=["xlsx", "xls"], accept_multiple_files=True) # allows multiple file uploads, returns a list of UploadedFile objects

if st.button("Upload and Process"):
    if not uploaded_files:
        st.warning("Please upload a file first.")
    else:
        with st.spinner("Processing..."):
            data_dict = load_data(uploaded_files)
            ## Load data returns a dictionary of dataframes, with filename as key and dataframe as value

            for filename in data_dict.keys():
                result = process_data(data_dict[filename],filename)                
                st.session_state["data"][filename] = result

        st.success("Done!")
#display initial results

for filename in st.session_state["data"].keys():
    st.subheader(f"Results for {filename}")
    st.write(st.session_state["data"][filename].describe()) # added describe() to display summary statistics instead of full dataframe

st.json(st.session_state)