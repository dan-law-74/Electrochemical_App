import streamlit as st

from Processing.parameters import check_data_loaded, check_parameters
from Processing.plotting import display_figures_conditionally, generate_comparitive_profile, generate_comparitive_percent_profile


st.set_page_config(page_title="Half Cell Profile")
st.title("Charge Capacity Profile Analysis")

show_legend = st.toggle("Show Legend", value=True)


max_charge_cap_options = ["Absolute Values", "Percent Retention"]
selection = st.segmented_control("dQ/dV plot selections", max_charge_cap_options, selection_mode="multi", help = "Choose all the different graphs you want plotting.")

if "Percent Retention" in selection:
    col1, col2 = st.columns(2)
    with col1:
        remove_outliers = st.toggle("Remove Outliers", help = "Remove Outliers in % Retention plot")
    with col2: 
        if remove_outliers:
            outlier_percentage = st.number_input("Outlier Percentage Threshold", min_value=0, max_value=15, value=7, 
                                         help = "Set the percentage threshold for consecutive datapoints to be considered an outlier. Increase the value to be more lenient in filtering")

# Warning message if no data in session state
check_data_loaded()
check_parameters()

if st.button("Generate Plots"):

    if "Absolute Values" in selection:
        fig, caption = generate_comparitive_profile(st.session_state["data"], st.session_state["sample_parameters"], show_legend)
        st.session_state["comparitive_profiles"] = [(fig, caption)]
        
    if "Percent Retention" in selection:
        if remove_outliers:            
            fig, caption =  generate_comparitive_percent_profile(st.session_state["data"], st.session_state["sample_parameters"], show_legend, remove_outliers, outlier_percentage)
            st.session_state["outlier_info_msg"] = f"Outlier removal is enabled. Data points where the discharge capacity retention drops by more than {outlier_percentage}% compared to the previous cycle will be removed from the plot."

        else:
            fig, caption =  generate_comparitive_percent_profile(st.session_state["data"], st.session_state["sample_parameters"], show_legend, remove_outliers)
            st.session_state.pop("outlier_info_msg", None) # Clear info message if toggled off
        st.session_state["comparitive_pct_profiles"] = [(fig, caption)]


# This seperation allows both graphs to be viewed simultaneously if user changes toggles. 

if "comparitive_profiles" in st.session_state or "comparitive_pct_profiles" in st.session_state:
    st.subheader(f"Comparitive discharge capacity")

if "comparitive_profiles" in st.session_state and "Absolute Values" in selection:
    display_figures_conditionally(st.session_state["comparitive_profiles"])

if "comparitive_pct_profiles" in st.session_state and "Percent Retention" in selection:
    if "outlier_info_msg" in st.session_state:
        st.info(st.session_state["outlier_info_msg"])
    display_figures_conditionally(st.session_state["comparitive_pct_profiles"])

