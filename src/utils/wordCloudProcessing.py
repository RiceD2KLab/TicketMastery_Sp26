import pandas as pd
from utils import WordCloudHelpers


def _normalize_work_task_id(df):
    df = df.copy()
    if "WORK_TASK_ID" in df.columns:
        df["WORK_TASK_ID"] = (
            df["WORK_TASK_ID"]
            .astype("string")
            .str.strip()
            .str.replace(r"\.0$", "", regex=True)
        )
    return df


def process_dfs(tickets_df, assets_df, spaces_df):
    """
    Merge asset, ticket, and space dfs and return a DataFrame with
    selected analysis fields and tokenized ticket descriptions.

    Args:
        tickets_df: Ticket records dataframe.
        assets_df: Asset records dataframe.
        spaces_df: Space records dataframe.

    Returns:
        pd.DataFrame: Merged and cleaned dataset with selected columns for analysis.
    """
    df_assets = _normalize_work_task_id(assets_df)
    df_tickets = _normalize_work_task_id(tickets_df)
    df_space = spaces_df.copy()

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
    merged_df['TOKENS'] = merged_df['DESCRIPTION'].apply(WordCloudHelpers.clean_and_tokenize)


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


def process_data(assets, tickets, spaces):
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
    return process_dfs(
        tickets_df=pd.read_csv(tickets),
        assets_df=pd.read_csv(assets),
        spaces_df=pd.read_csv(spaces),
    )
