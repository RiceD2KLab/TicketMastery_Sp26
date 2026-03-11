import pandas as pd
import numpy as np

######################################################
### Generating Merged Tickets & Assets (& surveys) ###
######################################################

# Load files
df_tickets = pd.read_csv("/content/V_OM_WORK_TASK.csv")
df_assets = pd.read_csv("/content/V_OM_WORK_TASK_ASSET.csv")
df_surveys_cleaned = pd.read_csv("/content/surveys_cleaned.csv")

# Optional: Check if the rows and columns have the right format: 
df_tickets.head()
df_assets.head()
df_surveys_cleaned.head()

# Ensure WORK_TASK_ID columns are numeric before merging and unique counts
df_tickets['WORK_TASK_ID'] = pd.to_numeric(df_tickets['WORK_TASK_ID'], errors='coerce')
df_assets['WORK_TASK_ID'] = pd.to_numeric(df_assets['WORK_TASK_ID'], errors='coerce')

# Drop rows where WORK_TASK_ID became NaN after coercion
df_tickets.dropna(subset=['WORK_TASK_ID'], inplace=True)

# Drop rows from df_assets where ASSET_ID is null (no value) or empty
df_assets.dropna(subset=['ASSET_ID'], inplace=True)

df_assets.dropna(subset=['WORK_TASK_ID'], inplace=True)

# 1. Merge df_tickets and df_assets on WORK_TASK_ID
print(f"Shape of df_tickets: {df_tickets.shape}")
print(f"Number of unique WORK_TASK_ID in df_tickets: {df_tickets['WORK_TASK_ID'].nunique()}")
print(f"Shape of df_assets: {df_assets.shape}")
print(f"Number of unique WORK_TASK_ID in df_assets: {df_assets['WORK_TASK_ID'].nunique()}")

# Check for duplicate WORK_TASK_ID in df_assets that would cause row expansion
duplicate_assets_work_task_ids_count = df_assets[df_assets.duplicated(subset=['WORK_TASK_ID'], keep=False)]['WORK_TASK_ID'].nunique()
total_rows_with_duplicate_work_task_id_in_assets = df_assets[df_assets.duplicated(subset=['WORK_TASK_ID'], keep=False)].shape[0]

print(f"Number of WORK_TASK_ID values appearing more than once in df_assets: {duplicate_assets_work_task_ids_count}")
print(f"Total number of rows in df_assets involved in duplicate WORK_TASK_ID entries: {total_rows_with_duplicate_work_task_id_in_assets}")

df_tickets_assets = pd.merge(df_tickets, df_assets, on='WORK_TASK_ID', how='inner', suffixes=('_ticket', '_asset'))

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
# --- End of fixes for df_tickets_assets ---


# 2. Now merge the result with df_surveys_avg
df_tickets_assets_surveys = pd.merge(df_tickets_assets, df_surveys_cleaned, on='WORK_TASK_ID', how='inner')

print(f"Original shape of merged and filtered DataFrame: {df_tickets_assets_surveys.shape}")
print(f"SHAPE: {df_tickets_assets_surveys.shape}")

# 3. Convert BASELINE_START_LTZ to datetime objects using corrected column name and explicit format
# Using a broader format or multiple formats if needed, or infer_datetime_format=True for mixed types.
# For now, let's try the user-provided format, but with errors='coerce' to see what remains.
if not pd.api.types.is_datetime64_any_dtype(df_tickets_assets_surveys['BASELINE_START_LTZ']):
    df_tickets_assets_surveys['BASELINE_START_LTZ'] = pd.to_datetime(df_tickets_assets_surveys['BASELINE_START_LTZ'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')

print(f"SHAPE after initial filter and before NaT drop: {df_tickets_assets_surveys.shape}")

# 4. Remove rows where BASELINE_START_LTZ contains NaT values
# df_tickets_assets_surveys.dropna(subset=['BASELINE_START_LTZ'], inplace=True)

print(f"Shape of tickets/assets joined DataFrame: {df_tickets_assets.shape}")
print(f"Shape of surveys_cleaned: {df_surveys_cleaned.shape}")
print(f"Final shape of merged and filtered DataFrame: {df_tickets_assets_surveys.shape}")
print(f"Final shape of tickets dataframe: {df_tickets.shape}")
print(f"Columns in merged and filtered DataFrame: {df_tickets_assets_surveys.columns.tolist()}")
print("Merged, filtered, and cleaned df_tickets_assets_surveys dataframe.")



## DOWNLOAD NEW FILES

# FOR df_merged_tickets_assets.csv
output_csv_filename_1 = 'df_merged_tickets_assets.csv'

# Convert WORK_TASK_ID to integer type before saving
# Using 'Int64' to allow for potential NaN values if any exist, otherwise 'int' could be used if no NaNs are present.
df_tickets_assets['WORK_TASK_ID'] = df_tickets_assets['WORK_TASK_ID'].astype('Int64')

df_tickets_assets.to_csv(output_csv_filename_1, index=False)

print(f"'df_merged_tickets_assets' has been successfully saved to '{output_csv_filename_1}'")

# FOR df_merged_tickets_assets_surveys.csv

output_csv_filename = 'df_merged_tickets_assets_surveys.csv'

# Convert WORK_TASK_ID to integer type before saving
# Using 'Int64' to allow for potential NaN values if any exist, otherwise 'int' could be used if no NaNs are present.
df_tickets_assets_surveys['WORK_TASK_ID'] = df_tickets_assets_surveys['WORK_TASK_ID'].astype('Int64')

df_tickets_assets_surveys.to_csv(output_csv_filename, index=False)

print(f"'df_merged_tickets_assets_surveys' has been successfully saved to '{output_csv_filename}'")


######################################################
########################  OLD  #######################
######################################################


# 1. Merge df_tickets and df_assets on WORK_TASK_ID
df_tickets_assets = pd.merge(df_tickets, df_assets, on='WORK_TASK_ID', how='inner', suffixes=('_ticket', '_asset'))

# 2. Now merge the result with df_surveys_avg
df_tickets_assets_surveys = pd.merge(df_tickets_assets, df_surveys_avg, on='WORK_TASK_ID', how='inner')

print(f"Original shape of merged and filtered DataFrame: {df_tickets_assets_surveys.shape}")
print(f"SHAPE: {df_tickets_assets_surveys.shape}")


# 4. Convert BASELINE_START_LTZ to datetime objects using corrected column name and explicit format
if not pd.api.types.is_datetime64_any_dtype(df_tickets_assets_surveys['BASELINE_START_LTZ']):
    df_tickets_assets_surveys['BASELINE_START_LTZ'] = pd.to_datetime(df_tickets_assets_surveys['BASELINE_START_LTZ'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')

print(f"SHAPE: {df_tickets_assets_surveys.shape}")

# 5. Remove rows where BASELINE_START_LTZ contains NaT values
# df_tickets_assets_surveys.dropna(subset=['BASELINE_START_LTZ'], inplace=True)

print(f"Shape of surveys_avg: {df_surveys_avg.shape}")
print(f"Shape of tickets/assets joined DataFrame: {df_tickets_assets.shape}")
print(f"Final shape of merged and filtered DataFrame: {df_tickets_assets_surveys.shape}")
print(f"Columns in merged and filtered DataFrame: {df_tickets_assets_surveys.columns.tolist()}")
print("Merged, filtered, and cleaned df_tickets_assets_surveys dataframe.")
display(df_surveys.head())