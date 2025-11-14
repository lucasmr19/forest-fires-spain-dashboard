import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import json

# Configuración de la página
st.set_page_config(
    page_title='Incendios Forestales en España',
    page_icon='🔥',
    initial_sidebar_state='expanded',
    layout='wide'
)

# **Carga de datos**
@st.cache_data
def load_data(filepath='incendios.csv'):
    """
    Carga el conjunto de datos de incendios desde un archivo CSV.
    """
    data = pd.read_csv(filepath, sep=';')
    return data

@st.cache_data
def load_geojson(filepath='spain-provinces.geojson'):
    """
    Carga el archivo GeoJSON de provincias.
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        geojson = json.load(file)
    return geojson


# **Filtrado de datos**
def filtrar_datos(datos, rango_anios, incluir_intencionados, incluir_no_intencionados):
    """
    Filtra los datos según el rango de años y los filtros de incendios intencionados/no intencionados.
    """
    # Filtrar por rango de años
    datos_filtrados = datos[(datos['anio'] >= rango_anios[0]) & (datos['anio'] <= rango_anios[1])]

    # Filtrar por tipo de incendio
    datos_filtrados['intencionado'] = datos_filtrados['idcausa'].between(400, 499)

    if not incluir_intencionados:
        datos_filtrados = datos_filtrados[~datos_filtrados['intencionado']]
    if not incluir_no_intencionados:
        datos_filtrados = datos_filtrados[datos_filtrados['intencionado']]

    return datos_filtrados

def normalizar_nombres_provincias(datos_filtrados, mapeo_nombres):
    """
    Normaliza los nombres de las provincias en el CSV para que coincidan con los nombres en el GeoJSON.
    """
    # Aplicar el mapeo para cambiar los nombres de las provincias en el CSV
    datos_filtrados['provincia_normalizada'] = datos_filtrados['provincia'].map(mapeo_nombres).fillna(datos_filtrados['provincia'])
    return datos_filtrados

# Crear el mapeo de nombres
mapeo_nombres = {
    'Leon': 'León',
    'A Coruna': 'A Coruña',
    'Bizkaia': 'Bizkaia/Vizcaya',
    'Gipuzkoa': 'Gipuzkoa/Guipúzcoa',
    'Alava': 'Araba/Álava',
    'Avila': 'Ávila',
    'Caceres': 'Cáceres',
    'Cordoba': 'Córdoba',
    'Jaen': 'Jaén',
    'Malaga': 'Málaga',
    'Cadiz': 'Cádiz',
    'Almeria': 'Almería',
    'Valencia': 'València/Valencia',
    'Alicante': 'Alacant/Alicante',
    'Castellon': 'Castelló/Castellón',
    'Islas Baleares': 'Illes Balears',
    'Santa Cruz de Tenerife': 'Santa Cruz De Tenerife'
}


# **Mapa coroplético**
def crear_mapa(datos_filtrados, geojson):
    """
    Crea un mapa coroplético que muestra los medios de extinción por provincia.
    """
    if datos_filtrados.empty:
        return None

    # Normalizar los nombres de las provincias
    datos_filtrados = normalizar_nombres_provincias(datos_filtrados, mapeo_nombres)

    # Sumar los medios por provincia
    medios_por_provincia = datos_filtrados.groupby('provincia_normalizada').agg({
        'numeromediospersonal': 'sum',
        'numeromediospesados': 'sum',
        'numeromediosaereos': 'sum',
        'perdidassuperficiales': 'sum',
        'idcausa': 'first'
    }).reset_index()

    # Crear un total de medios para visualizar
    medios_por_provincia['total_medios'] = medios_por_provincia[['numeromediospersonal', 'numeromediospesados', 'numeromediosaereos']].sum(axis=1)

    # Crear un diccionario para mapear la provincia con los valores adicionales
    provincias_info = medios_por_provincia.set_index('provincia_normalizada').to_dict(orient='index')

    # Crear el mapa centrado en España
    mapa = folium.Map(location=[40.4168, -3.7038], zoom_start=6, max_zoom=7, min_zoom=5)

    # Establecer límites de movimiento (para evitar mover el mapa más allá de España y las Islas Canarias)
    mapa.fit_bounds([
        [26.5, -18.5],  # Ampliamos un poco hacia el sur
        [44.5, 5.5]     # Ampliamos un poco hacia el norte y este
    ])
    mapa.options['maxBounds'] = [[26.5, -18.5], [44.5, 5.5]]
    mapa.options['maxBoundsViscosity'] = 1.0  # Impide que se salga de los límites

    # Añadir la capa Choropleth (coroplético) con bordes negros finos
    folium.Choropleth(
        geo_data=geojson,
        data=medios_por_provincia,
        columns=['provincia_normalizada', 'total_medios'],
        key_on='feature.properties.name',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=1,  # Borde visible
        line_color='black',  # Borde negro
        line_weight=0.5,  # Grosor del borde (ajustable para más finura)
        legend_name='Total de medios de extinción',
        nan_fill_color="white",
        nan_fill_opacity=0.5
    ).add_to(mapa)

    # Añadir GeoJson con tooltips y bordes negros finos
    folium.GeoJson(
        geojson,
        name="Provincias",
        tooltip=folium.GeoJsonTooltip(
            fields=['name', 'cod_prov'],
            aliases=['Provincia:', 'Código Provincia:'],
            localize=True,
            sticky=True,
            labels=True,
            style="""
                font-size: 14px;
                font-weight: bold;
                background-color: rgba(255, 255, 255, 0.7);
                border-radius: 5px;
                padding: 5px;
            """
        ),
        style_function=lambda x: {
            'fillColor': 'transparent',  # Fondo transparente
            'color': 'black',           # Borde negro
            'weight': 0.5               # Grosor fino del borde
        }
    ).add_to(mapa)

    # Crear los tooltips con la información adicional
    for feature in geojson['features']:
        provincia = feature['properties']['name']
        info = provincias_info.get(provincia, {})
        tooltip_content = f"""
            <b>Provincia:</b> {provincia}<br>
            <b>Código Provincia:</b> {feature['properties']['cod_prov']}<br>
            <b>Medios Personales:</b> {info.get('numeromediospersonal', 0)}<br>
            <b>Medios Pesados:</b> {info.get('numeromediospesados', 0)}<br>
            <b>Medios Aéreos:</b> {info.get('numeromediosaereos', 0)}<br>
            <b>Total de Medios:</b> {info.get('total_medios', 0)}<br>
            <b>Hectáreas Quemadas:</b> {info.get('perdidassuperficiales', 0)}<br>
        """
        folium.GeoJson(
            feature,
            tooltip=folium.Tooltip(tooltip_content, sticky=True),
            style_function=lambda x: {
                'fillColor': 'transparent',  # Fondo transparente
                'color': 'black',           # Borde negro
                'weight': 0.5               # Grosor fino del borde
            }
        ).add_to(mapa)

    return mapa





# **Gráfico de líneas**
def crear_grafico_lineas(datos_filtrados):
    """
    Crea un gráfico de líneas con el total de hectáreas quemadas por año.
    """
    # Agrupar por año y sumar las hectáreas quemadas
    hectareas_por_ano = datos_filtrados.groupby('anio')['perdidassuperficiales'].sum().reset_index()

    fig = px.line(
        hectareas_por_ano,
        x='anio',
        y='perdidassuperficiales',
        title='Hectáreas quemadas por año',
        labels={'anio': 'Año', 'perdidassuperficiales': 'Hectáreas Quemadas'},
        markers=True
    )
    fig.update_layout(xaxis_title="Año", yaxis_title="Hectáreas Quemadas")
    return fig


# **Gráfico de barras apiladas**
def crear_barras_apiladas(datos_filtrados):
    """
    Crea un gráfico de barras apiladas mostrando los recursos utilizados por año.
    """
    recursos_por_ano = datos_filtrados.groupby('anio').agg({
        'numeromediospersonal': 'sum',
        'numeromediospesados': 'sum',
        'numeromediosaereos': 'sum'
    }).reset_index()

    fig = px.bar(
        recursos_por_ano,
        x='anio',
        y=['numeromediospersonal', 'numeromediospesados', 'numeromediosaereos'],
        title='Recursos utilizados por año',
        labels={'value': 'Cantidad de recursos', 'anio': 'Año'},
        barmode='stack'
    )
    fig.update_layout(
        xaxis_title="Año",
        yaxis_title="Cantidad de Recursos",
        legend_title="Tipo de Recursos"
    )
    return fig


# **Interfaz de usuario**
def sidebar_controles(datos):
    """
    Crea los controles de interacción en la barra lateral.
    """
    st.sidebar.title("Controles de Interacción")

    # Rango de años
    min_year = int(datos['anio'].min())
    max_year = int(datos['anio'].max())
    rango_anios = st.sidebar.slider(
        "Selecciona el rango de años:",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        step=1
    )

    # Checkboxes para filtrar por intencionados/no intencionados
    incluir_intencionados = st.sidebar.checkbox("Incluir incendios intencionados", value=True)
    incluir_no_intencionados = st.sidebar.checkbox("Incluir incendios no intencionados", value=True)

    return rango_anios, incluir_intencionados, incluir_no_intencionados


# **Expander con información del dashboard**
def crear_expander_informacion():
    """
    Crea un expander que proporciona información sobre el dashboard.
    """
    with st.expander("Información del Dashboard"):
        st.markdown(
            """
            ### Propósito del Dashboard
            Este dashboard interactivo proporciona una visualización de los incendios forestales en España. 
            Los datos incluyen información sobre hectáreas quemadas, recursos utilizados y causas de los incendios.

            ### Integrantes del Grupo
            - Saúl de los Reyes
            - Lucas Miralles

            ### Fuente de Datos
            Los datos utilizados provienen de la plataforma Kaggle. Puedes acceder a la fuente oficial de datos en el siguiente [enlace](https://www.kaggle.com/).
            """,
            unsafe_allow_html=True
        )

# **Gráfico de provincias más afectadas**
def crear_grafico_provincias_mas_afectadas(datos_filtrados, top_n=10):
    """
    Crea un gráfico de barras horizontal que muestra las provincias más afectadas
    en términos de hectáreas quemadas.
    """
    # Agrupar por provincia y sumar las hectáreas quemadas
    hectareas_por_provincia = datos_filtrados.groupby('provincia').agg({'perdidassuperficiales': 'sum'}).reset_index()

    # Ordenar por hectáreas quemadas y tomar las "top_n" provincias
    hectareas_por_provincia = hectareas_por_provincia.sort_values(by='perdidassuperficiales', ascending=False).head(top_n)

    # Crear el gráfico de barras horizontal
    fig = px.bar(
        hectareas_por_provincia,
        x='perdidassuperficiales',
        y='provincia',
        orientation='h',
        title=f"Top {top_n} provincias más afectadas",
        labels={'perdidassuperficiales': 'Hectáreas Quemadas', 'provincia': 'Provincia'}
    )
    fig.update_layout(
        xaxis_title="Hectáreas Quemadas",
        yaxis_title="Provincia",
        yaxis=dict(categoryorder='total ascending')  # Orden ascendente
    )
    return fig

def panel_principal(datos_filtrados):
    """
    Crea el panel principal con dos columnas:
    1. Mapa de medios de extinción por provincia, gráfico de hectáreas quemadas y gráfico de recursos utilizados.
    2. Gráfico de provincias más afectadas por hectáreas quemadas y análisis complementario.
    """
    # Crear dos columnas, la primera será más grande
    col1, col2 = st.columns([2, 1])

    with col1:
        # Mapa de medios de extinción
        st.markdown("### Mapa de medios de extinción por provincia")
        mapa = crear_mapa(datos_filtrados, geojson)
        if mapa:
            st_folium(mapa, width=700, height=500)

        # Gráfico de hectáreas quemadas
        st.markdown("### Gráfico de tendencia de hectáreas quemadas")
        fig_lineas = crear_grafico_lineas(datos_filtrados)
        st.plotly_chart(fig_lineas, use_container_width=True)

        # Gráfico de recursos utilizados
        st.markdown("### Gráfico de tendencia de medios utilizados")
        fig_barras = crear_barras_apiladas(datos_filtrados)
        st.plotly_chart(fig_barras, use_container_width=True)

    with col2:
        # Panel Derecho
        st.markdown("### Análisis Complementario")
        # Gráfico adicional de provincias más afectadas
        fig_adicional = crear_grafico_provincias_mas_afectadas(datos_filtrados, top_n=10)
        st.plotly_chart(fig_adicional, use_container_width=True)

        # Información adicional
        crear_expander_informacion()



# **Script Principal**
if __name__ == "__main__":
    #path = 'C:\\Users\\TrendingPC\\Documents\\Ciencia e Ingeniería de Datos\\3er año\\Visualización de Datos\\Prácticas\\práctica 3\\datasets\\'
    
    # Cargar datos y geojson
    datos = load_data()
    geojson = load_geojson()


    # Filtrar datos según los controles seleccionados
    rango_anios, incluir_intencionados, incluir_no_intencionados = sidebar_controles(datos)
    datos_filtrados = filtrar_datos(datos, rango_anios, incluir_intencionados, incluir_no_intencionados)

    if datos_filtrados.empty:
        st.write("No hay datos disponibles para los filtros seleccionados.")
    else:
        panel_principal(datos_filtrados)




