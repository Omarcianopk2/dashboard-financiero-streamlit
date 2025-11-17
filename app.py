import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Dashboard Financiero - Análisis de Activos",
    page_icon="📈",
    layout="wide"
)

# --- Definición de Tickers ---
# "Big Seven"
TICKERS_BIG_SEVEN = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA']

# === CAMBIO: 5 EMPRESAS DE MÉXICO (IPC) ===
TICKERS_CUSTOM_FIVE = ['WALMEX.MX', 'AMXL.MX', 'GMEXICOB.MX', 'FMX', 'GFNORTEO.MX'] 
# Walmex, America Movil, Grupo Mexico, Femsa, Banorte

# Tipos de Cambio
TICKERS_FX = ['MXN=X', 'EURUSD=X'] # USD/MXN y USD/EUR

# Bonos y Tasas (Usamos ETFs como proxy)
TICKERS_RATES = ['SHY', 'CETETRC.MX'] # SHY = Bonos Tesoro USA, CETETRC.MX = CETES Mexico

ALL_TICKERS = TICKERS_BIG_SEVEN + TICKERS_CUSTOM_FIVE + TICKERS_FX + TICKERS_RATES

# --- Carga de Datos con Caché ---
@st.cache_data(ttl=3600)
def load_data(tickers, period="5y"):
    """
    Descarga datos históricos de 'Close' para la lista de tickers
    y los devuelve en un DataFrame de pandas.
    """
    try:
        data = yf.download(tickers, period=period)['Close']
        data.ffill(inplace=True) 
        return data
    except Exception as e:
        st.error(f"Error al descargar datos: {e}")
        return pd.DataFrame()

# Cargar los datos
data_historica = load_data(ALL_TICKERS)

# RENOMBRAR COLUMNAS PARA MAYOR CLARIDAD
if not data_historica.empty:
    data_historica.rename(columns={
        'SHY': 'Bonos_Tesoro_USA (SHY)',
        'CETETRC.MX': 'CETES_Mexico (ETF)',
        'MXN=X': 'USD/MXN',
        'EURUSD=X': 'EUR/USD',
        # === CAMBIO: Renombrar tickers de México ===
        'WALMEX.MX': 'Walmex (WALMEX.MX)',
        'AMXL.MX': 'America Movil (AMXL.MX)',
        'GMEXICOB.MX': 'Grupo Mexico (GMEXICOB.MX)',
        'FMX': 'Femsa (FMX)',
        'GFNORTEO.MX': 'Banorte (GFNORTEO.MX)'
    }, inplace=True)

if not data_historica.empty:
    # --- Transformación: Cálculo de Rendimientos ---
    data_normalizada = (data_historica / data_historica.iloc[0]) * 100
    rendimientos_diarios = data_historica.pct_change().dropna()

    # --- Sidebar: Filtros y Storytelling ---
    st.sidebar.title("Análisis Financiero Interactivo")
    
    # === CAMBIO: Actualizar el storytelling ===
    st.sidebar.markdown("""
    Este dashboard compara el rendimiento de los **gigantes tecnológicos globales ('Big Seven')** contra un **portafolio de las empresas líderes en México (IPC)**. 
    
    Pone especial énfasis en la perspectiva del inversor mexicano, analizando el riesgo 
    del tipo de cambio (`USD/MXN`) y el rendimiento 'seguro' de los (`CETES_Mexico`).
    """)
    
    st.sidebar.header("Filtros del Dashboard")
    
    # Filtro de Activos (Multiselect)
    activos_disponibles = list(data_historica.columns)
    activos_seleccionados = st.sidebar.multiselect(
        "Selecciona Activos para Comparar",
        options=activos_disponibles,
        default=TICKERS_BIG_SEVEN # Inicia con las Big Seven
    )
    
    # Filtro de Rango de Fechas
    fecha_inicio = st.sidebar.date_input(
        "Fecha de Inicio", 
        value=data_historica.index.min().to_pydatetime(),
        min_value=data_historica.index.min().to_pydatetime(),
        max_value=data_historica.index.max().to_pydatetime()
    )
    fecha_fin = st.sidebar.date_input(
        "Fecha de Fin", 
        value=data_historica.index.max().to_pydatetime(),
        min_value=data_historica.index.min().to_pydatetime(),
        max_value=data_historica.index.max().to_pydatetime()
    )
    
    # Filtrar datos según las fechas seleccionadas
    fecha_inicio_ts = pd.Timestamp(fecha_inicio)
    fecha_fin_ts = pd.Timestamp(fecha_fin)
    
    # Aplicar filtros
    data_filtrada = data_normalizada.loc[fecha_inicio_ts:fecha_fin_ts, activos_seleccionados]
    rendimientos_filtrados = rendimientos_diarios.loc[fecha_inicio_ts:fecha_fin_ts, activos_seleccionados]

    # --- Dashboard Layout ---
    st.title("📈 Dashboard Financiero: Big Tech vs. Mercados Globales")

    # --- Fila 1: Tarjetas de Datos (KPIs) ---
    st.header("Métricas Clave (Último Día)")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # === KPI 1: APPLE ===
    try:
        ultimo_precio_aapl = data_historica['AAPL'].iloc[-1]
        cambio_aapl = (data_historica['AAPL'].iloc[-1] / data_historica['AAPL'].iloc[-2]) - 1
        col1.metric("Apple (AAPL)", f"${ultimo_precio_aapl:.2f}", f"{cambio_aapl:.2%}")
    except:
        col1.metric("Apple (AAPL)", "N/A", "N/A")

    # === KPI 2: USD/MXN ===
    try:
        ultimo_precio_usdmxn = data_historica['USD/MXN'].iloc[-1]
        cambio_usdmxn = (data_historica['USD/MXN'].iloc[-1] / data_historica['USD/MXN'].iloc[-2]) - 1
        col2.metric("USD/MXN", f"${ultimo_precio_usdmxn:.2f}", f"{cambio_usdmxn:.2%}")
    except:
        col2.metric("USD/MXN", "N/A", "N/A")

    # === KPI 3: CETES ===
    try:
        ultimo_precio_cetes = data_historica['CETES_Mexico (ETF)'].iloc[-1]
        cambio_cetes = (data_historica['CETES_Mexico (ETF)'].iloc[-1] / data_historica['CETES_Mexico (ETF)'].iloc[-2]) - 1
        col3.metric("CETES_Mexico (ETF)", f"${ultimo_precio_cetes:.2f}", f"{cambio_cetes:.2%}")
    except:
        col3.metric("CETES_Mexico (ETF)", "N/A", "N/A")

    # === KPI 4: EUR/USD ===
    try:
        # Usamos el nuevo nombre 'EUR/USD'
        ultimo_precio_eurusd = data_historica['EUR/USD'].iloc[-1]
        cambio_eurusd = (data_historica['EUR/USD'].iloc[-1] / data_historica['EUR/USD'].iloc[-2]) - 1
        # Formateamos a 4 decimales, que es común para EUR/USD
        col4.metric("EUR/USD", f"${ultimo_precio_eurusd:.4f}", f"{cambio_eurusd:.2%}")
    except:
        col4.metric("EUR/USD", "N/A", "N/A")

    # --- Fila 2: Visualizaciones Principales ---
    st.header("Análisis de Crecimiento y Volatilidad")
    
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        st.subheader("Crecimiento Acumulado (Base 100)")
        fig_crecimiento = px.line(
            data_filtrada,
            title="Comparativa de Crecimiento de Activos"
        )
        st.plotly_chart(fig_crecimiento, use_container_width=True)

    with col_der:
        st.subheader("Distribución de Rendimientos Diarios")
        if len(activos_seleccionados) > 0:
            
            # --- AQUÍ ESTÁ LA SOLUCIÓN ---
            # Agregamos un selector para elegir el activo del histograma
            activo_hist = st.selectbox(
                "Selecciona un activo para analizar su volatilidad:",
                options=activos_seleccionados
            )
            # ---------------------------------
            
            fig_hist = px.histogram(
                rendimientos_filtrados[activo_hist],
                nbins=100,
                title=f"Volatilidad de {activo_hist}"
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Selecciona al menos un activo para ver el histograma.")

    # --- Fila 3: Alertas Automáticas y Correlación ---
    st.header("Alertas y Correlaciones")
    
    col_alertas, col_corr = st.columns(2)
    
    with col_alertas:
        st.subheader("Sistema de Alertas Automáticas")
        
        # Alerta 1: Caída de Nvidia
        try:
            umbral_nvda = 800.0 # Umbral de ejemplo
            precio_actual_nvda = data_historica['NVDA'].iloc[-1]
            if precio_actual_nvda < umbral_nvda:
                st.warning(f"🚨 ALERTA BAJISTA: NVIDIA ({precio_actual_nvda:.2f}) ha caído por debajo del umbral de ${umbral_nvda:.2f}.")
            else:
                st.success(f"NVIDIA ({precio_actual_nvda:.2f}) se mantiene por encima del umbral de ${umbral_nvda:.2f}.")
        except:
            st.error("No se pudo verificar la alerta de NVIDIA.")
            
        # Alerta 2: Fortaleza del Peso (USD/MXN bajo)
        try:
            umbral_usdmxn = 17.50 # Umbral de ejemplo
            # Usamos el nuevo nombre 'USD/MXN'
            precio_actual_usdmxn = data_historica['USD/MXN'].iloc[-1]
            if precio_actual_usdmxn < umbral_usdmxn:
                st.warning(f"🚨 ALERTA TIPO DE CAMBIO: El USD/MXN ({precio_actual_usdmxn:.2f}) está por debajo del umbral de ${umbral_usdmxn:.2f} (Peso Fuerte).")
            else:
                st.success(f"USD/MXN ({precio_actual_usdmxn:.2f}) se mantiene por encima del umbral de ${umbral_usdmxn:.2f}.")
        except:
            st.error("No se pudo verificar la alerta de USD/MXN.")


    with col_corr:
        st.subheader("Matriz de Correlación de Rendimientos")
        if len(activos_seleccionados) > 1:
            matriz_corr = rendimientos_filtrados.corr()
            fig_corr = px.imshow(
                matriz_corr,
                text_auto=True,
                aspect="auto",
                color_continuous_scale='RdYlGn', # Rojo-Amarillo-Verde
                title="Correlación entre Activos Seleccionados"
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Selecciona más de un activo para ver la matriz de correlación.")
            
    # --- Fila 4: Datos Crudos ---
    st.subheader("Datos Históricos (Últimos 10 días)")
    st.dataframe(data_historica[activos_seleccionados].tail(10))

else:
    st.error("No se pudieron cargar los datos. Revisa la conexión o los tickers.")