import streamlit as st
import pandas as pd
import warnings


def load_data(files):
    # Load data from the uploaded file
    #INPUT: List of UploadedFile objects
    #RETURNS: Dictionary of DataFrames, with filename as key and dataframe as value
    data_dfs = {}
    with warnings.catch_warnings():
        for file in files:
            warnings.simplefilter("ignore", UserWarning)
            df = pd.read_excel(file, sheet_name='record', header=0)
            filename = file.name
            data_dfs[filename] = df
    return data_dfs


@st.cache_data
def process_data(df, filename=None):
    # Process step column data uploaded. 
    # Standardise charge/discharge step names, remove step type 'Rest'
    # Rename columns to standard names
    # Processing voltage data, ensuring numbers, removing NaNs
    # INPUT: DataFrame
    # RETURNS: PD DataFrame
    
    if 'Step Type' not in df.columns:
        raise ValueError (f"'{filename}' does not contain a 'Step Type' column.")
    
    data_processed = df.copy()
    # ------- Standardise step names in step column -------
    data_processed['Step Type'] = data_processed['Step Type'].astype(str).str.strip()

    step_replacements = {
        'CCCV Chg': 'Charge',
        'CC DChg': 'Discharge',
        'CCCV CHG': 'Charge',
        'CC DCHG': 'Discharge',
        'Charge ': 'Charge',
        'Discharge ': 'Discharge'
    }
    for old, new in step_replacements.items():
        data_processed['Step Type'] = data_processed['Step Type'].replace(old, new, regex=False)

    data_processed = data_processed[data_processed['Step Type'] != 'Rest'].copy()
    data_processed.reset_index(drop=True, inplace=True)


    # ------- Rename columns to standard names -------
    columns_to_extract = {
    'Cycle Index': 'Cycle',
    'Step Type': 'Step',
    'Voltage(V)': 'Voltage',
    'Capacity(Ah)': 'Capacity(Ah)',
    'Spec. Energy(mWh/g)': 'Specific_Energy',
    'Chg. Spec. Cap.(mAh/g)': 'Charge_Capacity',
    'DChg. Spec. Cap.(mAh/g)': 'Discharge_Capacity',
    'Power(W)': 'Power',
    'dQm/dV(mAh/V.g)': 'dQ/dV'
    }

    # ------- Check if all columns are existing before renaming -------
    missing_cols = [col for col in columns_to_extract.keys() if col not in data_processed.columns]

    if missing_cols:
        error_msg = (f"Error processing '{filename}'. Missing required columns: {missing_cols}. "
                     f"Available columns are: {data_processed.columns.tolist()}")
        raise ValueError(error_msg)

    data_processed = data_processed.rename(columns=columns_to_extract, inplace=False)
    # Filter dataframe to only include these renamed columns:
    data_processed = data_processed[list(columns_to_extract.values())]

    # ------- Process Voltage Numerical Data -------

    # Voltage Data columns to process
    numeric_cols = ['Voltage', 'Charge_Capacity', 'Discharge_Capacity', 'Specific_Energy', 'Cycle', 'Power']
    for col in numeric_cols:
        data_processed[col] = pd.to_numeric(data_processed[col], errors = 'coerce')

    # Drop rows where any of the critical numeric columns OR the step column are NaN
    data_processed = data_processed.dropna(subset=numeric_cols + ['Step'])

    return data_processed

def calculate_cycle_data(df):
    """
    Calculates cycle-related data from a DataFrame, including cycle capacity and efficiency.
        Handles missing columns.

    Returns:
    - DataFrame: A DataFrame containing the calculated cycle data,
                    or an empty DataFrame if required columns are missing.
    """
    required_columns = ['Cycle', 'Charge_Capacity', 'Discharge_Capacity']
    if not all(col in df.columns for col in required_columns):
        st.info("  Warning: Required columns for cycle data calculation are missing.")
        return pd.DataFrame()  # Return an empty DataFrame

    # Group by 'Cycle' and calculate mean charge and discharge capacities
    cycle_data = df.groupby('Cycle').agg({
        'Charge_Capacity': 'mean',
        'Discharge_Capacity': 'mean'
    }).reset_index()

    # Calculate Coulombic efficiency, handling potential division by zero
    cycle_data['efficiency'] = (cycle_data['Discharge_Capacity'] / cycle_data['Charge_Capacity']) * 100
    cycle_data['efficiency'] = cycle_data['efficiency'].replace([float('inf'), -float('inf')], 0)  # Replace infinities with 0

    return cycle_data

def figure_to_bytes(fig, file_format = "png"):
    # Convert a Matplotlib figure to bytes for downloading
    import io
    buf = io.BytesIO()
    fig.savefig(buf, format=file_format, bbox_inches='tight',dpi = 300)
    buf.seek(0)
    return buf



# @st.cache_data
# def process_voltage_profile_data(data_df, filename):
#     # Placeholder for any specific processing needed for voltage profile data
#     # Currently, we assume the data is already in the correct format after processing in data_processing.py, however this is just generic
#     df =data_df.copy()
#     # Convert capacity and voltage to numeric
#     df['Voltage'] = pd.to_numeric(df['Voltage'], errors='coerce')
#     df['Charge_Capacity'] = pd.to_numeric(df['Charge_Capacity'], errors='coerce')
#     df['Discharge_Capacity'] = pd.to_numeric(df['Discharge_Capacity'], errors='coerce')
#     df['Cycle'] = pd.to_numeric(df['Cycle'], errors='coerce')

#     # Drop rows with NaN
#     data_df_cleaned = df.dropna(subset=['Voltage', 'Charge_Capacity', 'Discharge_Capacity', 'Cycle', 'Step'])

#     # Separate charge and discharge data_df
#     data_df_discharge = data_df_cleaned[data_df_cleaned['Step'] == 'Discharge']
#     data_df_charge = data_df_cleaned[data_df_cleaned['Step'] == 'Charge']

#     # Determine unique cycles
#     unique_cycles = sorted(data_df_cleaned['Cycle'].unique())   

#     #I dont think data_df_cleaned is used, so not including it in return for now, but we can always add it back in if needed.
#     return data_df_cleaned, data_df_discharge, data_df_charge, unique_cycles

