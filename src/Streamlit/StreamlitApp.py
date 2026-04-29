from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
from wordcloud import WordCloud
import matplotlib.pyplot as plt

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.StopWords import STOP_WORDS
from utils import repetitiveTicketProcessing as rtp
from utils import wordCloudProcessing
from utils import WordCloudHelpers
from utils import sentiments

st.set_page_config(page_title="Ticketmastery Dashboard", layout="wide")


ALLOWED_GROUP_COLS = [
    "SERVICE_CLASS",
    "REQUEST_CLASS",
    "RESPONSIBLE_ORGANIZATION_NAME",
]

SENTIMENT_TEXT_COLS = {
    "DESCRIPTION": "Initial Request Description",
    "RESOLUTION_DESCRIPTION": "Resolution Notes",
    "RESPONSE_COMMENTS": "Customer Response Comments",
}

MAP_REQUIRED_COLUMNS = {
    "FEP_BUILDING_X_COORDINATE",
    "FEP_BUILDING_Y_COORDINATE",
    "ASSIGNED_DATE_LTZ",
    "DESCRIPTION",
    "SERVICE_CLASS",
    "TASK_TYPE",
    "TASK_PRIORITY",
}


# Data access helpers
def sanitize_identifier(name: str) -> str:
    if not name:
        raise ValueError("Missing Snowflake view name.")
    cleaned = name.strip()
    if not re.fullmatch(r'[A-Za-z0-9_.$\"]+', cleaned):
        raise ValueError(f"Unsafe Snowflake object name: {name}")
    return cleaned


def get_conn():
    return st.connection("snowflake")


def get_default_source_mode() -> str:
    env = os.getenv("TICKETMASTERY_ENV", os.getenv("APP_ENV", "development")).strip().lower()
    return "Snowflake views" if env in {"prod", "production"} else "Local data folder"


def resolve_local_path(data_dir: str, filename: str | None) -> Path | None:
    if not filename or not filename.strip():
        return None

    file_path = Path(filename.strip()).expanduser()
    if file_path.is_absolute():
        return file_path

    base_dir = Path(data_dir.strip() or "data").expanduser()
    if not base_dir.is_absolute():
        base_dir = (Path(__file__).resolve().parent / base_dir).resolve()

    return base_dir / file_path


@st.cache_data(show_spinner=False)
def load_local_csv(csv_path: str) -> pd.DataFrame:
    path_obj = Path(csv_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Could not find CSV at {path_obj}")
    return pd.read_csv(path_obj)


@st.cache_data(show_spinner=False, ttl=600)
def load_snowflake_view(view_name: str) -> pd.DataFrame:
    conn = get_conn()
    safe_view = sanitize_identifier(view_name)
    return conn.query(f"SELECT * FROM {safe_view}", ttl=600)


# Utility logic 

def parse_group_values_input(text: str) -> list[str]:
    return [x.strip() for x in (text or "").split(",") if x.strip()]


def tokenize_description(text: str) -> list[str]:
    return [
        token
        for token in re.split(r"[^a-z0-9]+", str(text).lower())
        if token and len(token) > 2 and token not in STOP_WORDS
    ]


def clean_description(text: str) -> str:
    return " ".join(tokenize_description(text))


@st.cache_data(show_spinner=False)
def build_union_freq(descriptions: tuple[str, ...]) -> dict[str, int]:
    freq: dict[str, int] = {}
    for description in descriptions:
        for token in tokenize_description(description):
            freq[token] = freq.get(token, 0) + 1
    return freq


@st.cache_data(show_spinner=False)
def build_intersection_freq(
    descriptions: tuple[str, ...],
    group_values: tuple[str, ...],
    selected_values: tuple[str, ...],
) -> dict[str, int]:
    normalized_selected = {value.strip().lower() for value in selected_values if value.strip()}
    by_group_freq: dict[str, dict[str, int]] = {}

    for description, group_value in zip(descriptions, group_values):
        normalized_group = str(group_value).strip().lower()
        if normalized_group not in normalized_selected:
            continue
        if normalized_group not in by_group_freq:
            by_group_freq[normalized_group] = {}
        for token in tokenize_description(description):
            by_group_freq[normalized_group][token] = by_group_freq[normalized_group].get(token, 0) + 1

    if len(by_group_freq) < 2:
        return build_union_freq(descriptions)

    group_maps = list(by_group_freq.values())
    shared_words = set(group_maps[0].keys())
    for freq_map in group_maps[1:]:
        shared_words &= set(freq_map.keys())

    return {
        word: sum(freq_map.get(word, 0) for freq_map in group_maps)
        for word in shared_words
    }


@st.cache_data(show_spinner=False, ttl=600)
def build_repetitive_panel_data(
    tickets_df: pd.DataFrame,
    assets_df: pd.DataFrame,
    space_df: pd.DataFrame,
    num_days: int,
    min_days: int,
    repetitive_only: bool,
    drop_missing_space: bool,
    corrective_only: bool,
) -> tuple[pd.DataFrame, dict]:
    if rtp is None:
        raise RuntimeError(f"Could not import repetitiveTicketProcessing")

    labeled_df = rtp.build_repetitive_labels_from_dfs(
        tickets_df=tickets_df,
        assets_df=assets_df,
        space_df=space_df,
        group_cols=["SERVICE_CLASS", "BUILDING", "FLOOR", "SPACE"],
        num_days=num_days,
        min_days=min_days,
        drop_missing_space=drop_missing_space,
        corrective_only=corrective_only,
    )
    rows_df = rtp.build_repetitive_ticket_rows(
        labeled_df=labeled_df,
        repetitive_only=repetitive_only,
    )

    summary = {
        "total_rows": int(len(labeled_df)),
        "repetitive_rows": int((labeled_df["REPETITIVE"] == 1).sum()) if "REPETITIVE" in labeled_df.columns else 0,
        "returned_rows": int(len(rows_df)),
        "num_days": int(num_days),
        "min_days": int(min_days),
        "repetitive_only": bool(repetitive_only),
        "drop_missing_space": bool(drop_missing_space),
        "corrective_only": bool(corrective_only),
    }
    return rows_df, summary


@st.cache_data(show_spinner=False, ttl=600)
def build_wordcloud_ticket_rows(
    tickets_df: pd.DataFrame,
    assets_df: pd.DataFrame,
    space_df: pd.DataFrame,
    group_col: str,
    group_values_text: str,
) -> pd.DataFrame:
    if wordCloudProcessing is None:
        raise RuntimeError(f"Could not import wordCloudProcessing")

    selected_values = parse_group_values_input(group_values_text)

    df = wordCloudProcessing.process_dfs(
        tickets_df=tickets_df,
        assets_df=assets_df,
        spaces_df=space_df,
    )

    ticket_df = df.copy()

    if group_col:
        if group_col not in ALLOWED_GROUP_COLS:
            raise ValueError(f"Invalid group_col: {group_col}")
        if group_col not in ticket_df.columns:
            raise ValueError(f"{group_col} not found in processed data")
        if selected_values:
            ticket_df = ticket_df[ticket_df[group_col].isin(selected_values)]
        ticket_df["GROUP_VALUE"] = ticket_df[group_col].fillna("")
    else:
        ticket_df["GROUP_VALUE"] = ""

    output = (
        ticket_df[["WORK_TASK_ID", "BUILDING", "DESCRIPTION", "GROUP_VALUE"]]
        .fillna("")
        .replace({np.inf: "", -np.inf: ""})
        .copy()
    )
    return output

@st.cache_data(show_spinner=False, ttl=600)
def build_sentiment_ticket_rows(
    tickets_df: pd.DataFrame,
    assets_df: pd.DataFrame,
    space_df: pd.DataFrame,
    survey_df: pd.DataFrame,
) -> pd.DataFrame:
    if sentiments is None:
        raise RuntimeError("Could not import sentiments")

    df = sentiments.process_dfs(
        tickets_df=tickets_df,
        assets_df=assets_df,
        spaces_df=space_df,
        survey_df=survey_df,
    )
    df = sentiments.produce_sentimenet(df)

    output_cols = [
        "WORK_TASK_ID",
        "BUILDING",
        "SERVICE_CLASS",
        "REQUEST_CLASS",
        "DESCRIPTION",
        "DESCRIPTION_SENTIMENT",
        "RESOLUTION_DESCRIPTION",
        "RESOLUTION_DESCRIPTION_SENTIMENT",
        "RESPONSE_COMMENTS",
        "RESPONSE_COMMENTS_SENTIMENT",
    ]

    available_output_cols = [col for col in output_cols if col in df.columns]

    return (
        df[available_output_cols]
        .replace({np.inf: np.nan, -np.inf: np.nan})
        .copy()
    )


def build_sentiment_extremes(
    df: pd.DataFrame,
    text_col: str,
    threshold: float,
    n_rows: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    sentiment_col = f"{text_col}_SENTIMENT"

    available_cols = [
        "WORK_TASK_ID",
        "BUILDING",
        "SERVICE_CLASS",
        "REQUEST_CLASS",
        text_col,
        sentiment_col,
    ]

    available_cols = [col for col in available_cols if col in df.columns]

    sentiment_df = (
        df[available_cols]
        .dropna(subset=[sentiment_col])
        .copy()
    )

    positive_df = (
        sentiment_df[sentiment_df[sentiment_col] >= threshold]
        .sort_values(sentiment_col, ascending=False)
        .head(n_rows)
    )

    negative_df = (
        sentiment_df[sentiment_df[sentiment_col] <= -threshold]
        .sort_values(sentiment_col, ascending=True)
        .head(n_rows)
    )

    rename_map = {
        "WORK_TASK_ID": "Ticket ID",
        "BUILDING": "Building",
        "SERVICE_CLASS": "Service Class",
        "REQUEST_CLASS": "Request Class",
        text_col: SENTIMENT_TEXT_COLS.get(text_col, text_col),
        sentiment_col: "Sentiment Score",
    }

    return positive_df.rename(columns=rename_map), negative_df.rename(columns=rename_map)

def make_download_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def render_paginated_dataframe(df: pd.DataFrame, key_prefix: str, height: int = 500):
    total_rows = len(df)

    if f"{key_prefix}_page_size" not in st.session_state:
        st.session_state[f"{key_prefix}_page_size"] = 100
    if f"{key_prefix}_page" not in st.session_state:
        st.session_state[f"{key_prefix}_page"] = 1

    page_size = st.session_state[f"{key_prefix}_page_size"]
    total_pages = max(1, int(np.ceil(total_rows / page_size)))

    if st.session_state[f"{key_prefix}_page"] > total_pages:
        st.session_state[f"{key_prefix}_page"] = total_pages

    page = st.session_state[f"{key_prefix}_page"]
    start = (page - 1) * page_size
    end = start + page_size

    st.dataframe(df.iloc[start:end], use_container_width=True, height=height, hide_index=True)
    st.caption(f"Showing rows {start + 1:,}–{min(end, total_rows):,} of {total_rows:,}")

    col1, col2 = st.columns(2)

    with col1:
        st.session_state[f"{key_prefix}_page_size"] = st.selectbox(
            "Rows per page",
            options=[25, 50, 100, 250, 500],
            index=[25, 50, 100, 250, 500].index(page_size),
            key=f"{key_prefix}_page_size_control",
        )

    with col2:
        new_total_pages = max(
            1,
            int(np.ceil(total_rows / st.session_state[f"{key_prefix}_page_size"]))
        )
        if st.session_state[f"{key_prefix}_page"] > new_total_pages:
            st.session_state[f"{key_prefix}_page"] = new_total_pages

        st.session_state[f"{key_prefix}_page"] = st.number_input(
            "Page",
            min_value=1,
            max_value=new_total_pages,
            value=st.session_state[f"{key_prefix}_page"],
            step=1,
            key=f"{key_prefix}_page_control",
        )

# Word cloud render
def render_wordcloud(freq: dict[str, int]):
    if not freq:
        st.info("No words available for word cloud.")
        return

    wc = WordCloud(
        width=1400,
        height=500,
        background_color="white",
    ).generate_from_frequencies(freq)

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig, clear_figure=True)

# Source loading
def load_sources(
    source_mode: str,
    data_dir: str | None,
    tickets_filename: str | None,
    assets_filename: str | None,
    space_filename: str | None,
    map_filename: str | None,
    survey_filename: str | None,
    tickets_view: str | None,
    assets_view: str | None,
    space_view: str | None,
    map_view: str | None,
    survey_view: str | None,
) -> tuple[
    pd.DataFrame | None,
    pd.DataFrame | None,
    pd.DataFrame | None,
    pd.DataFrame | None,
    pd.DataFrame | None,
    dict[str, str],
]:
    tickets_df = assets_df = space_df = map_df = survey_df = None
    resolved_sources: dict[str, str] = {}

    if source_mode == "Snowflake views":
        if tickets_view:
            tickets_df = load_snowflake_view(tickets_view)
            resolved_sources["tickets"] = tickets_view
        if assets_view:
            assets_df = load_snowflake_view(assets_view)
            resolved_sources["assets"] = assets_view
        if space_view:
            space_df = load_snowflake_view(space_view)
            resolved_sources["space"] = space_view
        if map_view:
            map_df = load_snowflake_view(map_view)
            resolved_sources["map"] = map_view
        if survey_view:
            survey_df = load_snowflake_view(survey_view)
            resolved_sources["survey"] = survey_view
    else:
        tickets_path = resolve_local_path(data_dir, tickets_filename)
        assets_path = resolve_local_path(data_dir, assets_filename)
        space_path = resolve_local_path(data_dir, space_filename)
        map_path = resolve_local_path(data_dir, map_filename)
        survey_path = resolve_local_path(data_dir, survey_filename)

        if tickets_path:
            tickets_df = load_local_csv(str(tickets_path))
            resolved_sources["tickets"] = str(tickets_path)
        if assets_path:
            assets_df = load_local_csv(str(assets_path))
            resolved_sources["assets"] = str(assets_path)
        if space_path:
            space_df = load_local_csv(str(space_path))
            resolved_sources["space"] = str(space_path)
        if map_path:
            map_df = load_local_csv(str(map_path))
            resolved_sources["map"] = str(map_path)
        if survey_path:
            survey_df = load_local_csv(str(survey_path))
            resolved_sources["survey"] = str(survey_path)


    if map_df is None and tickets_df is not None and MAP_REQUIRED_COLUMNS.issubset(set(tickets_df.columns)):
        map_df = tickets_df.copy()
        resolved_sources["map"] = "tickets source (fallback)"

    return tickets_df, assets_df, space_df, map_df, survey_df, resolved_sources

# Sidebar and app shell
st.title("Ticketmastery Dashboard")

with st.sidebar:
    st.header("App Settings")
    default_source_mode = get_default_source_mode()
    source_mode = st.radio(
        "Data source",
        ["Local data folder", "Snowflake views"],
        index=0 if default_source_mode == "Local data folder" else 1,
    )
    page = st.radio(
        "Panel",
        [
            "Panel 1 · Repetitive Tasks",
            "Panel 2 · Map",
            "Panel 3 · Sentiment Analysis",
            "Panel 4 · Word Cloud",
        ],
    )

    data_dir = "../../data"
    tickets_filename = "V_OM_WORK_TASK.csv"
    assets_filename = "V_OM_WORK_TASK_ASSET.csv"
    space_filename = "V_SPACE_DETAIL.csv"
    map_filename = "TICKETS_WITH_COORDS.csv"
    survey_filename = "V_OM_WORK_TASK_SURVEY.csv"
    tickets_view = assets_view = space_view = map_view = survey_view = None

    if source_mode == "Snowflake views":
        st.subheader("Snowflake objects")
        st.caption("Production mode: Snowflake views")
        tickets_view = st.text_input("Tickets view", value="V_OM_WORK_TASK")
        assets_view = st.text_input("Assets view", value="V_OM_WORK_TASK_ASSET")
        space_view = st.text_input("Space view", value="V_SPACE_DETAIL")
        map_view = st.text_input("Map view", value="TICKETS_WITH_COORDS")
        survey_view = st.text_input("Survey view", value="V_OM_WORK_TASK_SURVEY")
    else:
        st.subheader("Local CSV files")
        data_dir = st.text_input("Data directory", value="../../data")
        tickets_filename = st.text_input("Tickets CSV", value="V_OM_WORK_TASK.csv")
        assets_filename = st.text_input("Assets CSV", value="V_OM_WORK_TASK_ASSET.csv")
        space_filename = st.text_input("Space CSV", value="V_SPACE_DETAIL.csv")
        map_filename = st.text_input("Map CSV", value="TICKETS_WITH_COORDS.csv")
        survey_filename = st.text_input("Survey CSV", value="V_OM_WORK_TASK_SURVEY.csv")

try:
    tickets_df, assets_df, space_df, map_df, survey_df, resolved_sources = load_sources(
        source_mode,
        data_dir,
        tickets_filename,
        assets_filename,
        space_filename,
        map_filename,
        survey_filename,
        tickets_view,
        assets_view,
        space_view,
        map_view,
        survey_view,
    )
except Exception as exc:
    st.error(f"Could not load source data: {exc}")
    st.stop()

with st.expander("Current source configuration", expanded=False):
    st.write(f"Source mode: **{source_mode}**")
    if source_mode == "Local data folder":
        resolved_data_dir = Path(data_dir).expanduser()
        if not resolved_data_dir.is_absolute():
            resolved_data_dir = (Path(__file__).resolve().parent / resolved_data_dir).resolve()
        st.write(f"Data directory: `{resolved_data_dir}`")
    st.json(resolved_sources)


# Panel 1
if page == "Panel 1 · Repetitive Tasks":
    st.header("Repetitive Tasks")

    if tickets_df is None or assets_df is None or space_df is None:
        st.info("Load Tickets, Assets, and Space data to use this panel.")
        st.stop()

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        num_days = st.number_input("X-day window", min_value=1, max_value=365, value=90)
    with col2:
        min_days = st.number_input("Minimum days", min_value=1, max_value=30, value=3)
    with col3:
        repetitive_only = st.checkbox("Repetitive only", value=True)
    with col4:
        corrective_only = st.checkbox("Corrective only", value=True)

    drop_missing_space = st.checkbox("Drop rows missing space", value=True)

    try:
        panel1_df, summary = build_repetitive_panel_data(
            tickets_df=tickets_df,
            assets_df=assets_df,
            space_df=space_df,
            num_days=int(num_days),
            min_days=int(min_days),
            repetitive_only=bool(repetitive_only),
            drop_missing_space=bool(drop_missing_space),
            corrective_only=bool(corrective_only),
        )
    except Exception as exc:
        st.error(f"Panel 1 failed: {exc}")
        st.stop()

    st.caption(
        f"Computed with num_days={summary['num_days']}, min_days={summary['min_days']}, "
        f"repetitive_only={summary['repetitive_only']}, drop_missing_space={summary['drop_missing_space']}, "
        f"corrective_only={summary['corrective_only']}."
    )

    rename_map = {
        "WORK_TASK_ID": "Ticket ID",
        "BUILDING": "Building",
        "OBJECT_ID": "Object",
        "TASK_TYPE": "Task Type",
        "CREATE_DATE_LTZ": "Created",
        "REPETITIVE": "Repetitive",
        "DESCRIPTION": "Description",
    }
    panel1_display = panel1_df.rename(columns=rename_map)
    render_paginated_dataframe(panel1_display, key_prefix="panel1")

    st.download_button(
        "Download Panel 1 CSV",
        data=make_download_bytes(panel1_display),
        file_name="panel1_repetitive_tasks.csv",
        mime="text/csv",
    )

# Panel 2
elif page == "Panel 2 · Map":
    st.header("Ticket Heat Map by Building")

    if map_df is None:
        st.info(
            "Load a map dataset or point the optional map view at a Snowflake object with coordinates. "
        )
        st.stop()

    missing_cols = MAP_REQUIRED_COLUMNS - set(map_df.columns)
    if missing_cols:
        st.error(f"Map data is missing required columns: {sorted(missing_cols)}")
        st.stop()

    map_df = map_df.dropna(subset=["FEP_BUILDING_X_COORDINATE", "FEP_BUILDING_Y_COORDINATE"]).copy()
    map_df["ASSIGNED_DATE_LTZ"] = pd.to_datetime(map_df["ASSIGNED_DATE_LTZ"], errors="coerce")
    map_df = map_df.dropna(subset=["ASSIGNED_DATE_LTZ"])

    with st.sidebar:
        st.subheader("Map Filters")
        search_option = st.text_input("Keyword search", value="", key="map_search")
        min_date = map_df["ASSIGNED_DATE_LTZ"].min().date()
        max_date = map_df["ASSIGNED_DATE_LTZ"].max().date()
        time_option = st.slider(
            "Date range",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            key="map_date_range",
        )
        service_option = st.multiselect(
            "Service Class",
            options=sorted(map_df["SERVICE_CLASS"].dropna().astype(str).unique().tolist()),
            default=sorted(map_df["SERVICE_CLASS"].dropna().astype(str).unique().tolist()),
            key="map_service_class",
        )
        building_col = "FEP_BUILDING_CLASS" if "FEP_BUILDING_CLASS" in map_df.columns else None
        building_option = []
        if building_col:
            building_option = st.multiselect(
                "Building Class",
                options=sorted(map_df[building_col].dropna().astype(str).unique().tolist()),
                default=[],
                key="map_building_class",
            )
        task_option = st.multiselect(
            "Task Type",
            options=sorted(map_df["TASK_TYPE"].dropna().astype(str).unique().tolist()),
            default=[],
            key="map_task_type",
        )
        priority_option = st.multiselect(
            "Task Priority",
            options=sorted(map_df["TASK_PRIORITY"].dropna().astype(str).unique().tolist()),
            default=[],
            key="map_task_priority",
        )

    filtered_map = map_df.copy()
    start_date = pd.to_datetime(time_option[0])
    end_date = pd.to_datetime(time_option[1])
    filtered_map = filtered_map[(filtered_map["ASSIGNED_DATE_LTZ"] >= start_date) & (filtered_map["ASSIGNED_DATE_LTZ"] <= end_date)]

    if search_option:
        filtered_map = filtered_map[
            filtered_map["DESCRIPTION"].fillna("").astype(str).str.contains(search_option, case=False, na=False)
        ]
    if service_option:
        filtered_map = filtered_map[filtered_map["SERVICE_CLASS"].astype(str).isin(service_option)]
    if building_col and building_option:
        filtered_map = filtered_map[filtered_map[building_col].astype(str).isin(building_option)]
    if task_option:
        filtered_map = filtered_map[filtered_map["TASK_TYPE"].astype(str).isin(task_option)]
    if priority_option:
        filtered_map = filtered_map[filtered_map["TASK_PRIORITY"].astype(str).isin(priority_option)]

    if filtered_map.empty:
        st.warning("No map rows match the selected filters.")
        st.stop()

    group_cols = [
        "FEP_BUILDING_Y_COORDINATE",
        "FEP_BUILDING_X_COORDINATE",
        "FEP_BUILDING_DESC",
    ]
    if building_col:
        group_cols.append(building_col)

    grouped = filtered_map.groupby(group_cols).size().reset_index(name="COUNT")
    grouped["COLOR_BIN"] = pd.cut(grouped["COUNT"], bins=5, labels=False, duplicates="drop")
    color_map = {
        0: [0, 0, 255],
        1: [0, 255, 0],
        2: [255, 255, 0],
        3: [255, 127, 0],
        4: [255, 0, 0],
    }
    grouped["COLOR"] = grouped["COLOR_BIN"].map(color_map)
    grouped["COLOR"] = grouped["COLOR"].apply(lambda x: x if isinstance(x, list) else [0, 0, 255])
    if building_col and building_col not in grouped.columns:
        grouped[building_col] = ""

    layer = pdk.Layer(
        "ColumnLayer",
        data=grouped.to_dict("records"),
        diskResolution=12,
        extruded=True,
        radius=10,
        elevationScale=500 / max(int(grouped["COUNT"].max()), 1),
        get_position=["FEP_BUILDING_Y_COORDINATE", "FEP_BUILDING_X_COORDINATE"],
        get_fill_color="COLOR",
        get_elevation="COUNT",
        pickable=True,
    )

    view_state = pdk.ViewState(
        longitude=-95.404182,
        latitude=29.717154,
        zoom=14.7,
        min_zoom=14,
        max_zoom=20,
        pitch=45,
    )

    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={
                "text": "Building: {FEP_BUILDING_DESC}\nType: {%s}\nTickets: {COUNT}" % (building_col or "FEP_BUILDING_DESC")
            },
        )
    )

    st.download_button(
        "Download filtered map rows",
        data=make_download_bytes(filtered_map),
        file_name="panel2_filtered_map_rows.csv",
        mime="text/csv",
    )
    st.subheader("Grouped building counts")
    render_paginated_dataframe(grouped.rename(columns={"COUNT": "Tickets"}), key_prefix="panel2_grouped", height=350)
# Panel 3
elif page == "Panel 3 · Sentiment Analysis":
    st.header("Sentiment Analysis")

    if tickets_df is None or assets_df is None or space_df is None or survey_df is None:
        st.info("Load Tickets, Assets, Space, and Survey data to use this panel.")
        st.stop()

    c1, c2, c3 = st.columns([1.4, 1, 1])

    with c1:
        selected_text_col = st.selectbox(
            "Text field",
            options=list(SENTIMENT_TEXT_COLS.keys()),
            format_func=lambda col: SENTIMENT_TEXT_COLS[col],
        )

    with c2:
        threshold = st.slider(
            "Sentiment threshold",
            min_value=0.05,
            max_value=1.00,
            value=0.50,
            step=0.05,
            help="Higher values show only stronger positive and negative sentiment.",
        )

    with c3:
        n_rows = st.number_input(
            "Rows per section",
            min_value=1,
            max_value=100,
            value=10,
            step=1,
        )

    try:
        panel3_df = build_sentiment_ticket_rows(
            tickets_df=tickets_df,
            assets_df=assets_df,
            space_df=space_df,
            survey_df=survey_df,
        )
    except Exception as exc:
        st.error(f"Panel 3 failed: {exc}")
        st.stop()

    sentiment_col = f"{selected_text_col}_SENTIMENT"

    if sentiment_col not in panel3_df.columns:
        st.error(f"Could not find sentiment column: {sentiment_col}")
        st.stop()

    scored_df = panel3_df.dropna(subset=[sentiment_col]).copy()

    positive_count = int((scored_df[sentiment_col] >= threshold).sum())
    negative_count = int((scored_df[sentiment_col] <= -threshold).sum())

    m1, m2, m3 = st.columns(3)
    m1.metric("Scored tickets", f"{len(scored_df):,}")
    m2.metric("Strong positive tickets", f"{positive_count:,}")
    m3.metric("Strong negative tickets", f"{negative_count:,}")

    st.caption(
        f"Showing sentiment extremes for **{SENTIMENT_TEXT_COLS[selected_text_col]}**. "
        f"Positive rows have scores ≥ {threshold:.2f}; negative rows have scores ≤ {-threshold:.2f}."
    )

    positive_df, negative_df = build_sentiment_extremes(
        df=panel3_df,
        text_col=selected_text_col,
        threshold=float(threshold),
        n_rows=int(n_rows),
    )

    left, right = st.columns(2)

    with left:
        st.subheader("Positive Tickets")
        if positive_df.empty:
            st.info("No tickets met the positive threshold.")
        else:
            render_paginated_dataframe(
                positive_df,
                key_prefix="panel3_positive",
                height=450,
            )

    with right:
        st.subheader("Negative Tickets")
        if negative_df.empty:
            st.info("No tickets met the negative threshold.")
        else:
            render_paginated_dataframe(
                negative_df,
                key_prefix="panel3_negative",
                height=450,
            )

    download_df = pd.concat(
        [
            positive_df.assign(Category="Positive"),
            negative_df.assign(Category="Negative"),
        ],
        ignore_index=True,
    )

    st.download_button(
        "Download Panel 3 sentiment rows",
        data=make_download_bytes(download_df),
        file_name="panel3_sentiment_extremes.csv",
        mime="text/csv",
    )

# Panel 4
elif page == "Panel 4 · Word Cloud":
    st.header("Keyword Search + Word Cloud")

    if tickets_df is None or assets_df is None or space_df is None:
        st.info("Load Tickets, Assets, and Space data to use this panel.")
        st.stop()

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        group_col = st.selectbox("Group column", options=[""] + ALLOWED_GROUP_COLS, format_func=lambda x: x or "(overall)")
    with c2:
        group_values_text = st.text_input("Group values", placeholder="Electrical, HVAC")
    with c3:
        keyword = st.text_input("Keyword filter", placeholder="Search keyword in descriptions")

    intersection = st.checkbox("Intersection mode", value=False)

    try:
        panel4_df = build_wordcloud_ticket_rows(
            tickets_df=tickets_df,
            assets_df=assets_df,
            space_df=space_df,
            group_col=group_col,
            group_values_text=group_values_text,
        )
    except Exception as exc:
        st.error(f"Panel 4 failed: {exc}")
        st.stop()

    panel4_df = panel4_df.rename(
        columns={
            "WORK_TASK_ID": "Ticket ID",
            "BUILDING": "Building",
            "DESCRIPTION": "Description",
            "GROUP_VALUE": "Group",
        }
    )

    if keyword:
        filtered_panel4 = panel4_df[
            panel4_df["Description"].fillna("").astype(str).map(clean_description).str.contains(keyword.lower(), na=False, regex=False)
        ].copy()
    else:
        filtered_panel4 = panel4_df.copy()

    selected_values = tuple(parse_group_values_input(group_values_text))
    can_intersect = bool(group_col and len(selected_values) > 1)

    descriptions = tuple(filtered_panel4["Description"].fillna("").astype(str).tolist())
    groups = tuple(filtered_panel4["Group"].fillna("").astype(str).tolist())
    union_freq = build_union_freq(descriptions)
    intersection_freq = build_intersection_freq(descriptions, groups, selected_values)
    freq = intersection_freq if intersection and can_intersect else union_freq

    st.caption(
        f"Showing {len(filtered_panel4):,} rows. "
        + (f'Keyword filter: "{keyword}". ' if keyword else "No keyword filter. ")
        + ("Using intersection frequency." if intersection and can_intersect else "Using union frequency.")
    )

    top_words_df = pd.DataFrame(
        sorted(freq.items(), key=lambda x: x[1], reverse=True)[:100],
        columns=["Word", "Count"],
    )

    st.subheader("Word Cloud")
    render_wordcloud(freq)

    left, right = st.columns([1, 2])
    with left:
        st.subheader("Top words")
        st.dataframe(top_words_df, use_container_width=True, height=400, hide_index=True)
    with right:
        st.subheader("Matching tickets")
        filtered_display = filtered_panel4.copy()
        filtered_display["Cleaned Description"] = filtered_display["Description"].map(clean_description)
        render_paginated_dataframe(
            filtered_display[["Ticket ID", "Building", "Group", "Cleaned Description"]],
            key_prefix="panel4",
            height=400,
        )

    st.download_button(
        "Download Panel 4 rows",
        data=make_download_bytes(filtered_panel4),
        file_name="panel4_wordcloud_rows.csv",
        mime="text/csv",
    )
