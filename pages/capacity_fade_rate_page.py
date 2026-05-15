import streamlit as st

from Processing.parameters import check_data_loaded, check_parameters
from Processing.plotting import display_figures_conditionally, generate_capacity_fade_rate_figures, generate_capacity_loss_per_cycle_figures
from Processing.calculations import calculate_capacity_fade_rate


st.set_page_config(page_title="Capacity Fade Rate Analysis")
st.title("Capacity Fade Rate Analysis")

st.write("This page analyzes the rate at which battery capacity fades over cycles, " \
"crucial for predicting long-term battery performance and lifespan. This is " \
"essentially capacity retention from a different perspective"
)

show_legend = st.toggle("Show Legend")

cap_fade_options = ["Cumulative Capacity Fade", "Capacity Loss per Cycle"]
selection = st.segmented_control("Capacity Fade Options", cap_fade_options, selection_mode="multi", help = "Choose all the different graphs you want plotting.")

capacity_fade = True if "Cumulative Capacity Fade" in selection else False
loss_per_cycle = True if "Capacity Loss per Cycle" in selection else False

# Warning message if no data in session state
check_data_loaded()
check_parameters()

if st.button("Generate Plots"):
    # This data is used for all. Seperated out for convenience
    fade_rate_data, compositions = calculate_capacity_fade_rate(st.session_state["data"], st.session_state["sample_parameters"])

    if capacity_fade: 
        fig_fade_rate, caption_fade_rate =generate_capacity_fade_rate_figures(fade_rate_data, compositions, show_legend)
        st.session_state["capacity_fade_rate_figures"] = [(fig_fade_rate, caption_fade_rate)]
    if loss_per_cycle:    
        fig_loss_per_cycle, caption_loss_per_cycle = generate_capacity_loss_per_cycle_figures(fade_rate_data, compositions, show_legend)
        st.session_state["capacity_loss_per_cycle_figures"] = [(fig_loss_per_cycle, caption_loss_per_cycle)]


if "capacity_fade_rate_figures" in st.session_state and capacity_fade:
    st.subheader("Cumulative capacity fade plot will be displayed .")
    display_figures_conditionally(st.session_state["capacity_fade_rate_figures"])
if "capacity_loss_per_cycle_figures" in st.session_state and loss_per_cycle:
    st.subheader("Capacity loss per cycle plot will be displayed.")
    display_figures_conditionally(st.session_state["capacity_loss_per_cycle_figures"])

