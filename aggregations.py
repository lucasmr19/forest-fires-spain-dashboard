import pandas as pd
import streamlit as st


@st.cache_data(show_spinner=False)
def yearly_burned(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["year", "burned_area"])
    return df.groupby("year", as_index=False)["burned_area"].sum()


@st.cache_data(show_spinner=False)
def yearly_resources(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["year", "num_personnel", "num_heavy", "num_air"])
    return df.groupby("year", as_index=False)[["num_personnel", "num_heavy", "num_air"]].sum()


@st.cache_data(show_spinner=False)
def top_provinces_by_burned_area(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["province", "burned_area"])
    out = df.groupby("province", as_index=False)["burned_area"].sum()
    return out.sort_values("burned_area", ascending=False).head(top_n)


@st.cache_data(show_spinner=False)
def totals(df: pd.DataFrame) -> dict:
    return {
        "burned": float(df["burned_area"].sum()),
        "personnel": int(df["num_personnel"].sum()),
        "heavy": int(df["num_heavy"].sum()),
        "air": int(df["num_air"].sum()),
    }