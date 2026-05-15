import streamlit as st

from Processing.parameters import check_data_loaded, check_parameters
from Processing.calculations import calculate_power_density
from Processing.plotting import display_figures_conditionally, generate_energy_density_plot, generate_power_density_plot, generate_ragone_power_density_plot


st.set_page_config(page_title="Power Density Analysis")
st.title("Power and Energy Density Analysis")


show_legend = st.toggle("Show Legend")

power_analysis_options = ["Energy vs Cycle", "Power vs Cycle", "Ragone-like"]
selection = st.segmented_control("Power and Energy Density options", power_analysis_options, selection_mode="multi", help = "Choose all the different graphs you want plotting.")

energy_cycle = True if "Energy vs Cycle" in selection else False
power_cycle = True if "Power vs Cycle" in selection else False
ragone_plot = True if "Ragone-like" in selection else False

# energy_cycle = st.toggle("Plot Energy vs Cycle")
# power_cycle = st.toggle("Plot Power vs Cycle")
# ragone_plot = st.toggle("Ragone-like Plot")

# Warning message if no data in session state
check_data_loaded()
check_parameters()

if st.button("Generate Plots"):
    params = st.session_state["sample_parameters"]
    power_energy_data = calculate_power_density(st.session_state["data"], params)
    if energy_cycle:
        fig_energy_cycle, caption_energy_cycle = generate_energy_density_plot(power_energy_data, params, show_legend)
        st.session_state["Energy_Density_Plot"] = [(fig_energy_cycle, caption_energy_cycle)]
    
    if power_cycle:
        fig_power_cycle, caption_power_cycle = generate_power_density_plot(power_energy_data, params, show_legend)
        st.session_state["Power_Density_Plot"] = [(fig_power_cycle, caption_power_cycle)]

    if ragone_plot:
        fig_ragone, caption_ragone = generate_ragone_power_density_plot(power_energy_data, params, show_legend)
        st.session_state["Ragone_plot"] = [(fig_ragone, caption_ragone)]

if "Energy_Density_Plot" in st.session_state and energy_cycle:
    st.subheader("Energy Density Plot")
    display_figures_conditionally(st.session_state["Energy_Density_Plot"])

if "Power_Density_Plot" in st.session_state and power_cycle:
    st.subheader("Power Density Plot")
    display_figures_conditionally(st.session_state["Power_Density_Plot"])

if "Ragone_plot" in st.session_state and ragone_plot:
    st.subheader("Ragone-like Plot")
    display_figures_conditionally(st.session_state["Ragone_plot"])




