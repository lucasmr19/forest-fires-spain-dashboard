import json
from pathlib import Path
from typing import Dict, Tuple, Optional

import folium
from folium.plugins import Fullscreen
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import st_folium


# -----------------------------
# Configuration
# -----------------------------
st.set_page_config(
    page_title="Forest Fires in Spain",
    page_icon="🔥",
    initial_sidebar_state="expanded",
    layout="wide",
)


# -----------------------------
# Data loading utilities
# -----------------------------
@st.cache_data
def load_data(filepath: str = "incendios.csv") -> pd.DataFrame:
    """
    Load wildfire data from a CSV file and normalize column names to English.

    The function attempts to read the CSV (semicolon-separated) and renames a set of
    known Spanish column names into English-friendly identifiers used by the app.

    Args:
        filepath: Path to the CSV file.

    Returns:
        A pandas DataFrame with normalized column names.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")

    # Read CSV (some datasets use ';' as separator)
    df = pd.read_csv(path, sep=";", low_memory=False)

    # Standardize column names used in the rest of the app
    rename_map = {
        "provincia": "province",
        "anio": "year",
        "perdidassuperficiales": "burned_area",
        "numeromediospersonal": "num_personnel",
        "numeromediospesados": "num_heavy",
        "numeromediosaereos": "num_air",
        "idcausa": "cause_id",
    }

    # Only rename if columns exist in the file
    existing_renames = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=existing_renames)

    # Ensure expected columns exist to avoid KeyError later; create them with defaults if missing
    expected_cols = [
        "province",
        "year",
        "burned_area",
        "num_personnel",
        "num_heavy",
        "num_air",
        "cause_id",
    ]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = 0

    # Convert types when reasonable
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(pd.Int64Dtype())
    df["burned_area"] = pd.to_numeric(df["burned_area"], errors="coerce").fillna(0)

    return df


@st.cache_data
def load_geojson(filepath: str = "spain-provinces.geojson") -> Dict:
    """
    Load a GeoJSON file containing Spanish provinces.

    Args:
        filepath: Path to the GeoJSON file.

    Returns:
        Parsed GeoJSON as a Python dictionary.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"GeoJSON file not found: {filepath}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------
# Helpers: filtering and normalization
# -----------------------------

def filter_data(
    df: pd.DataFrame,
    year_range: Tuple[int, int],
    include_intentional: bool,
    include_unintentional: bool,
) -> pd.DataFrame:
    """
    Filter the dataset by year range and whether to include intentional / unintentional fires.

    Args:
        df: Original DataFrame.
        year_range: Inclusive tuple (min_year, max_year).
        include_intentional: Keep intentional fires (cause_id between 400 and 499).
        include_unintentional: Keep non-intentional fires.

    Returns:
        Filtered DataFrame.
    """
    if df.empty:
        return df.copy()

    filtered = df.copy()

    # Year filter (handle missing year values safely)
    min_year, max_year = year_range
    filtered = filtered[filtered["year"].notna()]
    filtered = filtered[(filtered["year"] >= min_year) & (filtered["year"] <= max_year)]

    # Determine intentional by cause id range (adjust this logic if dataset uses different codes)
    filtered.loc[:, "intentional"] = filtered["cause_id"].between(400, 499)

    # Apply intent filters
    if not include_intentional:
        filtered = filtered[~filtered["intentional"]]
    if not include_unintentional:
        filtered = filtered[filtered["intentional"]]

    return filtered


def normalize_province_names(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Map province names from the dataset to the names used in the GeoJSON.

    Args:
        df: DataFrame that contains a `province` column.
        mapping: Dictionary mapping dataset province names -> GeoJSON province names.

    Returns:
        A copy of the DataFrame with a new column `province_normalized`.
    """
    df = df.copy()
    df.loc[:, "province_normalized"] = df["province"].map(mapping).fillna(df["province"])
    return df


# Common mapping from the Spanish dataset to typical GeoJSON province names
PROVINCE_NAME_MAP: Dict[str, str] = {
    "Leon": "León",
    "A Coruna": "A Coruña",
    "Bizkaia": "Bizkaia/Vizcaya",
    "Gipuzkoa": "Gipuzkoa/Guipúzcoa",
    "Alava": "Araba/Álava",
    "Avila": "Ávila",
    "Caceres": "Cáceres",
    "Cordoba": "Córdoba",
    "Jaen": "Jaén",
    "Malaga": "Málaga",
    "Cadiz": "Cádiz",
    "Almeria": "Almería",
    "Valencia": "València/Valencia",
    "Alicante": "Alacant/Alicante",
    "Castellon": "Castelló/Castellón",
    "Islas Baleares": "Illes Balears",
    "Santa Cruz de Tenerife": "Santa Cruz De Tenerife",
}


# -----------------------------
# Map construction
# -----------------------------

def create_choropleth_map(df: pd.DataFrame, geojson: Dict) -> Optional[folium.Map]:
    """
    Create a choropleth map showing total response resources per province.

    Args:
        df: Filtered DataFrame.
        geojson: GeoJSON dictionary for Spanish provinces.

    Returns:
        A folium.Map object or None when input data is empty.
    """
    if df.empty:
        return None

    # Normalize names and aggregate
    df_norm = normalize_province_names(df, PROVINCE_NAME_MAP)

    agg = (
        df_norm
        .groupby("province_normalized")
        .agg(
            num_personnel=("num_personnel", "sum"),
            num_heavy=("num_heavy", "sum"),
            num_air=("num_air", "sum"),
            burned_area=("burned_area", "sum"),
            sample_cause=("cause_id", "first"),
        )
        .reset_index()
    )

    agg["total_resources"] = agg[["num_personnel", "num_heavy", "num_air"]].sum(axis=1)

    info_by_province = agg.set_index("province_normalized").to_dict(orient="index")

    # Base map centered on mainland Spain
    m = folium.Map(location=[40.4168, -3.7038], zoom_start=6, max_zoom=7, min_zoom=5)
    
    Fullscreen(
        position="bottomright",
        title="Full screen",
        title_cancel="Exit Full Screen"
    ).add_to(m)

    # Limit bounds (include Canary Islands and Balearic area roughly)
    m.fit_bounds([[26.5, -18.5], [44.5, 5.5]])
    m.options["maxBounds"] = [[26.5, -18.5], [44.5, 5.5]]
    m.options["maxBoundsViscosity"] = 1.0

    # Add choropleth layer
    folium.Choropleth(
        geo_data=geojson,
        data=agg,
        columns=["province_normalized", "total_resources"],
        key_on="feature.properties.name",
        fill_color="YlOrRd",
        fill_opacity=0.7,
        line_opacity=1,
        line_color="black",
        line_weight=0.5,
        legend_name="Total resources",
        nan_fill_color="white",
        nan_fill_opacity=0.5,
    ).add_to(m)

    # Add per-feature GeoJson with a tooltip including aggregated info
    for feature in geojson.get("features", []):
        name = feature.get("properties", {}).get("name")
        province_info = info_by_province.get(name, {})

        tooltip_html = (
            f"<div style='font-size:13px'><b>Province:</b> {name}<br>"
            f"<b>Total resources:</b> {province_info.get('total_resources', 0)}<br>"
            f"<b>Personnel:</b> {province_info.get('num_personnel', 0)}<br>"
            f"<b>Heavy:</b> {province_info.get('num_heavy', 0)}<br>"
            f"<b>Air:</b> {province_info.get('num_air', 0)}<br>"
            f"<b>Burned area (ha):</b> {province_info.get('burned_area', 0):,.0f}<br></div>"
        )

        folium.GeoJson(
            feature,
            tooltip=folium.Tooltip(tooltip_html, sticky=True),
            style_function=lambda _: {"fillColor": "transparent", "color": "black", "weight": 0.5},
        ).add_to(m)

    return m


# -----------------------------
# Plot creation
# -----------------------------

def create_line_chart(df: pd.DataFrame) -> px.line:
    """
    Create a line chart of total burned area per year using Plotly Express.

    Args:
        df: Filtered DataFrame.

    Returns:
        A Plotly Figure object.
    """
    if df.empty:
        return px.line()

    burned_by_year = df.groupby("year")["burned_area"].sum().reset_index()

    fig = px.line(
        burned_by_year,
        x="year",
        y="burned_area",
        title="Burned area (hectares) by year",
        labels={"year": "Year", "burned_area": "Burned area (ha)"},
        markers=True,
    )
    fig.update_layout(xaxis_title="Year", yaxis_title="Burned area (ha)")
    return fig


def create_stacked_bar(df: pd.DataFrame) -> px.bar:
    """
    Create a stacked bar chart of response resources by year.

    Args:
        df: Filtered DataFrame.

    Returns:
        A Plotly Figure object.
    """
    if df.empty:
        return px.bar()

    resources_by_year = (
        df.groupby("year")[["num_personnel", "num_heavy", "num_air"]]
        .sum()
        .reset_index()
    )

    fig = px.bar(
        resources_by_year,
        x="year",
        y=["num_personnel", "num_heavy", "num_air"],
        title="Resources used by year",
        labels={"value": "Count", "year": "Year"},
        barmode="stack",
    )
    fig.update_layout(xaxis_title="Year", yaxis_title="Count", legend_title="Resource type")
    return fig


def create_top_provinces_chart(df: pd.DataFrame, top_n: int = 10) -> px.bar:
    """
    Create a horizontal bar chart of the top N provinces by burned area.

    Args:
        df: Filtered DataFrame.
        top_n: How many provinces to show.

    Returns:
        A Plotly Figure object.
    """
    if df.empty:
        return px.bar()

    burned_by_province = df.groupby("province")["burned_area"].sum().reset_index()
    top = burned_by_province.sort_values(by="burned_area", ascending=False).head(top_n)

    fig = px.bar(
        top,
        x="burned_area",
        y="province",
        orientation="h",
        title=f"Top {top_n} provinces by burned area",
        labels={"burned_area": "Burned area (ha)", "province": "Province"},
    )
    fig.update_layout(xaxis_title="Burned area (ha)", yaxis_title="Province", yaxis=dict(categoryorder="total ascending"))
    return fig


# -----------------------------
# Streamlit UI components
# -----------------------------

def sidebar_controls(df: pd.DataFrame) -> Tuple[Tuple[int, int], bool, bool]:
    """
    Create and render sidebar controls. Returns selected options.

    Args:
        df: The loaded DataFrame used to determine min/max year.

    Returns:
        Tuple containing (year_range, include_intentional, include_unintentional).
    """
    st.sidebar.title("Interaction controls")

    min_year = int(df["year"].min()) if not df["year"].isna().all() else 2000
    max_year = int(df["year"].max()) if not df["year"].isna().all() else 2020

    year_range = st.sidebar.slider(
        "Select year range:",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        step=1,
    )

    include_intentional = st.sidebar.checkbox("Include intentional fires", value=True)
    include_unintentional = st.sidebar.checkbox("Include unintentional fires", value=True)

    return year_range, include_intentional, include_unintentional


def info_expander() -> None:
    """
    Render an expander with dashboard information.
    """
    with st.expander("Dashboard information"):
        st.markdown(
            """
            **Purpose**

            This interactive dashboard visualizes forest fires in Spain. Data includes burned area,
            resources deployed and causes.

            **Team**

            - Saúl de los Reyes
            - Lucas Miralles

            **Data source**

            The dataset used originates from Kaggle.
            """
        )


def main_panel(df: pd.DataFrame, geojson: Dict) -> None:
    """
    Render the main dashboard panel with two columns of visualizations.

    Args:
        df: Filtered DataFrame used for plotting.
        geojson: GeoJSON dictionary for the map.
    """
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Response resources by province")
        fmap = create_choropleth_map(df, geojson)
        if fmap:
            st_folium(fmap, width=700, height=500)

        st.markdown("### Burned area trend")
        fig_line = create_line_chart(df)
        st.plotly_chart(fig_line, use_container_width=True)

        st.markdown("### Resources trend")
        fig_stack = create_stacked_bar(df)
        st.plotly_chart(fig_stack, use_container_width=True)

    with col2:
        st.markdown("### Top affected provinces")
        fig_top = create_top_provinces_chart(df, top_n=10)
        st.plotly_chart(fig_top, use_container_width=True)

        info_expander()


# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    try:
        data = load_data()
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()

    try:
        geojson = load_geojson()
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()

    year_range, include_intentional, include_unintentional = sidebar_controls(data)
    filtered = filter_data(data, year_range, include_intentional, include_unintentional)

    if filtered.empty:
        st.write("No data available for the selected filters.")
    else:
        main_panel(filtered, geojson)
