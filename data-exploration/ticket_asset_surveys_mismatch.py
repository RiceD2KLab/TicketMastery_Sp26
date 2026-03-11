
import pandas as pd

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
print("The increase in rows for df_tickets_assets compared to df_tickets is expected if there are multiple assets (rows in df_assets) linked to the same WORK_TASK_ID.")


# 2. Now merge the result with df_surveys_avg
df_tickets_assets_surveys = pd.merge(df_tickets_assets, df_surveys_avg, on='WORK_TASK_ID', how='inner')

print(f"Original shape of merged and filtered DataFrame: {df_tickets_assets_surveys.shape}")
print(f"SHAPE: {df_tickets_assets_surveys.shape}")


# 3. Convert BASELINE_START_LTZ to datetime objects using corrected column name and explicit format
# Using a broader format or multiple formats if needed, or infer_datetime_format=True for mixed types.
# For now, let's try the user-provided format, but with errors='coerce' to see what remains.
if not pd.api.types.is_datetime64_any_dtype(df_tickets_assets_surveys['BASELINE_START_LTZ']):
    df_tickets_assets_surveys['BASELINE_START_LTZ'] = pd.to_datetime(df_tickets_assets_surveys['BASELINE_START_LTZ'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')

print(f"SHAPE after initial filter and before NaT drop: {df_tickets_assets_surveys.shape}")

# 5. Remove rows where BASELINE_START_LTZ contains NaT values
df_tickets_assets_surveys.dropna(subset=['BASELINE_START_LTZ'], inplace=True)

print(f"Shape of tickets/assets joined DataFrame: {df_tickets_assets.shape}")
print(f"Shape of surveys_avg: {df_surveys_avg.shape}")
print(f"Final shape of merged and filtered DataFrame: {df_tickets_assets_surveys.shape}")
print(f"Final shape of tickets dataframe: {df_tickets.shape}")
print(f"Columns in merged and filtered DataFrame: {df_tickets_assets_surveys.columns.tolist()}")
print("Merged, filtered, and cleaned df_tickets_assets_surveys dataframe.")



# Get unique WORK_TASK_IDs from df_surveys_avg
work_task_ids_in_surveys_avg = set(df_surveys_avg['WORK_TASK_ID'].unique())

# Get unique WORK_TASK_IDs from df_tickets_assets
work_task_ids_in_tickets_assets = set(df_tickets_assets['WORK_TASK_ID'].unique())

# Find WORK_TASK_IDs that are in df_surveys_avg but NOT in df_tickets_assets
ids_only_in_surveys_avg = list(work_task_ids_in_surveys_avg - work_task_ids_in_tickets_assets)

print(f"WORK_TASK_IDs found in df_surveys_avg but NOT in df_tickets_assets: {ids_only_in_surveys_avg}")
print(f"Number of WORK_TASK_IDs found: {len(ids_only_in_surveys_avg)}")

if not ids_only_in_surveys_avg:
    print("As expected, all WORK_TASK_IDs from df_surveys_avg are present in df_tickets_assets.")
else:
    print("There was an unexpected mismatch in WORK_TASK_IDs.")