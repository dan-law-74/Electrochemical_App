import streamlit as st
import matplotlib.pyplot as plt
import numpy as np


# default and recommended colour palettes for graphing, imported into graph settings page
recommended_palettes = [
    "viridis_r", "bright", "Greys_d", "Reds", "YlOrRd", "OrRd", "deep",
    "dark", "hls", "husl", "Paired", "Accent", "rocket", "mako",
    "flare", "crest", "vlag", "icefire", "PRGn", "Spectral"
]


DEFAULTS = {
    "composition": "Active Material",
    "blend": "80/10/10",
    "charge_rate_c": 0.1, 
    "theoretical_capacity_mAh_g": 150,
    "active_material_mass_mg": 10,
    "colour_palette": "Greys_d",
    "key_cycles": [1, 5, 10, 20, 30, 40, 50],
    "file_format": "png",
    "electrode_type": "Positive(Cathode)"
}


# Set default figure size for all graphs
figure_width_inches = 9
figure_height_inches = 9
plt.rcParams['figure.figsize'] = (figure_width_inches, figure_height_inches)

# default_key_cycles = [1, 5, 10, 20, 30, 40, 50]

def process_key_cycles_input(key_cycles_input):
    if not key_cycles_input:
        return DEFAULTS["key_cycles"]
    
    try:
        key_cycles = [int(cycle.strip()) for cycle in key_cycles_input.split(",")]
        return key_cycles

    except ValueError:
        raise ValueError("Invalid key cycles entered. Please enter comma-separated integers.")


# Functions to calculate theoretical battery performance based in input
def calculate_theoretical_capacity(active_material_mass_mg, theoretical_capacity_mAh_g): 
    active_material_mass_g = active_material_mass_mg / 1000
    theoretical_capacity_mAh = active_material_mass_g * theoretical_capacity_mAh_g
    return theoretical_capacity_mAh

def calculate_theoretical_current(charge_rate_c, theoretical_capacity_mAh):
    theoretical_charge_current_mA = charge_rate_c * theoretical_capacity_mAh
    return theoretical_charge_current_mA

def calculate_theoretical_charge_rate(theoretical_charge_current_mA, active_material_mass_mg):
    theoretical_charge_rate_mAh_g = theoretical_charge_current_mA / (active_material_mass_mg / 1000)
    return theoretical_charge_rate_mAh_g

# Function to build sample parameters dictionary. Error Checking done inside. 
def build_sample_parameters(composition, blend, active_material_mass_mg, 
                             theoretical_capacity_mAh_g, charge_rate_c,
                             colour_palette,key_cycles_input, file_format, electrode_type):
    warnings = []

    # Validate Blend input
    if blend:
        is_valid_blend = all(part.strip().replace('.', '', 1).isdigit() for part in blend.split('/'))
        if not is_valid_blend:
            blend = None
            warnings.append(f"Invalid blend composition entered. Defaulting to {DEFAULTS['blend']}.")

    # Validate Key Cycles
    key_cycles = None
    if key_cycles_input:
        try:
            key_cycles = process_key_cycles_input(key_cycles_input)
        except ValueError:
            warnings.append(f"Invalid key cycles entered. Defaulting to {DEFAULTS['key_cycles']}.")

    # Validate Zero errors in number inputs
    if not active_material_mass_mg or not theoretical_capacity_mAh_g or not charge_rate_c:
        active_material_mass_mg = active_material_mass_mg or DEFAULTS["active_material_mass_mg"]
        theoretical_capacity_mAh_g = theoretical_capacity_mAh_g or DEFAULTS["theoretical_capacity_mAh_g"]
        charge_rate_c = charge_rate_c or DEFAULTS["charge_rate_c"]
        warnings.append (f"Ensure active material mass, theoretical capacity, and charge rate are non-zero. Using default values.")

    theoretical_capacity_mAh = calculate_theoretical_capacity(active_material_mass_mg, theoretical_capacity_mAh_g)
    theoretical_charge_current_mA = calculate_theoretical_current(charge_rate_c, theoretical_capacity_mAh)
    theoretical_charge_rate_mAh_g = calculate_theoretical_charge_rate(theoretical_charge_current_mA, active_material_mass_mg )

    # Combine Warnings if there are any
    warning_msg = " | ".join(warnings) if warnings else None

    # Setup parameters Dictionary
    params_dict ={
        "composition": composition or DEFAULTS["composition"],
        "blend": blend or DEFAULTS["blend"],
        "active_material_mass_mg": active_material_mass_mg or DEFAULTS["active_material_mass_mg"],
        "theoretical_capacity_mAh_g": theoretical_capacity_mAh_g or DEFAULTS["theoretical_capacity_mAh_g"],
        "charge_rate_c": charge_rate_c or DEFAULTS["charge_rate_c"],
        "colour_palette": colour_palette or DEFAULTS["colour_palette"],
        "key_cycles_input": key_cycles_input,
        "key_cycles": key_cycles or DEFAULTS["key_cycles"],
        "file_format": file_format or DEFAULTS["file_format"],
        "electrode_type": electrode_type or DEFAULTS["electrode_type"],
        "theoretical_capacity_mAh": theoretical_capacity_mAh, 
        "theoretical_charge_current_mA": theoretical_charge_current_mA,
        "theoretical_charge_rate_mAh_g": theoretical_charge_rate_mAh_g,
        #Default parameters for dQ/dV smoothing and spike removal
        'smoothing_window': 15,
        'polyorder': 3,
        'spike_removal': True,
        'spike_window_size': 5,
        'spike_threshold_multiplier': 3,
        # Default parameters for dQ/dV peak finding
        'peak_prominence': 0.02,
        'peak_distance': 10,
        'peak_width': 3,
        'center_error': np.nan        
    }

    return params_dict, warning_msg

def check_data_loaded():
    if not "data" in st.session_state or not st.session_state["data"]:
        st.warning("No data loaded. Please upload and process a file first.")
        st.stop()


def check_parameters():
    if not "sample_parameters" in st.session_state or len( st.session_state["sample_parameters"]) <= 1:
        st.warning("No sample parameters found. Please upload and process a file first.")
        st.stop()
    

