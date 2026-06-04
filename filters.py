from typing import Tuple
import pandas as pd
import streamlit as st


@st.cache_data(show_spinner=False)
def filter_data(
    df: pd.DataFrame,
    year_range: Tuple[int, int],
    include_intentional: bool,
    include_unintentional: bool,
) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    if not include_intentional and not include_unintentional:
        return df.iloc[0:0].copy()

    min_year, max_year = year_range

    out = df.loc[df["year"].notna()].copy()
    out = out[(out["year"] >= min_year) & (out["year"] <= max_year)]

    if include_intentional and not include_unintentional:
        out = out[out["intentional"]]
    elif include_unintentional and not include_intentional:
        out = out[~out["intentional"]]

    return out