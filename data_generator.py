import pandas as pd
import numpy as np

"""
DOCSTRING
"""
def df_convert_to_datetimes(df_tickets_assets):
    # List of date columns to convert and format
    date_columns = [
        'BASELINE_START_LTZ', 'BASELINE_END_LTZ', 'ASSIGNED_DATE_LTZ',
        'PLANNED_START_LTZ', 'PLANNED_END_LTZ', 'PLANNED_FOLLOW_UP_DATE_LTZ',
        'ACTUAL_START_LTZ', 'ACTUAL_END_LTZ', 'CREATE_DATE_LTZ'
    ]

    # Convert and format date columns
    for col in date_columns:
        # Ensure column is first converted to datetime
        df_tickets_assets[col] = pd.to_datetime(df_tickets_assets[col], errors='coerce')
        # Format datetime objects to the right string format
        df_tickets_assets[col] = df_tickets_assets[col].dt.strftime('%Y-%m-%d %H:%M:%S.%f').replace({np.nan: ''})

    # Convert WORK_TASK_ID to integer type before saving
    # df_tickets_assets['WORK_TASK_ID'] = df_tickets_assets['WORK_TASK_ID'].astype(int)
    bad_values = df_tickets_assets[pd.to_numeric(df_tickets_assets['WORK_TASK_ID'], errors='coerce').isna()]['WORK_TASK_ID'].unique()
    print(bad_values)
    # df_tickets_assets['WORK_TASK_ID'] = df_tickets_assets['WORK_TASK_ID'].astype('Int64')


"""
DOCSTRING
"""
def merge_tickets_assets(df_tickets, df_assets, verbose=False):
    # Convert WORK_TASK_ID to integers
    df_tickets['WORK_TASK_ID'] = pd.to_numeric(df_tickets['WORK_TASK_ID'], errors='coerce')
    df_assets['WORK_TASK_ID'] = pd.to_numeric(df_assets['WORK_TASK_ID'], errors='coerce')

    # Drop rows where WORK_TASK_ID became NaN after coercion
    df_tickets.dropna(subset=['WORK_TASK_ID'], inplace=True)
    df_assets.dropna(subset=['WORK_TASK_ID'], inplace=True)
    
    # 1. Merge df_tickets and df_assets on WORK_TASK_ID (optional prints)
    if verbose:
        print(f"Shape of df_tickets: {df_tickets.shape}")
        print(f"Number of unique WORK_TASK_ID in df_tickets: {df_tickets['WORK_TASK_ID'].nunique()}")
        print(f"Shape of df_assets: {df_assets.shape}")
        print(f"Number of unique WORK_TASK_ID in df_assets: {df_assets['WORK_TASK_ID'].nunique()}")

    # Check for duplicate WORK_TASK_ID in df_assets that would cause row expansion
    duplicate_assets_work_task_ids_count = df_assets[df_assets.duplicated(subset=['WORK_TASK_ID'], keep=False)]['WORK_TASK_ID'].nunique()
    total_rows_with_duplicate_work_task_id_in_assets = df_assets[df_assets.duplicated(subset=['WORK_TASK_ID'], keep=False)].shape[0]

    if verbose:
        print(f"Number of WORK_TASK_ID values appearing more than once in df_assets: {duplicate_assets_work_task_ids_count}")
        print(f"Total number of rows in df_assets involved in duplicate WORK_TASK_ID entries: {total_rows_with_duplicate_work_task_id_in_assets}")

    df_tickets_assets = pd.merge(df_tickets, df_assets, on='WORK_TASK_ID', how='inner', suffixes=('_ticket', '_asset'))

    if verbose:
        print(f"Shape of df_tickets_assets after inner merge: {df_tickets_assets.shape}")

    # --- Apply requested data type and format fixes to df_tickets_assets ---
    # Convert WORK_TASK_ID to integer type (Pandas nullable integer to handle NaNs)
    df_tickets_assets['WORK_TASK_ID'] = df_tickets_assets['WORK_TASK_ID'].astype('Int64')

    # Convert PLANNED_WORKING_DAYS to integer type
    df_tickets_assets['PLANNED_WORKING_DAYS'] = df_tickets_assets['PLANNED_WORKING_DAYS'].astype('Int64')

    # List of date columns to convert and format
    date_columns = [
        'BASELINE_START_LTZ', 'BASELINE_END_LTZ', 'ASSIGNED_DATE_LTZ',
        'PLANNED_START_LTZ', 'PLANNED_END_LTZ', 'PLANNED_FOLLOW_UP_DATE_LTZ',
        'ACTUAL_START_LTZ', 'ACTUAL_END_LTZ', 'CREATE_DATE_LTZ'
    ]

    # Convert and format date columns
    for col in date_columns:
        # Ensure column is first converted to datetime, coercing errors
        df_tickets_assets[col] = pd.to_datetime(df_tickets_assets[col], errors='coerce')
        # Format datetime objects to the desired string format, leave NaT as NaN (which will be empty string in CSV)
        df_tickets_assets[col] = df_tickets_assets[col].dt.strftime('%Y-%m-%d %H:%M:%S.%f').replace({np.nan: ''})
    
    return df_tickets_assets
