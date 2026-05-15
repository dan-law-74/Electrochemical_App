import streamlit as st
import pandas as pd
import numpy as np
from scipy.signal import savgol_filter 


def calculate_common_axis_scale(data):
    # This is used for voltage profile page to calculate common x-axis scale
    if not data:
        return 100  # Default scale if no data is available

    global_max_capacity = 0
    for name, df in data.items():
        df_cleaned_temp = df.dropna(subset=['Charge_Capacity', 'Discharge_Capacity'])
        
        # Ensure capacities are numeric before finding max
        current_max_charge = pd.to_numeric(df_cleaned_temp['Charge_Capacity'], errors='coerce').max()
        current_max_discharge = pd.to_numeric(df_cleaned_temp['Discharge_Capacity'], errors='coerce').max()
        
        # Consider both charge and discharge, and skip NaN if present
        if not pd.isna(current_max_charge):
            global_max_capacity = max(global_max_capacity, current_max_charge)
        if not pd.isna(current_max_discharge):
            global_max_capacity = max(global_max_capacity, current_max_discharge)
    
    # Add a small buffer to the max capacity for better visualization
    # We'll round up to the nearest convenient number (e.g., 10, 50, 100, 500)
    if global_max_capacity > 0:
        if global_max_capacity <= 100:
            global_max_capacity = (global_max_capacity // 10 + 1) * 10
        elif global_max_capacity <= 500:
            global_max_capacity = (global_max_capacity // 50 + 1) * 50
        elif global_max_capacity <= 1000:
            global_max_capacity = (global_max_capacity // 100 + 1) * 100
        else:
            global_max_capacity = (global_max_capacity // 500 + 1) * 500

    return global_max_capacity

def filter_key_cycles(data_df_discharge, data_df_charge, unique_cycles, key_cycles):
    # Filter the data for the key cycles specified by the user
    data_df_discharge_filtered = data_df_discharge[data_df_discharge['Cycle'].isin(key_cycles)]
    data_df_charge_filtered = data_df_charge[data_df_charge['Cycle'].isin(key_cycles)]
    unique_cycles_filtered = [c for c in unique_cycles if c in key_cycles]
    return data_df_discharge_filtered, data_df_charge_filtered, unique_cycles_filtered

def calculate_common_y_axis(data, sample_parameters):
    # Function used in half Cell profile, calculate maximum capacity and efficiency across all datasets
    #need to input whole data set dictionary
    global_max_capacity_val = 0
    global_max_efficiency_val = 0

    def get_max_capacity_per_cycle(data_df_cleaned, step_type):
        max_capacity = data_df_cleaned.groupby('Cycle')[f'{step_type}_Capacity'].max()
        return max_capacity
        
    for filename, data_df in data.items():
        # data_df_cleaned, data_df_discharge, data_df_charge, unique_cycles = process_voltage_profile_data(data_df, filename)
        data_df_discharge = data_df[data_df['Step'] == "Discharge"]
        data_df_charge = data_df[data_df['Step'] == "Charge"]

        electrode_type = sample_parameters.get(filename, {}).get("electrode_type", "Positive(Cathode)")
        # Relies on session state for electrode type, not ideal but avoids having to input manually elsewhere. Change this later. Defaults to positive if none found
        # electrode_type = st.session_state.get("sample_parameters", {}).get(filename, {}).get("electrode_type", "Positive (Cathode)")
        
        # Calculate max capacity section

        discharge_caps = get_max_capacity_per_cycle(data_df_discharge, 'Discharge')
        charge_caps = get_max_capacity_per_cycle(data_df_charge, 'Charge')

        current_max_capacity = max(discharge_caps.max(), charge_caps.max()) if not discharge_caps.empty and not charge_caps.empty else 0
            
        # Update global max capacity
        if not pd.isna(current_max_capacity):
            global_max_capacity_val = max(global_max_capacity_val, current_max_capacity)

        # Calculate efficiencies for current dataset to find max efficiency
        capacity_per_cycle = pd.DataFrame({
            'Cycle': discharge_caps.index.union(charge_caps.index).sort_values(),
            'Discharge_Capacity': discharge_caps,
            'Charge_Capacity': charge_caps
        }).set_index('Cycle')        

        # Calculate max efficiency while handling potential issues with missing or zero capacities
        efficiency = []
        for cycle in capacity_per_cycle.index:
            charge_cap = capacity_per_cycle.loc[cycle, 'Charge_Capacity']
            discharge_cap = capacity_per_cycle.loc[cycle, 'Discharge_Capacity']
            if cycle < 2:
                efficiency.append(float('nan'))  # Skip efficiency calculation for the first cycle
            elif pd.isna(charge_cap) or pd.isna(discharge_cap) or charge_cap == 0:
                efficiency.append(float('nan'))  # Handle cases with missing or zero charge capacity
            elif electrode_type.lower() == 'negative(anode)':
                efficiency.append((discharge_cap / charge_cap) * 100)
            else:
                efficiency.append((charge_cap / discharge_cap) * 100)

        capacity_per_cycle['efficiency'] = efficiency
        cycle_efficiency = capacity_per_cycle.dropna(subset=['efficiency'])

        if not cycle_efficiency.empty:
            global_max_efficiency_val = max(global_max_efficiency_val, cycle_efficiency['efficiency'].max()) 

    # Add a small buffer and round up for better visualization for capacity
    if global_max_capacity_val > 0:
        if global_max_capacity_val <= 100:
            global_max_capacity_val = (global_max_capacity_val // 10 + 1) * 10
        elif global_max_capacity_val <= 500:
            global_max_capacity_val = (global_max_capacity_val // 50 + 1) * 50
        elif global_max_capacity_val <= 1000:
            global_max_capacity_val = (global_max_capacity_val // 100 + 1) * 100
        else:
            global_max_capacity_val = (global_max_capacity_val // 500 + 1) * 500
        
        # # Ensure efficiency max is at least 100, and typically not much more than 100-105%
        # global_max_efficiency_val = min(110, max(100, global_max_efficiency_val * 1.05))        



    return global_max_capacity_val, global_max_efficiency_val

def half_cell_calculations(data_df, electrode_type, filename):
    # Get cleaned and processed voltage data. Not all is needed, but function is already set up
    # data_df_cleaned, data_df_discharge, data_df_charge, unique_cycles = process_voltage_profile_data(data_df, filename)
    data_df_discharge = data_df[data_df['Step'] == "Discharge"]
    data_df_charge = data_df[data_df['Step'] == "Charge"]


    def get_max_capacity_per_cycle(df_in, step_type):
        max_capacity = df_in.groupby('Cycle')[f'{step_type}_Capacity'].max()
        return max_capacity
    
    discharge_caps = get_max_capacity_per_cycle(data_df_discharge, 'Discharge')
    charge_caps = get_max_capacity_per_cycle(data_df_charge, 'Charge')

    #Create this into a single dataframe for easier plotting
    capacity_per_cycle = pd.DataFrame({
        'Cycle': discharge_caps.index.union(charge_caps.index).sort_values(),
        'Discharge_Capacity': discharge_caps,
        'Charge_Capacity': charge_caps
    }).set_index('Cycle')

    #Calculate efficiency while handling potential issues with missing or zero capacities
    efficiency = []
    max_cycle = capacity_per_cycle.index.max()
    for cycle in capacity_per_cycle.index:
        charge_cap = capacity_per_cycle.loc[cycle, 'Charge_Capacity']
        discharge_cap = capacity_per_cycle.loc[cycle, 'Discharge_Capacity']
        if cycle < 2 or cycle ==max_cycle:
            efficiency.append(float('nan'))  # Skip efficiency calculation for the first cycle
        elif pd.isna(charge_cap) or pd.isna(discharge_cap) or charge_cap < 0.001 or discharge_cap < 0.001:
            efficiency.append(float('nan'))  # Handle cases with missing or zero charge capacity
        elif electrode_type.lower() == 'negative(anode)':
            efficiency.append((discharge_cap / charge_cap) * 100)
        else:
            efficiency.append((charge_cap / discharge_cap) * 100)

    capacity_per_cycle['efficiency'] = efficiency
    # cycle_eff = capacity_per_cycle.dropna(subset=['efficiency']).reset_index()

    voltage_min = min(data_df_discharge['Voltage'].min(), data_df_charge['Voltage'].min())
    voltage_max = max(data_df_discharge['Voltage'].max(), data_df_charge['Voltage'].max())

    return capacity_per_cycle.reset_index(), voltage_min, voltage_max

def comparitive_capacity_calculations(data_dfs, params):
    processed_plot_data = {}

    # Store global variables needed for caption/axes
    metadata = {
        'voltage_min': None,
        'voltage_max': None,
        'max_cycles': None,
        'caption_parts': [],
        'error': None       
    }

    for filename, data_df in data_dfs.items():
        # Get composition
        composition = params.get(filename, {}).get('composition', 'Unknown')
        # Clean Data
        # data_df_cleaned, data_df_discharge, data_df_charge, unique_cycles = process_voltage_profile_data(data_df, filename)
        data_df_discharge = data_df[data_df['Step'] == "Discharge"]
        data_df_charge = data_df[data_df['Step'] == "Charge"]
        unique_cycles = sorted(data_df['Cycle'].unique())


        # Error Check
        if data_df_discharge.empty:
            metadata['error'] =  f"Discharge data is empty for {filename}"
            return None, metadata
        if not all(col in data_df_discharge.columns for col in ['Cycle', 'Discharge_Capacity']):
            metadata['error'] = f"Invalid data columns in {filename}"
            return None, metadata        

        # Calculate plotting data
        cycle_capacity = data_df_discharge.groupby('Cycle')['Discharge_Capacity'].max().reset_index()
        processed_plot_data[filename] = cycle_capacity

        # Update global Metadata
        current_voltage_min = min(data_df_discharge['Voltage'].min(), data_df_charge['Voltage'].min())
        current_voltage_max = max(data_df_discharge['Voltage'].max(), data_df_charge['Voltage'].max())
        current_max_cycles = max(unique_cycles) if unique_cycles else None

        if current_voltage_min is not None:
            metadata['voltage_min'] = current_voltage_min if metadata['voltage_min'] is None else min(metadata['voltage_min'], current_voltage_min)
        if current_voltage_max is not None:
            metadata['voltage_max'] = current_voltage_max if metadata['voltage_max'] is None else max(metadata['voltage_max'], current_voltage_max)
        if current_max_cycles is not None:
             metadata['max_cycles'] = current_max_cycles if metadata['max_cycles'] is None else max(metadata['max_cycles'], current_max_cycles)  

        metadata['caption_parts'].append(f"{composition} (markers)")

    return processed_plot_data, metadata

def comparitive_percent_capacity_calculations(data_dfs, params, remove_outliers, outlier_percentage = None):
    processed_plot_data = {}
    metadata = {
        'max_retention':[],
        'legend_labels':{}
    }

    for filename, data_df in data_dfs.items():
        composition = params.get(filename, {}).get('composition', 'Unknown')
        electrode_type = params.get(filename, {}).get('electrode_type', 'Unknown')

        # Clean Data
        # data_df_cleaned, data_df_discharge, data_df_charge, unique_cycles = process_voltage_profile_data(data_df, filename)
        data_df_discharge = data_df[data_df['Step'] == "Discharge"]
        data_df_charge = data_df[data_df['Step'] == "Charge"]

        
        if data_df_discharge.empty or data_df_charge.empty: 
            continue # Skip if dataset empty

        # Build legend label
        voltage_min = min(data_df_discharge['Voltage'].min(), data_df_charge['Voltage'].min())
        voltage_max = max(data_df_discharge['Voltage'].max(), data_df_charge['Voltage'].max())
        voltage_range = f"{voltage_min:.2f}-{voltage_max:.2f} V" if electrode_type.lower() == 'positive(cathode)' else f"{voltage_max:.2f}-{voltage_min:.2f} V"
        metadata['legend_labels'][filename] = f"{composition} ({voltage_range})"

        # Calculate raw retention
        data_df_discharge_cycles = data_df_discharge.sort_values(by='Cycle').reset_index(drop=True)
        initial_discharge_capacity = None
        discharge_capacity_retention = []
        cycles = []

        for cycle, data in data_df_discharge_cycles.groupby('Cycle'):
            max_discharge_capacity = data['Discharge_Capacity'].max()
            if initial_discharge_capacity is None and max_discharge_capacity > 0:
                initial_discharge_capacity_window = data_df_discharge_cycles[data_df_discharge_cycles['Cycle'] <= 5]['Discharge_Capacity']
                if not initial_discharge_capacity_window.empty:
                    initial_discharge_capacity = initial_discharge_capacity_window.max()
                elif max_discharge_capacity > 0:
                    initial_discharge_capacity = max_discharge_capacity # Fallback to first non-zero capacity if first 5 cycles are empty or zero
            
            if initial_discharge_capacity is not None and max_discharge_capacity > 0:
                retention = (max_discharge_capacity / initial_discharge_capacity) * 100
                discharge_capacity_retention.append(retention)
                cycles.append(cycle)           

        retention_df = pd.DataFrame({'Cycle': cycles, 'Discharge Capacity Retention (%)': discharge_capacity_retention}) # create a df with info just calculated

        ## ------------------------------------- Outlier removal section ------------------------------------- ##    
        if not retention_df.empty and remove_outliers == True:
            # Remove outliers if toggled on
            filtered_retention = []
            filtered_cycles = []
            
            # Always include data points from cycle 1 to 5
            initial_cycles_data = retention_df[retention_df['Cycle'] <= 5]
            filtered_retention.extend(initial_cycles_data['Discharge Capacity Retention (%)'].tolist())
            filtered_cycles.extend(initial_cycles_data['Cycle'].tolist())

            outlier_cycle_data = retention_df[retention_df['Cycle'] >= 6].copy().reset_index(drop=True) # Get data from cycle 6 onwards for outlier detection

            if outlier_cycle_data.shape[0] > 2: # Need at least 3 data points
                previous_retention = outlier_cycle_data['Discharge Capacity Retention (%)'].iloc[0]
                filtered_retention.append(previous_retention)
                filtered_cycles.append(outlier_cycle_data['Cycle'].iloc[0])


                for j in range(1, outlier_cycle_data.shape[0] - 1):
                    current_retention = outlier_cycle_data['Discharge Capacity Retention (%)'].iloc[j]
                    next_retention = outlier_cycle_data['Discharge Capacity Retention (%)'].iloc[j + 1]

                    if previous_retention > 0 and next_retention >0:
                        if (abs(current_retention - previous_retention) / previous_retention * 100 <= outlier_percentage) and (abs(next_retention - current_retention) / current_retention * 100 <= outlier_percentage):
                            filtered_retention.append(current_retention)
                            filtered_cycles.append(outlier_cycle_data['Cycle'].iloc[j])
                           
                    previous_retention = current_retention  # Update previous retention for next iteration    

                if outlier_cycle_data.shape[0] > 1:
                    filtered_retention.append(outlier_cycle_data['Discharge Capacity Retention (%)'].iloc[-1])
                    filtered_cycles.append(outlier_cycle_data['Cycle'].iloc[-1])
                elif outlier_cycle_data.shape[0] > 0:
                    filtered_retention.extend(outlier_cycle_data['Discharge Capacity Retention (%)'].tolist())
                    filtered_cycles.extend(outlier_cycle_data['Cycle'].tolist())

            filtered_retention_df = pd.DataFrame({'Cycle': filtered_cycles, 'Discharge Capacity Retention (%)': filtered_retention}).sort_values(by='Cycle').reset_index(drop=True)            
            plot_df = filtered_retention_df
        else:
            plot_df = retention_df
        
        if not plot_df.empty:
            processed_plot_data[filename] = plot_df
            metadata['max_retention'].append(plot_df['Discharge Capacity Retention (%)'].max())
    
    return processed_plot_data, metadata

def calculate_capacity_fade_rate(data_dfs, params):
    
    fade_rate_data = {}
    compositions = set()

    # Loop over each df in dictionary to get cycle data/ percentage lost
    for filename, data_df in data_dfs.items():
        composition = params.get(filename, {}).get('composition', 'Unknown')
        compositions.add(composition)
        # data_df_cleaned, data_df_discharge, data_df_charge, unique_cycles = process_voltage_profile_data(df, filename)
        data_df_discharge = data_df[data_df['Step'] == "Discharge"]



        if 'Cycle' in data_df_discharge.columns and 'Capacity(Ah)' in data_df_discharge.columns:
            # Find capacity at first stable cycle
            first_stable_capacity = data_df_discharge.groupby('Cycle')['Capacity(Ah)'].mean().loc[data_df_discharge['Cycle'].min()]
            capacity_vs_cycle = data_df_discharge.groupby('Cycle')['Capacity(Ah)'].mean().reset_index()
            capacity_vs_cycle['Capacity Loss (Ah)'] = first_stable_capacity - capacity_vs_cycle['Capacity(Ah)']
            capacity_vs_cycle['Percentage Capacity Loss'] = (capacity_vs_cycle['Capacity Loss (Ah)'] / first_stable_capacity) * 100

            # Calculate percentage loss per cycle
            capacity_vs_cycle['Percentage Loss per Cycle'] = capacity_vs_cycle['Percentage Capacity Loss'].diff() 
            capacity_vs_cycle['Percentage Loss per 100 Cycles'] = \
                capacity_vs_cycle['Percentage Capacity Loss'].rolling(window=100, min_periods=1).apply(
                    lambda x: (x.iloc[-1] - x.iloc[0]) if len(x) > 1 else np.nan, raw=False)


            capacity_vs_cycle['Composition'] = composition
            fade_rate_data[filename] = capacity_vs_cycle
        else:

            raise ValueError(f"Data for {filename} is missing required columns for capacity fade rate calculation.")
        
    return fade_rate_data, compositions

def calculate_power_density(data_dfs, params):
    min_capacity, max_capacity = calculate_global_max_min_cap_key(data_dfs, params)
    compositions = set()
    power_energy_data = {}

    for filename, data_df in data_dfs.items():
        # data_df_cleaned, data_df_discharge, data_df_charge, unique_cycles = process_voltage_profile_data(df, filename)
        data_df_discharge = data_df[data_df['Step'] == "Discharge"]


        composition = params.get(filename, {}).get('composition', 'Unknown')
        compositions.add(composition)
        active_material_mass_mg = params.get(filename, {}).get('active_material_mass_mg', 'Unknown')
        active_material_mass_g = active_material_mass_mg / 1000

        valid_discharge = data_df_discharge[['Cycle', 'Specific_Energy', 'Power']].copy()
        if not valid_discharge.empty:
            valid_discharge['Abs_Power_W'] = valid_discharge['Power'].abs()
            max_abs_power_per_cycle = valid_discharge.groupby('Cycle')['Abs_Power_W'].max()

            # Find the overall maximum absolute power for this dataset
            overall_max_abs_power = max_abs_power_per_cycle.max() if not max_abs_power_per_cycle.empty else 0

            # Handle potential negative energy values during discharge (if necessary)
            if (valid_discharge['Specific_Energy'] < 0).any():
                valid_discharge['Abs_Spec_Energy_mWh_g'] = valid_discharge['Specific_Energy'].abs()
                max_energy_per_cycle = valid_discharge.groupby('Cycle')['Abs_Spec_Energy_mWh_g'].max()
            else:
                max_energy_per_cycle = valid_discharge.groupby('Cycle')['Specific_Energy'].max()

            power_energy_data[filename] = pd.DataFrame({
                'Cycle': max_energy_per_cycle.index,
                'Max_Specific_Energy_mWh_g': max_energy_per_cycle.values,
                'Max_Power_W': max_abs_power_per_cycle.values,
                'Overall_Max_Abs_Power': overall_max_abs_power # Store for conditional formatting
            })
            if active_material_mass_g is not None:
                power_energy_data[filename]['Max_Power_W_g'] = power_energy_data[filename]['Max_Power_W'] / active_material_mass_g

    return power_energy_data

def calculate_global_max_min_cap_key(data_dfs, params):
    all_min_capacity_key_cycles = None
    all_max_capacity_key_cycles = None

    for filename, data_df in data_dfs.items():
        # data_df_cleaned, data_df_discharge, data_df_charge, unique_cycles = process_voltage_profile_data(df, filename)

        key_cycles = params.get(filename, {}).get('key_cycles')
        data_key_cycle = data_df[data_df['Cycle'].isin(key_cycles)]

        if not data_key_cycle.empty:
            min_capacity = min(data_key_cycle['Discharge_Capacity'].min(), data_key_cycle['Charge_Capacity'].min())
            max_capacity = max(data_key_cycle['Discharge_Capacity'].max(), data_key_cycle['Charge_Capacity'].max())
            all_min_capacity_key_cycles = min(all_min_capacity_key_cycles, min_capacity) if all_min_capacity_key_cycles is not None else min_capacity
            all_max_capacity_key_cycles = max(all_max_capacity_key_cycles, max_capacity) if all_max_capacity_key_cycles is not None else max_capacity
    return all_min_capacity_key_cycles, all_max_capacity_key_cycles

def calculate_dq_dv(data_df, apply_smoothing = False, shared_params=None):
    df_filtered = data_df.copy()

    # Cut off extremes of data first
    min_v = df_filtered['Voltage'].min() + 0.05
    max_v = df_filtered['Voltage'].max() - 0.05
    df_filtered = df_filtered[(df_filtered['Voltage'] >= min_v) & (df_filtered['Voltage'] <= max_v)]

    if apply_smoothing and shared_params is not None:
        # Smoothing/Spike removal Parameters
        smoothing_window = shared_params.get('smoothing_window', None)
        polyorder = shared_params.get('polyorder', 2)
        spike_removal = shared_params.get('spike_removal', False)
        spike_window_size = shared_params.get('spike_window_size', 3)
        spike_threshold_multiplier = shared_params.get('spike_threshold_multiplier', 3)

        # --- Spike Removal and Imputation ---
        def remove_and_impute_spikes(df_in, value_col='dQ/dV', voltage_col='Voltage', window_size=3, threshold_multiplier=3):
            df = df_in.copy()
            rolling_mean = df[value_col].rolling(window=window_size, center=True, min_periods=1).mean()
            rolling_std = df[value_col].rolling(window=window_size, center=True, min_periods=1).std()
            abs_diff = (df[value_col] - rolling_mean).abs()
            spike_indices = abs_diff > (threshold_multiplier * rolling_std)
            num_spikes = spike_indices.sum()
            
            # Impute spikes with rolling mean
            df.loc[spike_indices, value_col] = rolling_mean[spike_indices]
            return df, num_spikes
        num_spikes = None
        if spike_removal:
            df_filtered, num_spikes = remove_and_impute_spikes(
                    df_filtered.copy(),
                    window_size=spike_window_size,
                    threshold_multiplier=spike_threshold_multiplier
                    )
        # Apply smoothing to dQ/dV analysis
        if smoothing_window is not None and smoothing_window > 1 and len(df_filtered) > smoothing_window:
            df_filtered['dQ/dV_Smoothed'] = savgol_filter(df_filtered['dQ/dV'],smoothing_window, polyorder )
        else: 
            # Fallback, if smoothing window is larger than dataset, just return dQ.dV without smoothing to avoid errors
            df_filtered['dQ/dV_Smoothed'] = df_filtered['dQ/dV']
        # If smoothing, return both
        return df_filtered, num_spikes


    # if not smoothing, return just filtered df
    return df_filtered
