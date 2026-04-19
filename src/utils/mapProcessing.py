import pandas as pd
import pydeck as pdk


def build_map_html(csv_path: str) -> str:
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["FEP_BUILDING_X_COORDINATE", "FEP_BUILDING_Y_COORDINATE"]).copy()
    df["ASSIGNED_DATE_LTZ"] = pd.to_datetime(df["ASSIGNED_DATE_LTZ"], errors="coerce")

    df_filter = (
        df.groupby(
            [
                "FEP_BUILDING_Y_COORDINATE",
                "FEP_BUILDING_X_COORDINATE",
                "FEP_BUILDING_DESC",
                "FEP_BUILDING_CLASS",
            ]
        )
        .size()
        .reset_index(name="COUNT")
    )

    colors = {
        0: [0, 0, 255],
        1: [0, 255, 0],
        2: [255, 255, 0],
        3: [255, 127, 0],
        4: [255, 0, 0],
    }

    if not df_filter.empty:
        if df_filter["COUNT"].nunique() == 1:
            df_filter["COLOR"] = [[0, 255, 0]] * len(df_filter)
        else:
            df_filter["COLOR"] = pd.cut(
                df_filter["COUNT"], bins=5, labels=False, duplicates="drop"
            )
            df_filter["COLOR"] = df_filter["COLOR"].fillna(0).astype(int).map(colors)

    records = df_filter.to_dict("records")
    max_count = int(df_filter["COUNT"].max()) if not df_filter.empty else 1

    layer = pdk.Layer(
        "ColumnLayer",
        data=records,
        diskResolution=12,
        extruded=True,
        radius=10,
        elevationScale=500 / max_count if max_count else 1,
        get_position=["FEP_BUILDING_Y_COORDINATE", "FEP_BUILDING_X_COORDINATE"],
        get_fill_color="COLOR",
        getElevation="COUNT",
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

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "Building: {FEP_BUILDING_DESC}\n Type: {FEP_BUILDING_CLASS}\n Tickets: {COUNT}"},
    )

    return deck.to_html(as_string=True, iframe_height='100%', iframe_width='100%')