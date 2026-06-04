import copy
from typing import Dict, Optional

import folium
from branca.colormap import linear
from folium.features import GeoJsonTooltip
from folium.plugins import Fullscreen
import pandas as pd

from config import MAP_BOUNDS, MAP_CENTER, PROVINCE_NAME_MAP


def normalize_province_names(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["province_normalized"] = out["province"].map(PROVINCE_NAME_MAP).fillna(out["province"])
    return out


def create_choropleth_map(df: pd.DataFrame, geojson: Dict) -> Optional[folium.Map]:
    if df.empty:
        return None

    df_norm = normalize_province_names(df)

    agg = (
        df_norm.groupby("province_normalized", as_index=False)
        .agg(
            num_personnel=("num_personnel", "sum"),
            num_heavy=("num_heavy", "sum"),
            num_air=("num_air", "sum"),
            burned_area=("burned_area", "sum"),
        )
    )
    agg["total_resources"] = agg[["num_personnel", "num_heavy", "num_air"]].sum(axis=1)

    lookup = agg.set_index("province_normalized").to_dict(orient="index")

    geo = copy.deepcopy(geojson)
    for feature in geo.get("features", []):
        name = feature.get("properties", {}).get("name")
        info = lookup.get(name, {})
        props = feature.setdefault("properties", {})
        props["total_resources"] = int(info.get("total_resources", 0))
        props["num_personnel"] = int(info.get("num_personnel", 0))
        props["num_heavy"] = int(info.get("num_heavy", 0))
        props["num_air"] = int(info.get("num_air", 0))
        props["burned_area"] = float(info.get("burned_area", 0))

    values = agg["total_resources"]
    min_v = float(values.min()) if not values.empty else 0.0
    max_v = float(values.max()) if not values.empty else 1.0
    if max_v <= min_v:
        max_v = min_v + 1.0

    colormap = linear.YlOrRd_09.scale(min_v, max_v)
    colormap.caption = "Total resources"

    def style_function(feature):
        v = feature.get("properties", {}).get("total_resources", 0)
        return {
            "fillColor": colormap(v) if v else "#f2f2f2",
            "color": "#333333",
            "weight": 0.6,
            "fillOpacity": 0.75,
        }

    m = folium.Map(location=MAP_CENTER, zoom_start=6, control_scale=True)
    Fullscreen(
        position="bottomright",
        title="Full screen",
        title_cancel="Exit Full Screen",
    ).add_to(m)

    m.fit_bounds(MAP_BOUNDS)

    folium.GeoJson(
        geo,
        name="Provinces",
        style_function=style_function,
        highlight_function=lambda _: {
            "weight": 2,
            "color": "#000000",
            "fillOpacity": 0.9,
        },
        tooltip=GeoJsonTooltip(
            fields=[
                "name",
                "total_resources",
                "num_personnel",
                "num_heavy",
                "num_air",
                "burned_area",
            ],
            aliases=[
                "Province:",
                "Total resources:",
                "Personnel:",
                "Heavy:",
                "Air:",
                "Burned area (ha):",
            ],
            localize=True,
            sticky=True,
            labels=True,
        ),
    ).add_to(m)

    colormap.add_to(m)
    return m