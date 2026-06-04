from pathlib import Path
from typing import Dict
import json

import pandas as pd
import streamlit as st


@st.cache_data(show_spinner=False)
def load_data(filepath: str = "incendios.csv") -> pd.DataFrame:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")

    df = pd.read_csv(path, sep=";", low_memory=False)

    rename_map = {
        "provincia": "province",
        "anio": "year",
        "perdidassuperficiales": "burned_area",
        "numeromediospersonal": "num_personnel",
        "numeromediospesados": "num_heavy",
        "numeromediosaereos": "num_air",
        "idcausa": "cause_id",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    defaults = {
        "province": "Unknown",
        "year": pd.NA,
        "burned_area": 0,
        "num_personnel": 0,
        "num_heavy": 0,
        "num_air": 0,
        "cause_id": 0,
    }
    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default

    df["province"] = df["province"].fillna("Unknown").astype(str)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["burned_area"] = pd.to_numeric(df["burned_area"], errors="coerce").fillna(0)
    df["num_personnel"] = pd.to_numeric(df["num_personnel"], errors="coerce").fillna(0)
    df["num_heavy"] = pd.to_numeric(df["num_heavy"], errors="coerce").fillna(0)
    df["num_air"] = pd.to_numeric(df["num_air"], errors="coerce").fillna(0)
    df["cause_id"] = pd.to_numeric(df["cause_id"], errors="coerce").fillna(0)

    # Se calcula una sola vez
    df["intentional"] = df["cause_id"].between(400, 499)

    return df


@st.cache_data(show_spinner=False)
def load_geojson(filepath: str = "spain-provinces.geojson") -> Dict:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"GeoJSON file not found: {filepath}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)