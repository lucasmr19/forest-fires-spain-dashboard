from typing import Tuple

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from charts import (
    create_line_chart,
    create_stacked_bar,
    create_top_provinces_chart,
)
from map_utils import create_choropleth_map


def sidebar_controls(df: pd.DataFrame) -> Tuple[Tuple[int, int], bool, bool]:
    st.sidebar.title("Interaction controls")

    valid_years = df["year"].dropna()
    min_year = int(valid_years.min()) if not valid_years.empty else 2000
    max_year = int(valid_years.max()) if not valid_years.empty else 2020

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
    with st.expander("Dashboard information"):
        st.markdown(
            """
            **Purpose**

            This interactive dashboard visualizes forest fires in Spain. Data includes burned area,
            resources deployed and causes.

            **Team**

            - Lucas Miralles
            - Saúl de los Reyes

            **Data source**

            The dataset used originates from Kaggle.
            """
        )


def main_panel(
    df: pd.DataFrame,
    geojson: dict,
    burned_by_year: pd.DataFrame,
    resources_by_year: pd.DataFrame,
    top_provinces: pd.DataFrame,
) -> None:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Response resources by province")
        fmap = create_choropleth_map(df, geojson)
        if fmap:
            st_folium(fmap, width=700, height=500)

        st.markdown("### Burned area trend")
        fig_line = create_line_chart(burned_by_year)
        st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})

        st.markdown("### Resources trend")
        fig_stack = create_stacked_bar(resources_by_year)
        st.plotly_chart(fig_stack, use_container_width=True, config={"displayModeBar": False})

    with col2:
        st.markdown("### Top affected provinces")
        fig_top = create_top_provinces_chart(top_provinces)
        st.plotly_chart(fig_top, use_container_width=True, config={"displayModeBar": False})

        info_expander()