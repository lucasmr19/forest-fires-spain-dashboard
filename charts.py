import pandas as pd
import plotly.express as px


def create_line_chart(burned_by_year: pd.DataFrame):
    if burned_by_year.empty:
        return px.line()

    fig = px.line(
        burned_by_year,
        x="year",
        y="burned_area",
        title="Burned area (hectares) by year",
        labels={"year": "Year", "burned_area": "Burned area (ha)"},
        markers=True,
    )
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    return fig


def create_stacked_bar(resources_by_year: pd.DataFrame):
    if resources_by_year.empty:
        return px.bar()

    fig = px.bar(
        resources_by_year,
        x="year",
        y=["num_personnel", "num_heavy", "num_air"],
        title="Resources used by year",
        labels={"value": "Count", "year": "Year"},
        barmode="stack",
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title="Year",
        yaxis_title="Count",
        legend_title="Resource type",
    )
    return fig


def create_top_provinces_chart(top_provinces: pd.DataFrame):
    if top_provinces.empty:
        return px.bar()

    fig = px.bar(
        top_provinces.sort_values("burned_area", ascending=True),
        x="burned_area",
        y="province",
        orientation="h",
        title="Top affected provinces",
        labels={"burned_area": "Burned area (ha)", "province": "Province"},
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title="Burned area (ha)",
        yaxis_title="Province",
    )
    return fig