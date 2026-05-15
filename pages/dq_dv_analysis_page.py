import streamlit as st

from Processing.parameters import check_data_loaded, check_parameters
# from Processing.calculations import 
from Processing.plotting import display_figures_conditionally, generate_full_dq_dv_plot, generate_dq_dv_key_cycles_plot, generate_dq_dv_smoothed


st.set_page_config(page_title="dQ/dV Analysis")
st.title("dQ/dV Analysis")


# st.sidebar.markdown("---")
# st.sidebar.subheader("dQ/dV Settings")
# apply_smoothing = st.sidebar.checkbox("Enable Smoothing")

# if apply_smoothing:
#     st.subheader("TESTING")

def reset_raw_colours():
    st.session_state['dqdv_charge_colour'] = default_dqdv_charge_colour
    st.session_state['dqdv_dischrage_colour'] = default_dqdv_discharge_colour


def reset_smooth_colours():
    st.session_state['dqdv_smooth_charge_colour'] = default_dqdv_smooth_charge_colour
    st.session_state['dqdv_smooth_discharge_colour'] = default_dqdv_smooth_discharge_colour    

default_dqdv_charge_colour = '#1f77b4'
default_dqdv_discharge_colour = '#ff7f0e'
default_dqdv_smooth_charge_colour = '#228B22'
default_dqdv_smooth_discharge_colour = '#B22222'


tab1, tab2 = st.tabs(["📉 Raw dQ/dV", "✨ Smoothed dQ/dV"])

# Warning message if no data in session state
check_data_loaded()
check_parameters()


with tab1:
    st.subheader("Raw Data Plots")
    show_legend_raw = st.toggle("Show Legend", key = "dqdv_show_legend_raw")

    dq_dv_options = ["Full Data", "Key Cycles Only"]
    selection = st.segmented_control("dQ/dV plot selections", dq_dv_options, selection_mode="multi", help = "Choose all the different graphs you want plotting. Key cycles only gives easier viewing")

    # Colour Picking

    with st.expander("⚙️ Colour Options", expanded=False):
        col1, col2, col3 = st.columns(3)
        colours = {}
        with col1: 
            charge_colour = st.color_picker("Select colour for Charge", value=default_dqdv_charge_colour, key = 'dqdv_charge_colour')
            colours['Charge_Colour'] = charge_colour
        with col2:
            discharge_colour = st.color_picker("Select colour for Disharge", value=default_dqdv_discharge_colour, key = 'dqdv_dischrage_colour')
            colours['Discharge_Colour'] = discharge_colour
        with col3: 
            st.write("")
            st.button("Default Colours(Raw)", on_click=reset_raw_colours)

    if st.button("Generate Raw Plots"):

        # key_figures = []

        if "Full Data" in selection:
            full_figures = []
            for filename, df in st.session_state["data"].items():
                fig, caption = generate_full_dq_dv_plot(df, st.session_state["sample_parameters"][filename], colours, filename, show_legend_raw)
                full_figures.append((fig, caption))
            st.session_state["dQ_dV_full_range"] = full_figures
        
        if "Key Cycles Only" in selection:
            st.session_state["dQ_dV_key_range"] = {}
            for filename, df in st.session_state["data"].items():
                key_fig_captions = generate_dq_dv_key_cycles_plot(df, st.session_state["sample_parameters"][filename], colours, filename, show_legend_raw)
                st.session_state["dQ_dV_key_range"][filename] = key_fig_captions # Setting up in a dictionary instead

    # Display figures if they in session state
    if "dQ_dV_full_range" in st.session_state and "Full Data" in selection:
        st.subheader("Full Range Plots")  
        display_figures_conditionally(st.session_state["dQ_dV_full_range"]) 

    if "dQ_dV_key_range" in st.session_state and "Key Cycles Only" in selection:
        for filename, figures_list in st.session_state["dQ_dV_key_range"].items():
            st.subheader(f"Key Cycle Graphs for {filename}")
            display_figures_conditionally(figures_list) 

# Setting up settings ui menu for dQ/dV smoothing
@st.fragment
def smoothing_ui_fragment():
    with st.expander("⚙️ Smoothing Parameters", expanded=True):
        spike_removal = st.toggle("Remove Spikes")
        col1, col2 = st.columns(2)
        with col1:
            smoothing_window = st.slider("Window Size (Must be odd)", min_value=5, max_value=51, value=15, step=2, help = "Number of datapoints used in the filter. Larger values will result in more aggressive smoothing (Default 15)")
        with col2:
            polyorder = st.slider("Polynomial Order", min_value=1, max_value=5, value=2, help = "Interger parameter specifies order of polynomial used to fit data. Lower values (2,3) recommended to avoid overfitting")
        
        if spike_removal:
            with col1:
                spike_window = st.slider("Spike Window size", min_value=1, max_value=10, value = 3, step = 2,  help = "Odd integer parameter that determines the window size for rolling average used for spike removal")
            with col2:
                spike_threshold = st.number_input("Spike Removal Threshold (Std Dev)", value=2.0, help = "Determines the sensitivity of spike removal. Data point considered a spike if deviation from rolling average is greater than this multiplied by rolling standard deviation. Larger values (4,5) will make spike detention less sensitive.")
        
        cola, colb, colc = st.columns(3)
        smoothed_colours = {}
        with cola:
            charge_colour = st.color_picker("Select colour for Charge", value=default_dqdv_smooth_charge_colour, key = 'dqdv_smooth_charge_colour')
            smoothed_colours['Charge_Colour'] = charge_colour
        with colb:
            discharge_colour = st.color_picker("Select colour for Disharge", value=default_dqdv_smooth_discharge_colour, key = 'dqdv_smooth_dischrage_colour')
            smoothed_colours['Discharge_Colour'] = discharge_colour
        with colc: 
            st.write("")
            st.button("Default Colours(Smooth)",on_click=reset_smooth_colours )
        if st.button("Update Smoothing Parameters"):
            if "sample_parameters" in st.session_state:
                st.session_state["sample_parameters"]["shared"]["smoothing_window"] = smoothing_window
                st.session_state["sample_parameters"]["shared"]["polyorder"] = polyorder
                st.session_state["sample_parameters"]["shared"]["spike_removal"] = spike_removal
                st.session_state["sample_parameters"]["shared"]["spike_window_size"] = spike_window if spike_removal else None
                st.session_state["sample_parameters"]["shared"]["spike_threshold_multiplier"] = spike_threshold if spike_removal else None            
                # ---- Storing all these in shared parameters dictionary- all going to use the same. 
                # Store Colours in session state
                st.session_state["dq_dv_smoothed_colours"] = smoothed_colours  
                st.rerun()


with tab2:
    st.subheader("Smoothed Plots")

    show_legend_smooth = st.toggle("Show Legend", key="dqdv_show_legend_smooth")

    # with st.expander("⚙️ Smoothing Parameters", expanded=True):
    #     # Use st.form here for faster app
    #     with st.form("smoothing_parameters_form"):
    #         spike_removal = st.toggle("Remove Spikes")
    #         col1, col2 = st.columns(2)
    #         with col1:
    #             smoothing_window = st.slider("Window Size (Must be odd)", min_value=5, max_value=51, value=15, step=2, help = "Number of datapoints used in the filter. Larger values will result in more aggressive smoothing (Default 15)")
    #         with col2:
    #             polyorder = st.slider("Polynomial Order", min_value=1, max_value=5, value=2, help = "Interger parameter specifies order of polynomial used to fit data. Lower values (2,3) recommended to avoid overfitting")
            
    #         if spike_removal:
    #             with col1:
    #                 spike_window = st.slider("Spike Window size", min_value=1, max_value=10, value = 3, step = 2,  help = "Odd integer parameter that determines the window size for rolling average used for spike removal")
    #             with col2:
    #                 spike_threshold = st.number_input("Spike Removal Threshold (Std Dev)", value=2.0, help = "Determines the sensitivity of spike removal. Data point considered a spike if deviation from rolling average is greater than this multiplied by rolling standard deviation. Larger values (4,5) will make spike detention less sensitive.")
            
    #         cola, colb, colc = st.columns(3)
    #         smoothed_colours = {}
    #         with cola:
    #             charge_colour = st.color_picker("Select colour for Charge", value=default_dqdv_smooth_charge_colour, key = 'dqdv_smooth_charge_colour')
    #             smoothed_colours['Charge_Colour'] = charge_colour
    #         with colb:
    #             discharge_colour = st.color_picker("Select colour for Disharge", value=default_dqdv_smooth_discharge_colour, key = 'dqdv_smooth_dischrage_colour')
    #             smoothed_colours['Discharge_Colour'] = discharge_colour
    #         with colc: 
    #             st.write("")
    #             reset_clicked = st.form_submit_button("Default Colours(Smooth)",on_click=reset_smooth_colours )

    #         submitted = st.form_submit_button("Update Smoothing Parameters")
    #         if submitted:
    #             if "sample_parameters" in st.session_state:
    #                 st.session_state["sample_parameters"]["shared"]["smoothing_window"] = smoothing_window
    #                 st.session_state["sample_parameters"]["shared"]["polyorder"] = polyorder
    #                 st.session_state["sample_parameters"]["shared"]["spike_removal"] = spike_removal
    #                 st.session_state["sample_parameters"]["shared"]["spike_window_size"] = spike_window if spike_removal else None
    #                 st.session_state["sample_parameters"]["shared"]["spike_threshold_multiplier"] = spike_threshold if spike_removal else None            
    #                 # ---- Storing all these in shared parameters dictionary- all going to use the same.   

    # Testing @st.fragment UI element
    smoothing_ui_fragment()
    if "dq_dv_smoothed_colours" in st.session_state:
        smoothed_colours = st.session_state["dq_dv_smoothed_colours"]

    if st.button("Generate Smoothed Plots"):
        st.session_state["dQ_dV_smoothed"] = {}
        for filename, df in st.session_state["data"].items():
            # Access parameters
            file_params = st.session_state["sample_parameters"][filename]
            shared_params = st.session_state["sample_parameters"]["shared"]

            smooth_fig_captions= generate_dq_dv_smoothed(df, file_params, shared_params, smoothed_colours, filename, show_legend_smooth)
            st.session_state["dQ_dV_smoothed"][filename] = smooth_fig_captions
    
    # Display figures if they are in session state
    if "dQ_dV_smoothed" in st.session_state:
        for filename, figures_list in st.session_state["dQ_dV_smoothed"].items():
            st.subheader(f"Key Cycle Graphs (smoothed) for {filename}")
            display_figures_conditionally(figures_list)


    # then file_params = st.session_state["sample_parameters"][filename]
    #    shared_params = st.session_state["sample_parameters"]["shared_parameters"]