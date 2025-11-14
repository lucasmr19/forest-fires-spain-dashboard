# Forest Fires Spain Dashboard

[![Streamlit App](https://img.shields.io/badge/Streamlit-App-green)](https://forest-fires-spain.streamlit.app/)

## Overview

The **Forest Fires Spain Dashboard** is an interactive web application built with **Python**, **Streamlit**, and **Folium** that allows users to visualize and analyze forest fires across Spain. The dashboard provides insights into wildfire patterns, temporal trends, and geographic distribution through maps and customizable filters.

## Features

- **Interactive Map**: Visualize forest fire incidents across Spanish provinces using Folium maps.
- **Temporal Analysis**: Explore wildfire trends over time.
- **Customizable Filters**: Filter data by date, province, or fire characteristics.
- **GeoJSON Integration**: Province boundaries are visualized for contextual understanding.

## Demo

Access the live dashboard here: [Forest Fires Spain Dashboard](https://forest-fires-spain.streamlit.app/)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/lucasmr19/forest-fires-spain-dashboard.git
   cd forest-fires-spain-dashboard
   ```
2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the Streamlit app locally:

```bash
streamlit run streamlit_forest_fires_dashboard.py
```

The app will open in your default web browser.

## Data

- **incendios.csv**: Contains historical forest fire data in Spain.
- **spain-provinces.geojson**: GeoJSON file with province boundaries.

## File Structure

```
forest-fires-spain-dashboard/
├── incendios.csv
├── spain-provinces.geojson
├── streamlit_forest_fires_dashboard.py
├── requirements.txt
├── LICENSE
├── .gitattributes
└── README.md
```

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
