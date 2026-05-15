import streamlit as st

from Processing.parameters import check_data_loaded, check_parameters
from Processing.calculations import calculate_common_y_axis
from Processing.plotting import display_figures_conditionally, generate_half_cell_profile



st.set_page_config(page_title="Half Cell Profile")
st.title("Half Cell Profile Analysis")

show_legend = st.toggle("Show Legend", value=True)
half_cell_options = ["Common y-axis Capacity Scale", "Common y-axis Efficiency Scale"]
selection = st.segmented_control("Select Common y axis options", half_cell_options, selection_mode="multi", help = "Choose the common y-axis that are required for plotting.")

common_y_axis_capacity = True if "Common y-axis Capacity Scale" in selection else False
common_y_axis_efficiency = True if "Common y-axis Efficiency Scale" in selection else False

if common_y_axis_capacity or common_y_axis_efficiency: common_y_axis = True 
else: common_y_axis = False

global_max_capacity_val = 0
global_max_efficiency_val = 0
try:
    if common_y_axis:
        global_max_capacity_val, global_max_efficiency_val = calculate_common_y_axis(
            st.session_state["data"], 
            st.session_state["sample_parameters"]
            )
        
        st.info(f"The common y-axis scale for capacity will be set to a maximum of {global_max_capacity_val:.2f} mAh/g based on the maximum capacity across all datasets. Max eficiency of {global_max_efficiency_val: .2f}%")
except KeyError:
    st.warning("Unable to calculate common y-axis scale because sample parameters are not set for all files. Please go to the Graph Settings page and set parameters for all files before enabling common y-axis scale.")

# colours = {"Charge": st.color_picker("Select colour for Charge", value="#1f77b4"),
#            "Discharge": st.color_picker("Select colour for Discharge", value="#ff7f0e"),
#            "Efficiency": st.color_picker("Select colour for Efficiency", value="#000000")}

default_colours ={"Charge": "#1f77b4", "Discharge": "#ff7f0e", "Efficiency":"#000000"}
# Colour Picking
def reset_colours():
    st.session_state['half_cell_charge_colour'] = default_colours["Charge"]
    st.session_state['half_cell_dischrage_colour'] = default_colours["Discharge"]
    st.session_state['half_cell_efficiency_colour'] = default_colours["Efficiency"]

col1, col2, col3, col4 = st.columns(4)
colours = {}
with col1: 
    charge_colour = st.color_picker("Charge Colour", value=default_colours["Charge"], key = 'half_cell_charge_colour')
    colours['Charge'] = charge_colour
with col2:
    discharge_colour = st.color_picker("Discharge Colour", value=default_colours["Discharge"], key = 'half_cell_dischrage_colour')
    colours['Discharge'] = discharge_colour
with col3:
    efficiency_colour = st.color_picker("Efficiency Colour", value = default_colours["Efficiency"], key='half_cell_efficiency_colour' )
    colours['Efficiency'] = efficiency_colour
with col4: 
    st.button("Rest to default", on_click=reset_colours)



check_data_loaded()
check_parameters()

if st.button("Generate Plots"):
    figures = []
    for filename, df in st.session_state["data"].items():
        fig, caption = generate_half_cell_profile(df, st.session_state["sample_parameters"][filename], show_legend, common_y_axis_capacity, global_max_capacity_val, common_y_axis_efficiency, global_max_efficiency_val, colours, filename)
        figures.append((fig, caption))
    st.session_state["Half_Cell_Profile_Figures"] = figures

if "Half_Cell_Profile_Figures" in st.session_state:
    st.subheader(f"Half Cell Profiles")
    display_figures_conditionally(st.session_state["Half_Cell_Profile_Figures"])
