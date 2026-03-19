import pandas as pd
import numpy as np

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


"""
DOCSTRING

Returns a dataframe
"""
def aggregate_surveys(df_surveys, verbose=False):
        
    # ----------------------------------------------------------------
    # If the surveys csv ever gets corrupted, redownload V_OM_WORK_TASK_SURVEYS.csv 
    # from the box and run the code below.
    # ----------------------------------------------------------------

    # Define aggregation dictionary
    # Drop SURVEY_QUESTION_ID, SURVEY_QUESTION, SURVEY_TYPE, SURVEY_STATUS
    # Aggregate RESPONSE_COMMENTS into a single column
    aggregation_rules = {
        'AVERAGE_SURVEY_SCORE': ('SURVEY_SCORES', 'mean'), # Renamed key to match output column name directly
        'WORK_TASK_NAME': ('WORK_TASK_NAME', 'first'),
        'WORK_TASK_STATUS': ('WORK_TASK_STATUS', 'first'),
        'RESPONSIBLE_ORGANIZATION': ('RESPONSIBLE_ORGANIZATION', 'first'),
        'RESPONSIBLE_PERSON': ('RESPONSIBLE_PERSON', 'first'),
        'SERVICE_REQUEST_ID': ('SERVICE_REQUEST_ID', 'first'),
        'SURVEY_SENT_DATE': ('SURVEY_SENT_DATE', 'first'),
        'SURVEY_COMMENTS': ('SURVEY_COMMENTS', 'first'), # Keep original SURVEY_COMMENTS
        'SURVEY_RESPONSE': ('SURVEY_RESPONSE', 'first'),
        'RESPONSE_COMMENTS': ('RESPONSE_COMMENTS', lambda x: '. '.join(x.dropna().astype(str).unique()) if x.dropna().any() else np.nan),
        'SURVEY_QUESTION_DESC': ('SURVEY_QUESTION_DESC', 'first'),
        'BUILDING': ('BUILDING', 'first'),
        'FLOOR': ('FLOOR', 'first'),
        'REQUEST_CLASS': ('REQUEST_CLASS', 'first')
    }

    # Group by 'WORK_TASK_ID' and apply the aggregation rules
    df_surveys_agg = df_surveys.groupby('WORK_TASK_ID').agg(**aggregation_rules).reset_index()

    # The AVERAGE_SURVEY_SCORE column is already named correctly by using named aggregation

    if verbose:
        print(f"Shape of df_surveys_agg: {df_surveys_agg.shape}")
        print("First 5 rows of df_surveys_agg:")
        print(f"Shape of df_surveys_agg: {df_surveys_agg.shape}")
        display(df_surveys_agg.head())

    return df_surveys_agg

"""
DOCSTRING
"""
def merge_tickets_assets_surveys(df_tickets_assets, df_surveys_agg, verbose=False):

    # Merge the dataframes
    df_tickets_assets_surveys = pd.merge(df_tickets_assets, df_surveys_agg, on='WORK_TASK_ID', how='inner')

    if verbose:
        print(f"Original shape of merged and filtered DataFrame: {df_tickets_assets_surveys.shape}")
        print(f"SHAPE: {df_tickets_assets_surveys.shape}")

    # Ensure BASELINE_START_LTZ is a datetime object
    if not pd.api.types.is_datetime64_any_dtype(df_tickets_assets_surveys['BASELINE_START_LTZ']):
        df_tickets_assets_surveys['BASELINE_START_LTZ'] = pd.to_datetime(df_tickets_assets_surveys['BASELINE_START_LTZ'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')

    if verbose:
        print(f"SHAPE after initial filter and before NaT drop: {df_tickets_assets_surveys.shape}")

    # Optional: remove rows where BASELINE_START_LTZ contains NaT values
    # df_tickets_assets_surveys.dropna(subset=['BASELINE_START_LTZ'], inplace=True)

    if verbose:
        print(f"Shape of tickets/assets joined DataFrame: {df_tickets_assets.shape}")
        print(f"Shape of surveys_cleaned: {df_surveys_agg.shape}")
        print(f"Final shape of merged and filtered DataFrame: {df_tickets_assets_surveys.shape}")
        print(f"Columns in merged and filtered DataFrame: {df_tickets_assets_surveys.columns.tolist()}")
        print("Merged, filtered, and cleaned df_tickets_assets_surveys dataframe.")

    return df_tickets_assets_surveys


def convert_cols_to_datetime(df):
    date_columns = [
        'BASELINE_START_LTZ', 'BASELINE_END_LTZ', 'ASSIGNED_DATE_LTZ',
        'PLANNED_START_LTZ', 'PLANNED_END_LTZ', 'PLANNED_FOLLOW_UP_DATE_LTZ',
        'ACTUAL_START_LTZ', 'ACTUAL_END_LTZ', 'CREATE_DATE_LTZ'
    ]

    missing_cols = [col for col in date_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns in dataframe: {missing_cols}")

    for col in date_columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    
    return df


def merge_tickets_locations(df_tickets, df_locations, verbose=False):
    """
    Merges df_tickets with df_locations using an inner join.
    
    Parameters:
    -----------
    df_tickets : pd.DataFrame
        DataFrame containing ticket data with a 'BUILDING' column
    df_locations : pd.DataFrame
        DataFrame containing location data with a 'FEP_BUILDING_DESC' column
    verbose : bool, optional
        If True, prints information about the merge
        
    Returns:
    --------
    pd.DataFrame
        Inner joined DataFrame with all columns from both dataframes
    """
    
    merged_df = pd.merge(
        df_tickets,
        df_locations,
        left_on='BUILDING',
        right_on='FEP_BUILDING_DESC',
        how='inner'
    )
    
    if verbose:
        print(f"Original tickets: {len(df_tickets)} rows")
        print(f"Original locations: {len(df_locations)} rows")
        print(f"Merged result: {len(merged_df)} rows")
    
    return merged_df


def download_df_csv(df, output_csv_filepath):
    df.to_csv(output_filepath, index=False)
    print(f"'{df}' has been successfully saved to '{output_csv_filepath}'")
