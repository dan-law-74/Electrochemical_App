import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from Processing.calculations import filter_key_cycles, half_cell_calculations, comparitive_capacity_calculations, comparitive_percent_capacity_calculations, calculate_dq_dv




def display_figures_conditionally(list_of_figure_info, threshold=4):
    
    def render_figures():
        for fig, caption_str in list_of_figure_info:
            st.caption(caption_str)
            st.pyplot(fig)
            plt.close(fig)

    if len(list_of_figure_info) > threshold:
        with st.container(height=600):
            render_figures()
    else:
        render_figures()  

def generate_voltage_profile(data_df, params, show_legend, common_xaxis_scale, global_max_capacity,filename, plot_key_cycles_only=False):
    # Get user-defined parameters
    composition = params.get('composition', 'Unknown')
    charge_rate_c = params.get('charge_rate_c', 'Unknown')
    colour_palette = params.get('colour_palette', 'viridis_r')
    
    # Retrieve key_cycles, ensuring it's an iterable (list) or defaults to an empty list if None
    key_cycles = params.get('key_cycles') 
    key_cycles_for_annotation = key_cycles if key_cycles is not None else []
    # data_df_cleaned, data_df_discharge, data_df_charge, unique_cycles = process_voltage_profile_data(data_df, filename)

    data_df_discharge = data_df[data_df['Step'] == 'Discharge']
    data_df_charge = data_df[data_df['Step'] == 'Charge']
    unique_cycles = sorted(data_df['Cycle'].unique())

    # If plot_key_cycles_only is True, filter unique_cycles to only include those in key_cycles
    if plot_key_cycles_only and key_cycles:
        data_df_discharge, data_df_charge, unique_cycles = filter_key_cycles(data_df_discharge, data_df_charge, unique_cycles, key_cycles)
    
    # Number of total cycles to plot (used for color palette)
    num_cycles = len(unique_cycles)

    # Create the figure and axes
    fig, ax = plt.subplots() # Create a new figure for each dataset

    # Get the color palette
    palette = sns.color_palette(colour_palette, n_colors=num_cycles)

    #Plot Discharge Data
    for i, cycle in enumerate(unique_cycles):
        df_cycle = data_df_discharge[data_df_discharge['Cycle'] == cycle]
        label = f'Cycle {cycle}' if show_legend and (key_cycles is None or cycle in key_cycles) else None
        ax.plot(df_cycle['Discharge_Capacity'], df_cycle['Voltage'],
                color=palette[i], linestyle='-', linewidth=1.0, label=label)
    #Plot Charge Data
    for i, cycle in enumerate(unique_cycles):
        df_cycle = data_df_charge[data_df_charge['Cycle'] == cycle]
        label = f'Cycle {cycle}' if show_legend and (key_cycles is None or cycle in key_cycles) else None
        ax.plot(df_cycle['Charge_Capacity'], df_cycle['Voltage'],
                color=palette[i], linestyle='--', linewidth=1.0)

 # --- Add Annotations for Key Cycles with Collision Avoidance ---
    placed_annotations_coords = [] # Stores (capacity, voltage) of placed annotations. Filled later
    
    # Sort key_cycles in descending order to prioritize higher cycle numbers
    # Use the safe 'key_cycles_for_annotation' list here
    key_cycles_to_annotate = sorted([c for c in unique_cycles if c in key_cycles_for_annotation], reverse=True)
    #For Loop to annotate key cycles with collision avoidance. Simplified into a single function to avoid code repetition. 
    # We loop through the key cycles and attempt to annotate both charge and discharge points for each cycle, 
    # checking for collisions before placing each annotation. If a collision is detected, that annotation is skipped
    #  to maintain clarity of the graph.
    for cycle_to_annotate in key_cycles_to_annotate:
        color_for_cycle = palette[unique_cycles.index(cycle_to_annotate)]
        
        annotate_cycle(ax, data_df_discharge, cycle_to_annotate, 'Discharge_Capacity', 
                    color_for_cycle, placed_annotations_coords, y_offset=-8, va='top')
        
        annotate_cycle(ax, data_df_charge, cycle_to_annotate, 'Charge_Capacity', 
                    color_for_cycle, placed_annotations_coords, y_offset=8, va='bottom')

    # Create the custom legend
    if show_legend:
        if key_cycles:
            handles, labels = ax.get_legend_handles_labels()
            key_handles = []
            key_labels = []
            for handle, label in zip(handles, labels):
                if label.startswith('Cycle') and int(label.split(' ')[1]) in key_cycles:
                    key_handles.append(handle)
                    key_labels.append(f'{label} (— DChg, -- Chg)')
            if key_handles:
                ax.legend(key_handles, key_labels, bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0, fontsize=10)
        else:
            handles, labels = ax.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            ax.legend(by_label.values(), [f'{label} (— DChg, -- Chg)' for label in by_label.keys()],
                        bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0, fontsize=10)

    #Setting up other layouts
    plt.xlabel("Specific Capacity / mAh g$^{-1}$", fontsize=16)
    plt.ylabel("Voltage / V", fontsize=16)
    ax.tick_params(axis='both', labelcolor='black', labelsize=14, width=1)
    if common_xaxis_scale and global_max_capacity > 0:
        ax.set_xlim(left=0, right=global_max_capacity)  
    plt.tight_layout(rect=[0,0,1,0.95])
    caption = f"Figure <X>. Voltage profiles for the first {num_cycles} galvanostatic cycles of {composition}, cycled between {data_df['Voltage'].min():.1f} and {data_df['Voltage'].max():.1f} V at a rate of {charge_rate_c}. "
    caption += "|Discharge data are represented with solid lines, with dashed lines used for charge. Colours are related to cycle number."

    return fig, caption

def annotate_cycle(ax, df, cycle, capacity_col, color, placed_annotations_coords, y_offset, va):
    # Annotate cycles in generate_voltage_profile with collision avoidance
    df_cycle = df[df['Cycle'] == cycle]
    if df_cycle.empty:
        return
    
    max_cap_row = df_cycle.loc[df_cycle[capacity_col].idxmax()]
    annotate_capacity = max_cap_row[capacity_col]
    annotate_voltage = max_cap_row['Voltage']

    # Check for collision
    for prev_cap, prev_volt in placed_annotations_coords:
        if abs(annotate_capacity - prev_cap) < 5 and abs(annotate_voltage - prev_volt) < 0.05:
            return  # Colliding, skip annotation
    
    ax.annotate(
        str(cycle),
        xy=(annotate_capacity, annotate_voltage),
        xytext=(0, y_offset),
        textcoords='offset points',
        ha='center',
        va=va,
        fontsize=8,
        color=color,
        weight='bold'
    )
    placed_annotations_coords.append((annotate_capacity, annotate_voltage))

def generate_half_cell_profile(data_df, params, show_legend, common_y_axis_capacity, global_max_capacity_val, common_y_axis_efficiency, global_max_efficiency_val, colours, filename):
    
    # Get user defined parameters.
    #get user defined parameters.
    composition = params.get('composition', 'Unknown')
    charge_rate_c = params.get('charge_rate_c', 'Unknown')
    electrode_type = params.get('electrode_type', 'Unknown')

    half_cell_data, voltage_min, voltage_max = half_cell_calculations(data_df, electrode_type, filename)

    # Create figures and axis
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()  # Create a second y-axis for efficiency
    ax1.grid(False)
    ax2.grid(False)

    # # Plot charge capacity
    ax1.plot(
        half_cell_data['Cycle'], 
        half_cell_data['Charge_Capacity'], 
        color=colours["Charge"] if "Charge" in colours else 'tab:orange', 
        marker='s',
        markersize=8,
        label='Charge' if show_legend else None, 
        linestyle=''        
        )
    # Plot discharge capacity
    ax1.plot(
        half_cell_data['Cycle'], 
        half_cell_data['Discharge_Capacity'],  
        color=colours["Discharge"] if "Discharge" in colours else 'tab:blue', 
        marker='o',
        markersize=8,
        label='Discharge' if show_legend else None, 
        linestyle=''        
        )
    # Plot efficiencyon secondary y-axis
    ax2.plot(
        half_cell_data['Cycle'], 
        half_cell_data['efficiency'], 
        color=colours["Efficiency"] if "Efficiency" in colours else "#000000", 
        marker='^',
        markersize=8,
        label='Efficiency' if show_legend else None, 
        linestyle=''        
        )
    # Apply common y-axis scaling if toggled on
    if common_y_axis_capacity and global_max_capacity_val > 0:
        ax1.set_ylim(0, global_max_capacity_val)
    else: 
        ax1.autoscale_view()
        ax1.set_ylim(bottom=0)        

    if common_y_axis_efficiency and global_max_efficiency_val > 0:
        ax2.set_ylim(0, global_max_efficiency_val)
    else:
        if not half_cell_data['efficiency'].empty:
            ax2.set_ylim(0, max(110, half_cell_data['efficiency'].max() * 1.1))
        else:
            ax2.set_ylim(0, 110)

    ax1.tick_params(axis='both', labelcolor='black', labelsize=12, width=2)
    ax2.tick_params(axis='y', labelcolor='black', labelsize=12, width=2)

    # Legend control
    if show_legend:
        ax1.legend(bbox_to_anchor=(1.15, 1), loc='upper left', borderaxespad=0, fontsize=10, frameon=False)
        y_offset = 0.1
        ax2.legend(["Coulombic Efficiency"], bbox_to_anchor=(1.15, 1 - y_offset), loc='upper left', borderaxespad=0, fontsize=10, frameon=False)
         
    # set labels
    ax1.set_xlabel("Cycle number", fontsize=16)
    ax1.set_ylabel("Specific capacity / mAh g$^{-1}$", fontsize=14)
    ax2.set_ylabel("Coulombic efficiency / %", fontsize=14)    

 # Construct the caption
    if electrode_type.lower() == 'positive(cathode)':
        voltage_limits = f"{voltage_min:.2f} - {voltage_max:.2f} V"
    else:
        voltage_limits = f"{voltage_max:.2f} - {voltage_min:.2f} V"

    caption = f"Figure <{filename}>. Specific (dis)charge capacities and Coulombic efficiencies for {composition} cycled at {charge_rate_c} C between {voltage_limits}."

    return fig, caption

def generate_comparitive_profile(data_dfs, params, show_legend):

    # Get processed plot data
    processed_plot_data, metadata = comparitive_capacity_calculations(data_dfs, params)

    # Catch errors if any were made in calculations
    if metadata.get('error'):
        return metadata['error'], None
    
    fig, ax = plt.subplots(figsize = (9,7))
    colourblind_palette = sns.color_palette("colorblind", n_colors=10)   

    # Loop over processed data and plot
    for i, (filename, cycle_capacity) in enumerate(processed_plot_data.items()):
        ax.plot(
        cycle_capacity['Cycle'],
        cycle_capacity['Discharge_Capacity'],
        label=filename,
        color=colourblind_palette[i % 10],
        marker='o',
        linestyle='',
        markersize=8
        )

    # Construct Caption
    all_compositions = ", ".join(metadata['caption_parts'])
    representative_charge_rate = next((param.get('charge_rate_c', 'Unknown') for param in params.values() if 'charge_rate_c' in param), 'Unknown')    

    caption = f"Discharge capacity for {all_compositions} cycled at {representative_charge_rate} C between {metadata['voltage_min']:.1f}-{metadata['voltage_max']:.1f} V for {metadata['max_cycles']} cycles."

    # Formatting
    ax.set_xlim(0, ax.get_xlim()[1])
    ax.set_ylim(0, ax.get_ylim()[1])

    ax.set_xlabel("Cycle number", fontsize=14)
    ax.set_ylabel("Specific capacity / mAh g$^{-1}$", fontsize=14)
    ax.set_title("Comparitive Discharge Capacity vs Cycle Number", fontsize=18)
    
    if show_legend:
        ax.legend(fontsize=10)

    ax.tick_params(axis='both', labelcolor='black', labelsize=12, width=1)
    plt.tight_layout()

    return fig, caption

def generate_comparitive_percent_profile(data_dfs, params, show_legend, remove_outliers, outlier_percentage=None):
    # Generate comparitive percent profiles. processes data, calculates and plots. 
    # INPUT: Dictionary of Data dataframes
    # OUTPUT: fig, caption
    
    fig, ax = plt.subplots(figsize = (9,7))
    markers = ['o', 's', '^', 'v', 'D', 'P', '*', 'X']

    # Get plot data
    processed_plot_data, metadata = comparitive_percent_capacity_calculations(data_dfs, params, remove_outliers, outlier_percentage)

    # Plotting Loop
    for i, (filename, plot_df) in enumerate(processed_plot_data.items()):
        legend_label = metadata['legend_labels'].get(filename) if show_legend else None

        ax.plot(
            plot_df['Cycle'], 
            plot_df['Discharge Capacity Retention (%)'],
            label = legend_label,
            marker = markers[i % len(markers)],
            linestyle = '', 
            markersize = 8
        )

    # Axis labels and formatting
    ax.set_xlabel("Cycle number", fontsize=16)
    ax.set_ylabel("Discharge capacity retention / %", fontsize=16)
    if show_legend:
        ax.legend(loc = 'upper left', bbox_to_anchor=(1.02, 1), borderaxespad=0, fontsize=10, frameon=False)
    fig.tight_layout(rect = [0,0,1,.85])

    max_ret = max(metadata['max_retention'], default = 0)
    if max_ret > 105:
        ax.set_ylim(bottom = 0, top = max_ret*1.05)

    # Caption
    if remove_outliers:
        caption = "Figure <Z>. Discharge capacity retention vs. cycle number for multiple datasets (outliers removed)."
    else: 
        caption = "Figure <Y>. Discharge capacity retention vs. cycle number for multiple datasets (raw data)."
    fig.text(0.5, -0.15, caption, wrap=True, horizontalalignment='center', fontsize=12, transform=fig.transFigure)


    return fig, caption

def generate_capacity_fade_rate_figures(fade_rate_data, compositions, show_legend):
    # Plot capacity fade over cycling (essentially cumulative)
    colorblind_palette = sns.color_palette("colorblind", n_colors=len(fade_rate_data))
    use_composition_in_legend = len(compositions) > 1

    fig_fade_rate, ax_fade_rate  = plt.subplots()
    # Plot results
    for i, (filename, fdf) in enumerate(fade_rate_data.items()):
        label_text = fdf["Composition"].iloc[0] if use_composition_in_legend else filename
        ax_fade_rate.scatter(
            fdf['Cycle'], 
            fdf['Percentage Capacity Loss'], 
            label=label_text if show_legend else None, 
            color=colorblind_palette[i], 
            marker='o', 
            s=50
        )
    # Configure axes
    ax_fade_rate.set_xlabel("Cycle number", fontsize=14)
    ax_fade_rate.set_ylabel("Percentage capacity loss / %", fontsize=14)
    ax_fade_rate.set_title("Capacity Fade over Cycling", fontsize=16)
    if show_legend: 
        ax_fade_rate.legend(fontsize=10)
    ax_fade_rate.tick_params(axis='both', labelcolor='black', labelsize=12, width=1)
    fig_fade_rate.tight_layout()

    caption = "Figure <X>. Percentage capacity fade over cycle number for electrochemical cells. Colours distinguish different datasets. A loss of 0% indicates capacity equal to the first stable cycle."

    return fig_fade_rate, caption

def generate_capacity_loss_per_cycle_figures(fade_rate_data, compositions, show_legend):
    # Plot capacity loss per cycle
    colorblind_palette = sns.color_palette("colorblind", n_colors=len(fade_rate_data))
    use_composition_in_legend = len(compositions) > 1

    fig_loss_per_cycle, ax_loss_per_cycle  = plt.subplots()
    # Plot results
    for i, (filename, fdf) in enumerate(fade_rate_data.items()):
        label_text = fdf["Composition"].iloc[0] if use_composition_in_legend else filename
        ax_loss_per_cycle.scatter(
            fdf['Cycle'], 
            fdf['Percentage Loss per Cycle'], 
            label=label_text if show_legend else None, 
            color=colorblind_palette[i], 
            marker='o', 
            s=50
        )
    ax_loss_per_cycle.set_xlabel("Cycle number", fontsize=14)
    ax_loss_per_cycle.set_ylabel("Percentage capacity loss per Cycle / %", fontsize=14)
    ax_loss_per_cycle.set_title("Capacity Loss per Cycle", fontsize=16)
    if show_legend: 
        ax_loss_per_cycle.legend(fontsize=10)
    ax_loss_per_cycle.tick_params(axis='both', labelcolor='black', labelsize=12, width=1)
    fig_loss_per_cycle.tight_layout()    
    caption = "Figure <X>. Percentage capacity loss per cycle for electrochemical cells. Each point represents the percentage capacity change from the previous cycle. Colours distinguish different datasets."

    return fig_loss_per_cycle, caption

def annotate_cycles_with_collision_check(ax, df, x_col, y_col, key_cycles, placed_annotations, colour, x_tol=2, y_tol_pct=0.05, text_offset=(0, 8), text_ha='center'):
    # Pre-calculate the Y-axis tolerance
    max_y = max(df[y_col].max(), 1e-9)
    y_tolerance = max_y * y_tol_pct

    # Filter the dataframe to key_cycles
    annotation_df = df[df['Cycle'].isin(key_cycles)]

    for _, row in annotation_df.iterrows():
        x_val = row[x_col]
        y_val = row[y_col]
        cycle_val = row['Cycle'] # We always want the text to be the cycle number

        is_colliding = False
        
        # Check for collisions
        for prev_x, prev_y in placed_annotations:
            if abs(x_val - prev_x) < x_tol and abs(y_val - prev_y) < y_tolerance:
                is_colliding = True
                break
        
        if not is_colliding:
            ax.annotate(
                str(int(cycle_val)),
                xy=(x_val, y_val),
                xytext= text_offset,
                textcoords='offset points',
                ha=text_ha,
                va='bottom',
                fontsize=8,
                color=colour,
                weight='bold'
            )
            placed_annotations.append((x_val, y_val))

def generate_energy_density_plot(power_energy_data, params, show_legend):
    fig_energy_cycle, ax_energy_cycle = plt.subplots()
    colorblind_palette = sns.color_palette("colorblind", n_colors=len(power_energy_data))
    placed_annotations = [] # For Energy vs. Cycle plot

    for i, (filename, pe_df) in enumerate(power_energy_data.items()):
        colour = colorblind_palette[i % len(power_energy_data)]
        composition = params.get(filename, {}).get('Composition', 'Unknown')

        key_cycles = params.get(filename, {}).get('key_cycles', 'Unknown')

        # Filter key cycles to only those present in the dataframe
        key_cycles_to_annotate = sorted([c for c in pe_df['Cycle'].unique() if c in key_cycles], reverse=True)

        # Calculate Wh/kg for energy density
        pe_df['Max_Specific_Energy_Wh_kg'] = pe_df['Max_Specific_Energy_mWh_g']

        # Plotting
        ax_energy_cycle.plot(pe_df['Cycle'], 
                             pe_df['Max_Specific_Energy_Wh_kg'], 
                             label = filename if show_legend else None,
                             color=colour, 
                             marker='o', 
                             linestyle='-'
                             )

        # Add annotations next
        annotate_cycles_with_collision_check(ax_energy_cycle, pe_df,'Cycle', 'Max_Specific_Energy_Wh_kg', key_cycles_to_annotate, placed_annotations, colour )
    
    # -- formating energy vs cycle plot
    ax_energy_cycle.set_xlabel("Cycle Number", fontsize=14)
    ax_energy_cycle.set_ylabel("Maximum Specific Energy / Wh kg$^{-1}$", fontsize=14)
    ax_energy_cycle.set_title("Maximum Specific Energy vs. Cycle Number", fontsize=16)
    #ax_energy_cycle.grid(True, linestyle=":", linewidth=0.5, color='.25', zorder=-10)
    ax_energy_cycle.tick_params(axis='both', labelcolor='black', labelsize=12, width=1)
    if show_legend: 
        ax_energy_cycle.legend(fontsize = 10)
    ax_energy_cycle.set_ylim(bottom=0) # Set lower limit for y-axis to 0
    fig_energy_cycle.tight_layout()

    #Caption
    caption_energy_cycle = "Figure <Y.1>. Evolution of maximum specific energy (Wh kg$^{-1}$) as a function of cycle number for different materials. The y-axis starts at zero. Key cycles are annotated directly on the curves."
    fig_energy_cycle.text(0.5, -0.05, caption_energy_cycle, wrap=True, horizontalalignment='center', fontsize=12, transform=fig_energy_cycle.transFigure)
    fig_energy_cycle.subplots_adjust(bottom=0.15)

    return fig_energy_cycle, caption_energy_cycle

def generate_power_density_plot(power_energy_data, params, show_legend):
    fig_power_cycle, ax_power_cycle = plt.subplots()
    colorblind_palette = sns.color_palette("colorblind", n_colors=len(power_energy_data))
    placed_annotations = [] # For Power vs Cycle plot

    for i, (filename, pe_df) in enumerate(power_energy_data.items()):
        colour = colorblind_palette[i % len(power_energy_data)]
        composition = params.get(filename, {}).get('Composition', 'Unknown')

        key_cycles = params.get(filename, {}).get('key_cycles', 'Unknown')

        # Filter key cycles to only those present in the dataframe
        key_cycles_to_annotate = sorted([c for c in pe_df['Cycle'].unique() if c in key_cycles], reverse=True)
        power_col = 'Max_Power_W_g' if 'Max_Power_W_g' in pe_df.columns else 'Max_Power_W'
        ax_power_cycle.plot(pe_df['Cycle'], 
                            pe_df[power_col],
                            label = filename if show_legend else None, 
                            color=colour, 
                            marker='s', 
                            linestyle='-'
                            )
        annotate_cycles_with_collision_check(ax_power_cycle, pe_df, 'Cycle', power_col,key_cycles_to_annotate, placed_annotations, colour)

        # if 'Max_Power_W_g' in pe_df.columns:
        #     ax_power_cycle.plot(pe_df['Cycle'], 
        #                         pe_df['Max_Power_W_g'],
        #                         label = filename if show_legend else None, 
        #                         color=colour, 
        #                         marker='s', 
        #                         linestyle='-'
        #                         )
        #     # Add annotations
        #     annotate_cycles_with_collision_check(ax_power_cycle, pe_df, 'Cycle', 'Max_Power_W_g',key_cycles_to_annotate, placed_annotations, colour)

        # else: # Max_Power_W instead
        #     ax_power_cycle.plot(pe_df['Cycle'], pe_df['Max_Power_W'], label = filename if show_legend else None, color=colour, marker='s', linestyle='-')
        #     annotate_cycles_with_collision_check(ax_power_cycle, pe_df, 'Cycle', 'Max_Power_W',key_cycles_to_annotate, placed_annotations, colour)
    
    # --- Formatting Power vs. Cycle Plot ---
    ax_power_cycle.set_xlabel("Cycle Number", fontsize=14)
    #y_label logic
    y_label = "Maximum power / W"
    if power_energy_data:
        # Grab the first DataFrame directly from the values
        first_df = list(power_energy_data.values())[0] 
        
        # Check the columns
        if 'Max_Power_W_g' in first_df.columns:
            y_label = "Maximum Power / W g$^{-1}$"

    ax_power_cycle.set_ylabel(y_label, fontsize=14)
    ax_power_cycle.set_title("Maximum Power vs. Cycle Number", fontsize=16)
    #ax_power_cycle.grid(True, linestyle=":", linewidth=0.5, color='.25', zorder=-10)
    ax_power_cycle.tick_params(axis='both', labelcolor='black', labelsize=12, width=1)
    if show_legend:
        ax_power_cycle.legend(fontsize = 10)
    ax_power_cycle.set_ylim(bottom=0) # Set lower limit for y-axis to 0
    fig_power_cycle.tight_layout()
    
    # Caption
    caption_power_cycle = "Figure <Y.2>. Evolution of maximum absolute power as a function of cycle number for different materials. The y-axis starts at zero. Key cycles are annotated directly on the curves."
    return fig_power_cycle, caption_power_cycle

def generate_ragone_power_density_plot(power_energy_data, params, show_legend):
    fig_ragone, ax_ragone = plt.subplots()
    colorblind_palette = sns.color_palette("colorblind", n_colors=len(power_energy_data))
    placed_annotations = [] # For ragone-like plot

    for i, (filename, pe_df) in enumerate(power_energy_data.items()):
        colour = colorblind_palette[i % len(power_energy_data)]
        composition = params.get(filename, {}).get('Composition', 'Unknown')
        pe_df['Max_Specific_Energy_Wh_kg'] = pe_df['Max_Specific_Energy_mWh_g'] # Need this line in for future calcs

        key_cycles = params.get(filename, {}).get('key_cycles', 'Unknown')

        # Filter key cycles to only those present in the dataframe
        key_cycles_to_annotate = sorted([c for c in pe_df['Cycle'].unique() if c in key_cycles], reverse=True)
        
        power_col = 'Max_Power_W_g' if 'Max_Power_W_g' in pe_df.columns else 'Max_Power_W'
        ax_ragone.scatter(
            pe_df['Max_Specific_Energy_Wh_kg'], # X-axis data
            pe_df[power_col],                   # Y-axis data
            color=colour, 
            s=50, 
            label = filename
        )
        annotate_cycles_with_collision_check(ax_ragone, pe_df, 'Max_Specific_Energy_Wh_kg', power_col, key_cycles_to_annotate, placed_annotations, colour, x_tol = 5, text_offset=(8,8), text_ha='left')


    # --- Formatting Ragone-like Plot ---
    ax_ragone.set_xlabel("Specific Energy (Wh kg$^{-1}$)", fontsize=14)
    # y_label logic
    y_label = "Maximum power / W"
    if power_energy_data:
        # Grab the first DataFrame directly from the values
        first_df = list(power_energy_data.values())[0] 
        
        # Check the columns
        if 'Max_Power_W_g' in first_df.columns:
            y_label = "Maximum Power / W g$^{-1}$"    
    ax_ragone.set_ylabel(y_label, fontsize=14)

    ax_ragone.set_title("Ragone-like Plot (Max Power vs. Max Energy)", fontsize=16)
    ax_ragone.tick_params(axis='both', labelcolor='black', labelsize=12, width=1)

    # Legend
    if show_legend:
        ax_ragone.legend(fontsize = 10)
    ax_ragone.set_xlim(left=0) # Set lower limit for x-axis to 0
    ax_ragone.set_ylim(bottom=0) # Set lower limit for y-axis to 0
    fig_ragone.tight_layout()

    # Caption
    caption_ragone = "Figure <Z>. Ragone-like plot showing the relationship between maximum specific energy (Wh kg$^{-1}$) and maximum absolute power for different materials across their cycle life. Both axes start from zero. Key cycles are annotated directly on the plot."

    return fig_ragone, caption_ragone

def plot_filter_dq_dv(ax, df, step_type, plot_colour, plot_linestyle, show_legend, smoothed = False, num_spikes = None):
    # Universal helper to filter edge cases in dQ/dV plot and actaully plot it
    if not df.empty and 'Voltage' in df.columns and 'dQ/dV' in df.columns and 'Cycle' in df.columns:
        # Plot Data, grouped by cycle
        label_added = False
        for cycle_num, cycle_data in df.groupby('Cycle'):
            if smoothed:
                if num_spikes is not None:
                    label_to_plot = f'{step_type} (smoothed, {num_spikes} spikes removed)' if not label_added and show_legend else None
                else:
                    label_to_plot = f'{step_type} (smoothed)' if not label_added and show_legend else None
            else:
                label_to_plot = f'{step_type}' if not label_added and show_legend else None

            if smoothed:
                y_data = cycle_data['dQ/dV_Smoothed']
            else:
                y_data = cycle_data['dQ/dV']
            ax.plot(
                cycle_data['Voltage'],
                y_data,
                label = label_to_plot,
                color = plot_colour,
                linestyle = plot_linestyle,
                alpha = 0.6
            )
            label_added = True

def generate_full_dq_dv_plot(data_df, params, colours, filename, show_legend):
    fig, ax = plt.subplots(figsize=(12,7))
    # Get data
    data_df_charge = data_df[data_df['Step'] == 'Charge'].sort_values(by='Voltage').copy()
    data_df_discharge = data_df[data_df['Step'] == 'Discharge'].sort_values(by='Voltage').copy()

    # Process data
    df_charge_processed = calculate_dq_dv(data_df_charge)
    df_discharge_processed = calculate_dq_dv(data_df_discharge)

    # Get colours
    charge_colour = colours['Charge_Colour']
    discharge_colour = colours['Discharge_Colour']

    default_dqdv_charge_linestyle = '-'
    default_dqdv_discharge_linestyle = '-'


    # Call for charge data
    plot_filter_dq_dv(ax, df_charge_processed, 'Charge',charge_colour,default_dqdv_charge_linestyle, show_legend)
    # Call for discharge data
    plot_filter_dq_dv(ax, df_discharge_processed, 'Discharge',discharge_colour,default_dqdv_discharge_linestyle, show_legend)


    ax.set_xlabel("Voltage / V", fontsize=12)
    ax.set_ylabel("dQ/dV / mAh V$^{-1}$ g$^{-1}$", fontsize=12)
    ax.set_title(
        f"dQ/dV vs. Voltage for {filename} (Full Range, Excluding 0.05V at Ends)", fontsize=14)  # Include dataset name in title
    if show_legend:
        ax.legend(fontsize=10)

    ax.tick_params(axis='both', labelcolor='black', labelsize=10, width=1)
    fig.tight_layout()
    caption = f"Figure <X>. Full range differential capacity, dQ/dV, plots for {filename}. Data within 0.05 V of either voltage extreme are omitted."

    return fig, caption

def generate_dq_dv_key_cycles_plot(data_df, params, colours, filename, show_legend):
    # Get params
    composition = params.get('composition', 'Unknown')
    charge_rate_c = params.get('charge_rate_c', 'Unknown')
    key_cycles = params.get('key_cycles', [])    

    # Get colours
    charge_colour = colours['Charge_Colour']
    discharge_colour = colours['Discharge_Colour']

    default_dqdv_charge_linestyle = '-'
    default_dqdv_discharge_linestyle = '-'    
    # Min/max voltage for caption
    voltage_min = data_df['Voltage'].min()
    voltage_max = data_df['Voltage'].max()

    figs_and_captions = []
    for cycle_num in key_cycles:
        # Collect Data
        df_cycle = data_df[data_df['Cycle'] == cycle_num].copy()
        df_charge = df_cycle[df_cycle['Step'] == 'Charge'].sort_values(by='Voltage').copy()
        df_discharge = df_cycle[df_cycle['Step'] == 'Discharge'].sort_values(by='Voltage').copy()

        # Filter Data
        df_charge_processed = calculate_dq_dv(df_charge)
        df_discharge_processed = calculate_dq_dv(df_discharge)
        
        # Create figure
        fig, ax = plt.subplots()
        
        # Plot data using helper function
        plot_filter_dq_dv(ax, df_charge_processed, 'Charge', charge_colour, default_dqdv_charge_linestyle, show_legend)
        plot_filter_dq_dv(ax, df_discharge_processed, 'Discharge', discharge_colour, default_dqdv_discharge_linestyle, show_legend) 

        # Graph Settings
        ax.set_title(
            f"dQ/dV vs. Voltage for {filename} for cycle {cycle_num} (Excluding 0.05V at Ends)", fontsize=14)
        ax.set_xlabel("Voltage / V", fontsize=14)
        ax.set_ylabel("dQ/dV / mAh V$^{-1}$ g$^{-1}$", fontsize=14)
        ax.tick_params(axis='both', labelsize=12)
        if show_legend:
            ax.legend(fontsize=10)
        plt.tight_layout()        

        # Caption
        caption = f"Figure <X>. Differential capacity, dQ/dV, plots for {composition} during the {cycle_num}{'st' if cycle_num == 1 else 'nd' if cycle_num == 2 else 'rd' if cycle_num == 3 else 'th'} cycle of a half-cell being cycled at {charge_rate_c} C between {voltage_min:.2f} and {voltage_max:.2f} V. Data within 0.05 V of either voltage extreme are omitted."

        figs_and_captions.append((fig, caption))

    return figs_and_captions

def generate_dq_dv_smoothed(data_df, file_params, shared_params, colours, filename, show_legend):

    # Get file parameters
    key_cycles = file_params.get('key_cycles', [])
    composition = file_params.get('composition', 'Unknown')
    charge_rate_c = file_params.get('charge_rate_c', 'Unknown')
    # Colurs
    charge_colour = colours.get('Charge_Colour')
    discharge_colour = colours.get('Discharge_Colour')
    #linestyle
    default_dqdv_charge_linestyle = '-'
    default_dqdv_discharge_linestyle = '-' 
    # Min/max voltage for caption
    voltage_min = data_df['Voltage'].min()
    voltage_max = data_df['Voltage'].max()

    figs_and_captions = []

    for cycle_num in key_cycles:
        # Collect Data
        df_cycle = data_df[data_df['Cycle'] == cycle_num].copy()
        df_charge = df_cycle[df_cycle['Step'] == 'Charge'].sort_values(by='Voltage').copy()
        df_discharge = df_cycle[df_cycle['Step'] == 'Discharge'].sort_values(by='Voltage').copy()

        # Filter Data
        df_charge_processed, num_charge_spikes = calculate_dq_dv(df_charge, apply_smoothing=True, shared_params=shared_params)
        df_discharge_processed, num_discharge_spikes = calculate_dq_dv(df_discharge, apply_smoothing=True, shared_params=shared_params)

        # Create figure
        fig, ax = plt.subplots()

        # Plot data using helper function
        plot_filter_dq_dv(ax, df_charge_processed, 'Charge', charge_colour, default_dqdv_charge_linestyle, show_legend, smoothed=True, num_spikes = num_charge_spikes)
        plot_filter_dq_dv(ax, df_discharge_processed, 'Discharge', discharge_colour, default_dqdv_discharge_linestyle, show_legend, smoothed=True, num_spikes = num_discharge_spikes) 

        # Graph Settings
        ax.set_title(
            f"Smoothed dQ/dV vs. Voltage for {filename} for cycle {cycle_num} (Excluding 0.05V at Ends)", fontsize=14)
        ax.set_xlabel("Voltage / V", fontsize=14)
        ax.set_ylabel("dQ/dV / mAh V$^{-1}$ g$^{-1}$", fontsize=14)
        ax.tick_params(axis='both', labelsize=12)
        if show_legend:
            ax.legend(fontsize=10)
        plt.tight_layout()        

        # Caption
        caption = f"Figure <X>. Differential capacity (smoothed), dQ/dV, plots for {composition} during the {cycle_num}{'st' if cycle_num == 1 else 'nd' if cycle_num == 2 else 'rd' if cycle_num == 3 else 'th'} cycle of a half-cell being cycled at {charge_rate_c} C between {voltage_min:.2f} and {voltage_max:.2f} V. Data within 0.05 V of either voltage extreme are omitted."

        figs_and_captions.append((fig, caption))

    return figs_and_captions
