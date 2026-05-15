import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# this Website: https://fonts.google.com/icons?icon.size=32&icon.color=%231f1f1f&icon.platform=web
# To get icons :))
home = st.Page("pages/home.py", title="Home", icon = ":material/home:")

upload = st.Page("pages/upload_data_page.py", title="Upload Data", icon = ":material/upload:")
graph_settings = st.Page("pages/graph_settings_page.py", title="Graph Settings", icon=":material/settings:")

voltage_profile = st.Page("pages/voltage_profile_page.py", title="Voltage Profiles", icon=":material/bar_chart:")
# voltage_key_profile = st.Page("pages/voltage_key_profile_page.py", title="Voltage Key Profile", icon=":material/bar_chart:")
half_cell_profile = st.Page("pages/half_cell_profile_page.py", title="Half Cell Profiles", icon=":material/battery_5_bar:")
max_charge_capacity = st.Page("pages/max_charge_cap_page_.py", title="Max Charge Capacity", icon=":material/bolt:")
capacity_fade_rate_page = st.Page("pages/capacity_fade_rate_page.py", title="Capacity Fade Rate", icon=":material/trending_down:")
power_energy_analysis_page = st.Page("pages/power_energy_analysis_page.py", title="Power/Energy Density Analysis", icon = ":material/grouped_bar_chart:")
dq_dv_analysis_page = st.Page("pages/dq_dv_analysis_page.py", title = "dQ/dV Analysis", icon = ":material/area_chart:")

pages ={"": [home], "Data": [upload, graph_settings], "Voltage Analysis": [voltage_profile, half_cell_profile, max_charge_capacity, capacity_fade_rate_page, power_energy_analysis_page, dq_dv_analysis_page]}
pg = st.navigation(pages)
pg.run()
