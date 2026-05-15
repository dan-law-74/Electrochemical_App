import streamlit as st

from Processing.data_processing import figure_to_bytes
from Processing.parameters import check_data_loaded, check_parameters
from Processing.calculations import calculate_common_axis_scale
from Processing.plotting import generate_voltage_profile, display_figures_conditionally

st.set_page_config(page_title="Voltage Profile")
st.title("Voltage Profile Analysis")
st.write("This page will display voltage profiles for the selected key cycles. " \
            "You can customize the parameters for the voltage profile analysis in the " \
            "Graph Settings page. Make sure to save your parameters there before coming to this page.")
st.header("Additional Graph Settings")

show_legend = st.toggle("Show Legend", value=True, 
                          help="Toggle the display of the legend on the voltage profile graph.")
common_axis_scale = st.toggle("Common x-axis Scale", value=True, 
                          help="Toggle the use of a common scale for the x-axis across all voltage profile graphs.")


# Warning message if no data in session state
check_data_loaded()
check_parameters()

tab1, tab2 = st.tabs(["All Data", "Key Cycles Only"])

with tab1:
    if st.button("Generate Raw Plots"):
        figures_all = []
        for filename, df in st.session_state["data"].items():
            # st.subheader(f"Voltage Profile for {filename}")
            fig, caption = generate_voltage_profile(df, st.session_state["sample_parameters"][filename], show_legend, common_axis_scale, calculate_common_axis_scale(st.session_state["data"]), filename)
            figures_all.append((fig, caption))
        st.session_state["Voltage_Profile_Figures"] = figures_all

    # Display figures if they in session state
    if "Voltage_Profile_Figures" in st.session_state:  
        display_figures_conditionally(st.session_state["Voltage_Profile_Figures"])  

    # Add download buttons for each figure
    for filename, (fig, caption) in zip(st.session_state["data"].keys(), st.session_state.get("Voltage_Profile_Figures", [])):
        #Add download button for each figure. Add image file format variable for simpler code in this loop
        image_file_format = st.session_state["sample_parameters"][filename]["file_format"]
        buf = figure_to_bytes(fig, image_file_format)
        st.download_button(
            label=f"Download {filename}", 
            data=buf, 
            file_name=f"{filename.replace('.xlsx', '')}_voltage_profile.{image_file_format}",
            mime=f"image/{image_file_format.lower()}",
            key= f"download_{filename}"
            )

with tab2:
    if st.button("Generate Key Plots"):
        figures_key = []
        for filename, df in st.session_state["data"].items():
            # st.subheader(f"Voltage Profile for {filename}")
            fig, caption = generate_voltage_profile(df, st.session_state["sample_parameters"][filename], show_legend, common_axis_scale, calculate_common_axis_scale(st.session_state["data"]), filename, plot_key_cycles_only=True)
            figures_key.append((fig, caption))
        st.session_state["Voltage_Key_Profile_Figures"] = figures_key


    if "Voltage_Key_Profile_Figures" in st.session_state:  
        display_figures_conditionally(st.session_state["Voltage_Key_Profile_Figures"])  