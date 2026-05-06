import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
import nltk
from collections import Counter
from nltk.sentiment import SentimentIntensityAnalyzer
from utils.StopWords import STOP_WORDS, SHORT_KEEP

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
sia = SentimentIntensityAnalyzer()


def _normalize_work_task_id(df):
    """
    Normalize WORK_TASK_ID values before joining ticket-related DataFrames.
    Args:
        df (pd.DataFrame): Source DataFrame with an optional WORK_TASK_ID column.

    Returns:
        pd.DataFrame: Copy of df with normalized WORK_TASK_ID values.
    """
    df = df.copy()
    if "WORK_TASK_ID" in df.columns:
        df["WORK_TASK_ID"] = (
            df["WORK_TASK_ID"]
            .astype("string")
            .str.strip()
            .str.replace(r"\.0$", "", regex=True)
        )
    return df


def clean_text(text):
    """
    Normalize a text value by stripping whitespace and collapsing internal spaces.

    Returns an empty string if the input is NaN or None.

    Parameters
    ----------
    text : any
        Raw text value, possibly NaN.

    Returns
    -------
    str
        Cleaned text string, or "" if input was null.
    """

    if pd.isna(text):
        return ""
    text = str(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def sentiment_score(text):
    """
    Compute the VADER compound sentiment score for a given text.

    Cleans the input text before scoring. Returns NaN if the cleaned
    text is empty.

    Parameters
    ----------
    text : any
        Raw text value to score.

    Returns
    -------
    float
        VADER compound score in [-1.0, 1.0], or np.nan if text is empty.
    """
    text = clean_text(text)
    if text == "":
        return np.nan
    return sia.polarity_scores(text)["compound"]


def print_sentiment_extremes(df, text_col, sentiment_col=None, n=5):
    """
    Print the highest and lowest sentiment rows in a DataFrame.

    Displays the top and bottom n rows ranked by a sentiment column,
    showing WORK_TASK_ID, SERVICE_CLASS, REQUEST_CLASS, the source text,
    and the sentiment score (only columns that exist in the DataFrame).

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing text and sentiment columns.
    text_col : str
        Name of the column containing the source text.
    sentiment_col : str, optional
        Name of the sentiment score column. Defaults to "{text_col}_SENTIMENT".
    n : int, optional
        Number of extreme rows to display at each end. Default is 5.
    """
    if sentiment_col is None:
        sentiment_col = f"{text_col}_SENTIMENT"

    cols_to_show = ["WORK_TASK_ID", "SERVICE_CLASS", "REQUEST_CLASS", "BUILDING", text_col, sentiment_col]
    available_cols = [col for col in cols_to_show if col in df.columns]

    top_rows = (
        df[available_cols]
        .dropna(subset=[sentiment_col])
        .sort_values(sentiment_col, ascending=False)
        .head(n)
    )

    bottom_rows = (
        df[available_cols]
        .dropna(subset=[sentiment_col])
        .sort_values(sentiment_col, ascending=True)
        .head(n)
    )

    print(f"Top {n} {text_col} sentiment")
    for _, row in top_rows.iterrows():
        for col in available_cols:
            print(f"{col}: {row[col]}")
        print("-" * 120)

    print(f"\nBottom {n} {text_col} sentiment")
    for _, row in bottom_rows.iterrows():
        for col in available_cols:
            print(f"{col}: {row[col]}")
        print("-" * 120)


def produce_sentimenet(df):
    """
    Applies sentiment scores across ticket rows. Sentiments scores
    are -1 to 1, -1 being associated with the most negative and 
    1 being the most positive. 

    Returns new df with additional columns
        - DESCRIPTION_SENTIMENT
        - RESOLUTION_DESCRIPTION_SENTIMENT
        - RESPONSE_COMMENTS_SENTIMENT
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing the following text columns:
        - DESCRIPTION
        - RESOLUTION_DESCRIPTION
        - RESPONSE_COMMENTS
    """
    text_cols = ["DESCRIPTION", "RESOLUTION_DESCRIPTION", "RESPONSE_COMMENTS"]
    df = df[
        ~df[text_cols]
        .astype(str)
        .apply(lambda row: row.str.contains("IGNORE", case=True, na=False).any(), axis=1)
    ].copy()
    for col in text_cols:
        df[f"{col}_SENTIMENT"] = df[col].apply(sentiment_score)
    return df


def process_dfs(tickets_df, assets_df, spaces_df, survey_df):
    """
    Merge asset, ticket, space, and survey dfs for sentiment analysis.

    Args:
        tickets_df: Ticket records dataframe.
        assets_df: Asset records dataframe.
        spaces_df: Space records dataframe.
        survey_df: Survey records dataframe.

    Returns:
        pd.DataFrame: Merged and cleaned dataset with selected columns for analysis.
    """
    df_assets = _normalize_work_task_id(assets_df)
    df_tickets = _normalize_work_task_id(tickets_df)
    df_space = spaces_df.copy()
    df_survey = _normalize_work_task_id(survey_df)
    ticket_response_col = None
    if "RESPONSE_COMMENTS" in df_tickets.columns:
        ticket_response_col = "__TICKET_RESPONSE_COMMENTS__"
        df_tickets = df_tickets.rename(columns={"RESPONSE_COMMENTS": ticket_response_col})

    df_assets = df_assets.drop_duplicates(subset="WORK_TASK_ID", keep="first")
    if "RESPONSE_COMMENTS" not in df_survey.columns:
        df_survey["RESPONSE_COMMENTS"] = ""

    df_survey_unique = (
        df_survey.dropna(subset=["WORK_TASK_ID"])
        .drop_duplicates(subset="WORK_TASK_ID", keep="first")
        [["WORK_TASK_ID", "RESPONSE_COMMENTS"]]
    )
    merged_df = pd.merge(df_tickets, df_assets, on='WORK_TASK_ID', how='left')
    merged_df = pd.merge(merged_df, df_survey_unique, on='WORK_TASK_ID', how='left')
    if ticket_response_col and "RESPONSE_COMMENTS" in merged_df.columns:
        merged_df["RESPONSE_COMMENTS"] = merged_df["RESPONSE_COMMENTS"].fillna(merged_df[ticket_response_col])
        merged_df = merged_df.drop(columns=[ticket_response_col])
    elif ticket_response_col:
        merged_df = merged_df.rename(columns={ticket_response_col: "RESPONSE_COMMENTS"})

    buildingclass_map = (
        df_space
        .dropna(subset=["BUILDING_DESC", "BUILDING_CLASS"])
        .drop_duplicates(subset=["BUILDING_DESC"])
        .set_index("BUILDING_DESC")["BUILDING_CLASS"]
    )
    merged_df["BUILDING_CLASS"] = merged_df["BUILDING"].map(buildingclass_map)
    for col in ["DESCRIPTION", "RESOLUTION_DESCRIPTION", "RESPONSE_COMMENTS"]:
        if col not in merged_df.columns:
            merged_df[col] = ""

    selected_columns = [
        'WORK_TASK_ID',
        'WORK_TASK_NAME_x',
        'WORK_TASK_STATUS_x',
        'RICE_WORK_STATUS',
        'TASK_TYPE',
        'RESOLUTION_DESCRIPTION',
        'DESCRIPTION',
        'RESPONSE_COMMENTS',
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
        'RICE_ACTUAL_COST'
    ]
    return merged_df[selected_columns].copy()


def process_data(assets, tickets, spaces, survey):
    """
    Load asset, ticket, space, and survey CSV data for sentiment analysis.

    Args:
        assets: Path to the assets CSV file.
        tickets: Path to the tickets CSV file.
        spaces: Path to the spaces CSV file.
        survey: Path to the survey CSV file.

    Returns:
        pd.DataFrame: Merged and cleaned dataset with selected columns for analysis.
    """
    return process_dfs(
        tickets_df=pd.read_csv(tickets),
        assets_df=pd.read_csv(assets),
        spaces_df=pd.read_csv(spaces),
        survey_df=pd.read_csv(survey),
    )
