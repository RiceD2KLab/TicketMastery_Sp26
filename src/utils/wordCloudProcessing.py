import pandas as pd
from dashboard.WordCloud import WordCloud

"""
Load asset, ticket, and space CSV data and return a merged DataFrame with
selected analysis fields and tokenized ticket descriptions.

Args:
    assets: Path to the assets CSV file.
    tickets: Path to the tickets CSV file.
    spaces: Path to the spaces CSV file.

Returns:
    pd.DataFrame: Merged and cleaned dataset with selected columns for analysis.
"""
def process_data(assets, tickets, spaces):
    df_assets = pd.read_csv(assets)
    df_tickets = pd.read_csv(tickets)
    df_space = pd.read_csv(spaces)

    df_assets = df_assets.drop_duplicates(subset="WORK_TASK_ID", keep="first")
    merged_df = pd.merge(df_tickets, df_assets, on='WORK_TASK_ID', how='left')

    buildingclass_map = (
        df_space
          .dropna(subset=["BUILDING_DESC", "BUILDING_CLASS"])
          .drop_duplicates(subset=["BUILDING_DESC"])
          .set_index("BUILDING_DESC")["BUILDING_CLASS"]
    )
    merged_df["BUILDING_CLASS"] = merged_df["BUILDING"].map(buildingclass_map)

    # Tokenizing Description for Word Cloud 
    merged_df = merged_df.dropna(subset=['DESCRIPTION'])
    merged_df['TOKENS'] = merged_df['DESCRIPTION'].apply(WordCloud.clean_and_tokenize)


    selected_columns = [
        'WORK_TASK_ID',
        'WORK_TASK_NAME_x',
        'WORK_TASK_STATUS_x',
        'RICE_WORK_STATUS',
        'TASK_TYPE',
        'DESCRIPTION',
        'TASK_PRIORITY',
        'REQUEST_CLASS',
        'SERVICE_CLASS',
        'PRIMARY_LOCATION',
        'BUILDING',
        'CUSTOMER_DEPARTMENT',
        'ASSET_ID',
        'ASSET_NAME',
        'ASSET_STATUS',
        'BUILDING_CLASS',
        'NUMBER_OF_ASSETS',
        'RESPONSIBLE_ORGANIZATION_NAME',
        'ORGANIZATION_TYPE',
        'ACTUAL_START_LTZ',
        'ACTUAL_END_LTZ',
        'RICE_ACTUAL_COST',
        'TOKENS'
    ]
    return merged_df[selected_columns].copy()