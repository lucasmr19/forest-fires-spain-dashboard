import streamlit as st

from aggregations import (
    yearly_burned,
    yearly_resources,
    top_provinces_by_burned_area,
)
from data import load_data, load_geojson
from filters import filter_data
from ui import sidebar_controls, main_panel


st.set_page_config(
    page_title="Forest Fires in Spain",
    page_icon="🔥",
    initial_sidebar_state="expanded",
    layout="wide",
)


def main() -> None:
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

    st.title("Forest Fires in Spain")

    if filtered.empty:
        st.warning("No data available for the selected filters.")
        return

    burned_by_year = yearly_burned(filtered)
    resources_by_year = yearly_resources(filtered)
    top_provinces = top_provinces_by_burned_area(filtered, top_n=10)

    main_panel(
        filtered,
        geojson,
        burned_by_year,
        resources_by_year,
        top_provinces,
    )


if __name__ == "__main__":
    main()