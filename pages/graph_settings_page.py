import streamlit as st
from Processing.parameters import DEFAULTS, recommended_palettes, process_key_cycles_input, build_sample_parameters, check_data_loaded


st.set_page_config(page_title="Graph Settings")
st.title("Graph Settings")
st.write("Customize the parameters for graphing your battery data.")



# initialize session state for sample parameters, and shared (if going to be used)
if "sample_parameters"not in st.session_state:
    st.session_state["sample_parameters"] = {}

if "shared" not in st.session_state["sample_parameters"]:
    st.session_state["sample_parameters"]["shared"] = {}

# Warning message if no data in session state
check_data_loaded()

#------------------------------------------START OF GRAPH SETTINGS PAGE------------------------------------------#

#Add option to apply same settings to all files or customize for each file

#Shortcut this dictionary for these shared settings
existing_shared = st.session_state["sample_parameters"]["shared"]

existing_use_common = existing_shared.get("use_common_settings", False)
use_common_settings = st.checkbox("Use same common settings for all files", value=existing_use_common, help="Toggle to apply the same image format and colour settings to all files.")
st.session_state["sample_parameters"]["shared"]["use_common_settings"] = use_common_settings

if use_common_settings:
    colour_palette = st.selectbox("Colour Palette", recommended_palettes,  key="shared_colour_palette", 
                                  index=recommended_palettes.index(existing_shared.get("colour_palette", recommended_palettes[0])) 
                                   if existing_shared.get("colour_palette") in recommended_palettes else 0)
    
    image_file_format = st.pills("Image File Format", ["png", "tiff"], key="shared_file_format")

    st.session_state["sample_parameters"]["shared"]["colour_palette"] = colour_palette
    st.session_state["sample_parameters"]["shared"]["file_format"] = image_file_format

#setup scrollable container for all files, then loop for each file and individual settings. save settings in session state under sample_parameters
#  with filename as key, then can access these in voltage_profile_page to generate graphs based on individual settings for each file. if use_common_settings is true, then use the shared settings for all files instead of individual settings.
with st.container(height =600):
    for filename in st.session_state["data"].keys():
        existing = st.session_state["sample_parameters"].get(filename, {})

        st.subheader(f"Graph Settings for: {filename}")

        # Multiple inputs below for active ingredient, blend, active material mass, theoretical capacity, charge rate and electreode type
        #Condensed into columns to save space

        col1,col2 = st.columns(2)

        with col1:
            if not use_common_settings:
                image_file_format = st.pills("Image File Format", ["png", "tiff"], key=f"image_file_format_{filename}")

            composition = st.text_input("Active material composition", placeholder="Enter the name of the active ingredient",
                                        key = f"composition_{filename}", value=existing.get("composition", None), help = "E.g. LiCoO2")
            # if not composition:
            #     composition = "Active Material"
            
            active_material_mass_mg = st.number_input("Active material mass (mg)", min_value=0.0, step=0.01, key = f"active_material_mass_mg_{filename}",
                                                    value = float(existing.get("active_material_mass_mg", None)) if existing.get("active_material_mass_mg") is not None else None,
                                                    help="Enter the mass of the active material in milligrams (mg). If left empty these calculations won't work")
            
            charge_rate_c = st.number_input("Charge rate (C)", min_value=0.0, step=0.01, 
                                            value= float(existing.get("charge_rate_c", None)) if existing.get("charge_rate_c") is not None else None, 
                                            key = f"charge_rate_c_{filename}", 
                                            help="Enter the charge rate in C, default is 0.1. If left empty these calculations won't work")

        with col2:
            if not use_common_settings:
                colour_palette = st.selectbox("Colour Palette", recommended_palettes,
                                    index=recommended_palettes.index(existing.get("colour_palette", recommended_palettes[0])) if existing.get("colour_palette") in recommended_palettes else 0,
                                    placeholder="Select a colour palette", 
                                    key = f"colour_palette_{filename}", 
                                    help="Choose a colour palette for the graphs. Leave blank for the default (greys), " \
                                    "but you can also enter a custom palette name if you have specific preferences.")

            blend = st.text_input("Electrode blend", placeholder="Enter the blend composition", 
                                  key = f"blend_{filename}",
                                   value = existing.get("blend", None),
                                   help = "e.g. 80/10/10, leave blank for default")          
            
            theoretical_capacity_mAh_g = st.number_input("Theoretical capacity (mAh/g)", min_value=0.0, step=0.01, 
                                                         value= float(existing.get("theoretical_capacity_mAh_g", None)) if existing.get("theoretical_capacity_mAh_g") is not None else None, 
                                                         key = f"theoretical_capacity_mAh_g_{filename}", help="Enter the theoretical capacity of the active material in mAh/g. If left empty these calculations won't work")
            
            electrode_options = ["Positive(Cathode)", "Negative(Anode)"]
            existing_electrode = existing.get("electrode_type", "Positive(Cathode)")
            electrode_type = st.radio("Electrode Type", ["Positive(Cathode)", "Negative(Anode)"], key = f"electrode_type_{filename}", 
                                      index=electrode_options.index(existing_electrode) if existing_electrode in electrode_options else 0, help ="Default to positive")


        key_cycles_input = st.text_input("Key cycles to plot", 
                                         placeholder="Enter key cycles to plot, separated by commas (e.g. 1, 5, 10, 20)", 
                                         key = f"key_cycles_input_{filename}",value = existing.get("key_cycles_input", None), 
                                         help=f"Enter the key cycles you want to plot, separated by commas. Default: {', '.join(map(str, DEFAULTS['key_cycles']))}")


if st.button("Save Parameters"):
    for filename in st.session_state["data"].keys():
        
        # Grab the raw user inputs (if they are empty, they default to None)
        composition = st.session_state.get(f"composition_{filename}")
        blend = st.session_state.get(f"blend_{filename}")
        active_material_mass_mg = st.session_state.get(f"active_material_mass_mg_{filename}")
        theoretical_capacity_mAh_g = st.session_state.get(f"theoretical_capacity_mAh_g_{filename}")
        charge_rate_c = st.session_state.get(f"charge_rate_c_{filename}")
        key_cycles_input = st.session_state.get(f"key_cycles_input_{filename}", "")
        # key_cycles = st.session_state.get(f"key_cycles_{filename}")
        electrode_type = st.session_state.get(f"electrode_type_{filename}")
        
        # Handle the shared vs individual toggles
        colour_palette = st.session_state["sample_parameters"]["shared"].get("colour_palette", recommended_palettes[0]) if use_common_settings else st.session_state.get(f"colour_palette_{filename}")
        image_file_format = st.session_state["sample_parameters"]["shared"].get("file_format") if use_common_settings else st.session_state.get(f"image_file_format_{filename}")

        # Call the builder,
        params_dict, warning_message = build_sample_parameters(
            composition, blend, active_material_mass_mg,
            theoretical_capacity_mAh_g, charge_rate_c,
            colour_palette, key_cycles_input, image_file_format, electrode_type
        )
        
        # Save it to state
        st.session_state["sample_parameters"][filename] = params_dict
        
        # If builder has warning message, display
        if warning_message:
            st.error(f"For {filename}: {warning_message}")

    st.success("Parameters saved successfully!")


st.json(st.session_state)

