"""Utilities for labeling repetitive maintenance tasks from source CSV files.

This module follows the object-based approach used in repetitive_objects.ipynb:
- build the merged tickets/assets dataframe from source CSVs
- convert date columns to datetimes
- restrict repetition detection to corrective tasks
- default to grouping_4: SERVICE_CLASS + BUILDING + FLOOR + SPACE
- flag a task as repetitive when a later task for the same object occurs within
  the chosen time window

The main entry point is `build_repetitive_labels_from_csvs`, which returns the
full merged dataframe with a REPETITIVE column (1/0).
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd

from utils.data_aggregation_tools import merge_tickets_assets, convert_cols_to_datetime


DEFAULT_GROUP_COLS = ["SERVICE_CLASS", "BUILDING", "FLOOR", "SPACE"]
DEFAULT_OUTPUT_COLS = [
    "WORK_TASK_ID",
    "BUILDING",
    "FLOOR",
    "SPACE",
    "SERVICE_CLASS",
    "REQUEST_CLASS",
    "RESPONSIBLE_ORGANIZATION_NAME",
    "TASK_TYPE",
    "DESCRIPTION",
    "CREATE_DATE_LTZ",
    "BASELINE_START_LTZ",
    "REPETITIVE",
    "OBJECT_ID",
]

def _choose_time_column(df: pd.DataFrame) -> str:
    """Pick the best time column available for repetitive detection.

    The notebook's object-based workflow uses CREATE_DATE_LTZ through the helper
    in repetitive_tasks.py, while the older asset-based comparison used
    BASELINE_START_LTZ. We default to CREATE_DATE_LTZ when present and fall back
    to BASELINE_START_LTZ.
    """
    if "CREATE_DATE_LTZ" in df.columns:
        return "CREATE_DATE_LTZ"
    if "BASELINE_START_LTZ" in df.columns:
        return "BASELINE_START_LTZ"
    raise ValueError("Expected CREATE_DATE_LTZ or BASELINE_START_LTZ in merged dataframe.")



def _build_object_id(df: pd.DataFrame, group_cols: Sequence[str]) -> pd.Series:
    return df[group_cols].fillna("").astype(str).agg(" | ".join, axis=1)



def label_repetitive_objects(
    df_tickets_assets: pd.DataFrame,
    group_cols: Sequence[str] | None = None,
    num_days: int = 90,
    min_days: int = 3,
    drop_missing_space: bool = True,
    corrective_only: bool = True,
) -> pd.DataFrame:
    """Return a copy of the merged dataframe with REPETITIVE and OBJECT_ID columns.

    Parameters
    ----------
    df_tickets_assets:
        Merged tickets/assets dataframe.
    group_cols:
        Columns defining a unique object. Defaults to the notebook's chosen
        grouping_4: SERVICE_CLASS, BUILDING, FLOOR, SPACE.
    num_days:
        Maximum number of days between tasks for a row to be flagged repetitive.
    min_days:
        Minimum number of days between tasks. Matches the current helper's
        default to avoid near-duplicate same-day work being labeled repetitive.
    drop_missing_space:
        Whether to mimic the notebook's `dropna(subset=['SPACE'])` step before
        checking repetition. Rows excluded from detection remain in the output
        with REPETITIVE = 0.
    corrective_only:
        Whether to only consider corrective work tasks for repetition detection.

    Returns
    -------
    pd.DataFrame
        Full dataframe with REPETITIVE (1/0) and OBJECT_ID columns added.
    """
    group_cols = list(group_cols or DEFAULT_GROUP_COLS)
    df = df_tickets_assets.copy()

    required_cols = set(group_cols)
    required_cols.add("TASK_TYPE")

    time_col = _choose_time_column(df)
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")

    # Preserve stable row identity before sorting/grouping.
    df["__ROW_ID__"] = range(len(df))
    df["REPETITIVE"] = 0
    df["OBJECT_ID"] = ""

    detection_df = df.copy()

    if drop_missing_space and "SPACE" in detection_df.columns:
        detection_df = detection_df.dropna(subset=["SPACE"]).copy()

    if corrective_only:
        detection_df = detection_df[
            detection_df["TASK_TYPE"].astype(str).str.strip().str.lower() == "corrective"
        ].copy()

    # Ignore rows that cannot participate in time-window comparisons.
    detection_df = detection_df.dropna(subset=[time_col]).copy()

    if detection_df.empty:
        df = df.drop(columns=["__ROW_ID__"])
        return df

    detection_df["OBJECT_ID"] = _build_object_id(detection_df, group_cols)

    # Sort so we can early-break once we exceed the window.
    detection_df = detection_df.sort_values(group_cols + [time_col]).reset_index(drop=True)

    max_delta = pd.Timedelta(days=num_days)
    min_delta_td = pd.Timedelta(days=min_days)
    repetitive_row_ids: set[int] = set()

    for _, group in detection_df.groupby(group_cols, dropna=False):
        group = group.sort_values(time_col).reset_index(drop=True)

        for i in range(len(group)):
            current_row = group.iloc[i]
            current_time = current_row[time_col]
            later_rows = group.iloc[i + 1 :]

            for j in range(len(later_rows)):
                other_row = later_rows.iloc[j]
                diff = other_row[time_col] - current_time

                if pd.isna(diff):
                    continue

                if min_delta_td <= diff <= max_delta:
                    repetitive_row_ids.add(int(current_row["__ROW_ID__"]))
                    break
                if diff > max_delta:
                    break

    df["OBJECT_ID"] = _build_object_id(df, group_cols)
    df.loc[df["__ROW_ID__"].isin(repetitive_row_ids), "REPETITIVE"] = 1

    df = df.drop(columns=["__ROW_ID__"])
    return df



def build_repetitive_labels_from_csvs(
    tickets_csv_path: str | Path,
    assets_csv_path: str | Path,
    space_csv_path: str | Path | None = None,
    group_cols: Sequence[str] | None = None,
    num_days: int = 90,
    min_days: int = 3,
    drop_missing_space: bool = True,
    corrective_only: bool = True,
) -> pd.DataFrame:
    """Build merged tickets/assets data from source CSVs and label repetition.

    Parameters
    ----------
    tickets_csv_path:
        Path to V_OM_WORK_TASK.csv.
    assets_csv_path:
        Path to V_OM_WORK_TASK_ASSET.csv.
    space_csv_path:
        Accepted for interface consistency with the shared dashboard uploads.
        It is not used by the current notebook-derived repetitive-object logic.
    """
    df_tickets = pd.read_csv(tickets_csv_path)
    df_assets = pd.read_csv(assets_csv_path)

    df_tickets_assets = merge_tickets_assets(df_tickets=df_tickets, df_assets=df_assets)
    df_tickets_assets = convert_cols_to_datetime(df_tickets_assets)

    labeled_df = label_repetitive_objects(
        df_tickets_assets=df_tickets_assets,
        group_cols=group_cols,
        num_days=num_days,
        min_days=min_days,
        drop_missing_space=drop_missing_space,
        corrective_only=corrective_only,
    )

    return labeled_df



def build_repetitive_ticket_rows(
    labeled_df: pd.DataFrame,
    repetitive_only: bool = True,
    output_cols: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Return a frontend-friendly ticket table dataframe.

    This keeps the ticket-level grain needed for a panel table similar to the
    Panel 4 ticket results table.
    """
    df = labeled_df.copy()

    if repetitive_only:
        df = df[df["REPETITIVE"] == 1].copy()

    cols = list(output_cols or DEFAULT_OUTPUT_COLS)
    existing_cols = [col for col in cols if col in df.columns]

    # Keep REPETITIVE visible even if the caller overrides output_cols and omits it.
    if "REPETITIVE" not in existing_cols and "REPETITIVE" in df.columns:
        existing_cols.append("REPETITIVE")

    df = df[existing_cols].copy()

    for col in ["CREATE_DATE_LTZ", "BASELINE_START_LTZ"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
            df[col] = df[col].fillna("")

    if "REPETITIVE" in df.columns:
        df["REPETITIVE"] = df["REPETITIVE"].fillna(0).astype(int)

    for col in df.columns:
        if df[col].dtype == "object" or str(df[col].dtype).startswith("string"):
            df[col] = df[col].fillna("")

    return df
