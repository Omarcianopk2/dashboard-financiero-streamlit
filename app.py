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

# 5 EMPRESAS A ELECCION
TICKERS_CUSTOM_FIVE = ['JPM', 'JNJ', 'PG', 'KO', 'XOM'] 


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
        # Añadir un try-except más específico para yfinance
        data = yf.download(tickers, period=period)['Close']
        if isinstance(data, pd.Series):
             # Si solo se descarga un ticker, yfinance devuelve una Serie
             data = data.to_frame() 
        data.ffill(inplace=True) 
        return data
    except Exception as e:
        st.error(f"Error al descargar datos. Asegúrate de que los tickers son válidos y hay conexión a internet: {e}")
        return pd.DataFrame()

# Cargar los datos
data_historica = load_data(ALL_TICKERS)

# RENOMBRAR COLUMNAS PARA MAYOR CLARIDAD
if not data_historica.empty:
    # Manejar el caso de un solo ticker descargado (data['Close'] sería una Serie, no un DataFrame)
    if 'Close' in data_historica.columns:
        # Esto es un manejo de caso límite que puede ocurrir en yfinance con un solo ticker
        data_historica.columns = [
            col.replace('SHY', 'Bonos_Tesoro_USA (SHY)')
               .replace('CETETRC.MX', 'CETES_Mexico (ETF)')
               .replace('MXN=X', 'USD/MXN')
               .replace('EURUSD=X', 'EUR/USD')
            for col in data_historica.columns
        ]
    else:
        # Renombrar en el caso de múltiples tickers
        data_historica.rename(columns={
            'SHY': 'Bonos_Tesoro_USA (SHY)',
            'CETETRC.MX': 'CETES_Mexico (ETF)',
            'MXN=X': 'USD/MXN',
            'EURUSD=X': 'EUR/USD'
        }, inplace=True)

if not data_historica.empty:
    # --- Transformación: Cálculo de Rendimientos ---
    data_normalizada = (data_historica / data_historica.iloc[0]) * 100
    rendimientos_diarios = data_historica.pct_change().dropna()

    # --- Sidebar: Filtros y Storytelling (NARRATIVA CON PROPÓSITO) ---
    st.sidebar.title("Análisis Financiero Táctico")
    st.sidebar.markdown("""
    **Propósito:** Este dashboard está diseñado para **gestionar el riesgo de concentración** en las acciones de alto crecimiento ('Big Seven') y evaluar estrategias de **diversificación** y cobertura cambiaria, con especial atención a la **perspectiva del inversor mexicano**.
    
    *Utiliza los filtros para personalizar tu análisis y buscar coberturas.*
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
    fecha_min = data_historica.index.min().to_pydatetime()
    fecha_max = data_historica.index.max().to_pydatetime()
    
    fecha_inicio = st.sidebar.date_input(
        "Fecha de Inicio", 
        value=fecha_min,
        min_value=fecha_min,
        max_value=fecha_max
    )
    fecha_fin = st.sidebar.date_input(
        "Fecha de Fin", 
        value=fecha_max,
        min_value=fecha_min,
        max_value=fecha_max
    )
    
    # Asegurar que la fecha de inicio no sea posterior a la fecha de fin
    if fecha_inicio > fecha_fin:
        st.sidebar.error("Error: La fecha de inicio no puede ser posterior a la fecha de fin.")
        # Usar el rango completo si hay error en las fechas, para evitar fallos
        fecha_inicio_ts = data_historica.index.min()
        fecha_fin_ts = data_historica.index.max()
    else:
        # Filtrar datos según las fechas seleccionadas
        fecha_inicio_ts = pd.Timestamp(fecha_inicio)
        fecha_fin_ts = pd.Timestamp(fecha_fin)
    
    # Aplicar filtros
    if activos_seleccionados:
        data_filtrada = data_normalizada.loc[fecha_inicio_ts:fecha_fin_ts, activos_seleccionados]
        rendimientos_filtrados = rendimientos_diarios.loc[fecha_inicio_ts:fecha_fin_ts, activos_seleccionados]
    else:
        # Manejar caso de no selección de activos
        data_filtrada = pd.DataFrame()
        rendimientos_filtrados = pd.DataFrame()


    # --- Dashboard Layout ---
    st.title("📈 Dashboard Financiero: Gestión de Riesgo en Big Tech y Cobertura MXN")

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
        ultimo_precio_eurusd = data_historica['EUR/USD'].iloc[-1]
        cambio_eurusd = (data_historica['EUR/USD'].iloc[-1] / data_historica['EUR/USD'].iloc[-2]) - 1
        col4.metric("EUR/USD", f"${ultimo_precio_eurusd:.4f}", f"{cambio_eurusd:.2%}")
    except:
        col4.metric("EUR/USD", "N/A", "N/A")

    # --- Separador ---
    st.markdown("---")
    
    # --- Fila 2: Visualizaciones Principales ---
    st.header("Análisis de Crecimiento y Volatilidad (Asimetría de Retornos)")
    
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        st.subheader("Crecimiento Acumulado (Base 100)")
        if not data_filtrada.empty:
            fig_crecimiento = px.line(
                data_filtrada,
                # Título que apoya la narrativa de asimetría
                title="Rendimiento Asimétrico: Comparativa de Crecimiento de Activos"
            )
            # Mejorar el layout para la narrativa (Eje Y representa % de crecimiento)
            fig_crecimiento.update_layout(yaxis_title="Índice de Crecimiento (%)")
            st.plotly_chart(fig_crecimiento, use_container_width=True)
        else:
            st.info("Selecciona activos y un rango de fechas válido para ver el gráfico de crecimiento.")


    with col_der:
        st.subheader("Distribución de Rendimientos Diarios (Volatilidad Comparada) ")
        
        # --- Histograma Comparativo de Volatilidad ---
        if not rendimientos_filtrados.empty and len(activos_seleccionados) > 0:
            
            # Transformar el DataFrame de rendimientos a formato "long" para Plotly
            df_long = rendimientos_filtrados.melt(ignore_index=False, var_name='Activo', value_name='Rendimiento Diario')
            
            fig_hist = px.histogram(
                df_long,
                x='Rendimiento Diario',
                color='Activo',
                nbins=100,
                opacity=0.7, 
                barmode='overlay', 
                # Título que apoya la narrativa de riesgo
                title="Comparación de la Volatilidad (Distribución de Rendimientos Diarios)"
            )
            
            fig_hist.update_layout(xaxis_title="Rendimiento Diario")
            
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Selecciona activos y un rango de fechas válido para ver el histograma comparativo de volatilidad.")

    # --- Separador ---
    st.markdown("---")

    # --- Fila 3: Alertas Automáticas y Correlación ---
    st.header("Alertas y Correlaciones (Gestión de Riesgo) ")
    
    col_alertas, col_corr = st.columns(2)
    
    with col_alertas:
        # --- Sistema de Alertas (Umbrales Tácticos y Realistas) ---
        st.subheader("Sistema de Alertas Automáticas (Puntos de Decisión) 🔔")
        
        # --- DEFINICIÓN DE UMBRALES TÁCTICOS ---
        umbral_nvda_correccion = 150.0 
        umbral_nvda_euforia = 750.0 
        umbral_usdmxn_debil = 19.00 
        umbral_usdmxn_fuerte = 17.00
        
        # --- MOSTRAR UMBRALES CON FORMATO LIMPIO (USANDO COLUMNAS) ---
        st.markdown("**Umbrales de Decisión:**")
        
        col_nvda_corr, col_nvda_euph, col_mxn_fuerte, col_mxn_debil = st.columns(4)
        
        col_nvda_corr.metric("NVDA Soporte Clave (Corr.)", f"${umbral_nvda_correccion:.2f}", "Riesgo Bajista")
        col_nvda_euph.metric("NVDA Euforia (Sobrecompra)", f"${umbral_nvda_euforia:.2f}", "Riesgo de Corrección")
        col_mxn_fuerte.metric("USD/MXN Peso Fuerte", f"${umbral_usdmxn_fuerte:.2f}", "Oportunidad USD")
        col_mxn_debil.metric("USD/MXN Peso Débil", f"${umbral_usdmxn_debil:.2f}", "Riesgo Cambiario")

        st.markdown("---")

        
        # Alerta 1: Corrección Agresiva / Euforia de Nvidia 
        try:
            precio_actual_nvda = data_historica['NVDA'].iloc[-1]
            
            if precio_actual_nvda < umbral_nvda_correccion:
                st.warning(f"🚨 CORRECCIÓN AGRESIVA: NVIDIA ({precio_actual_nvda:.2f}) ha caído por debajo del soporte clave de **${umbral_nvda_correccion:.2f}**. Riesgo de baja extendida.")
            elif precio_actual_nvda > umbral_nvda_euforia: 
                st.info(f"🚀 EUFORIA: NVIDIA ({precio_actual_nvda:.2f}) cotiza en zona de máximos ($750+), posible señal de sobrecompra o burbuja.")
            else:
                st.success(f"NVIDIA ({precio_actual_nvda:.2f}) se mantiene en rango operativo.")
        except:
            st.error("No se pudo verificar la alerta de NVIDIA.")
            
        # Alerta 2: Fortaleza o Debilidad Extrema del Peso Mexicano (USD/MXN)
        try:
            precio_actual_usdmxn = data_historica['USD/MXN'].iloc[-1]
            
            if precio_actual_usdmxn > umbral_usdmxn_debil:
                st.error(f"⚠️ RIESGO MXN: El USD/MXN ({precio_actual_usdmxn:.2f}) está **por encima de ${umbral_usdmxn_debil:.2f}** (Peso Débil). Momento de evaluar cobertura cambiaria.")
            elif precio_actual_usdmxn < umbral_usdmxn_fuerte:
                st.success(f"🟢 OPORTUNIDAD MXN: El USD/MXN ({precio_actual_usdmxn:.2f}) está **por debajo de ${umbral_usdmxn_fuerte:.2f}** (Peso Fuerte). Momento ideal para cambiar pesos a USD.")
            else:
                st.info(f"USD/MXN ({precio_actual_usdmxn:.2f}) se mantiene en rango neutro (${umbral_usdmxn_fuerte:.2f} - ${umbral_usdmxn_debil:.2f}).")
        except:
            st.error("No se pudo verificar la alerta de USD/MXN.")


    with col_corr:
        st.subheader("Matriz de Correlación (Mitigación de Riesgo)")
        if not rendimientos_filtrados.empty and len(activos_seleccionados) > 1:
            matriz_corr = rendimientos_filtrados.corr()
            
            # Escala de color divergente centrada en 0 (Rojo/Negativo - Blanco/Cero - Azul/Positivo)
            fig_corr = px.imshow(
                matriz_corr,
                text_auto=".2f", 
                aspect="auto",
                color_continuous_scale='RdBu_r', 
                zmin=-1, 
                zmax=1,
                # Título que apoya la narrativa de diversificación
                title="Correlación para Diversificación (Rendimientos Diarios)"
            )
            fig_corr.update_layout(xaxis=dict(tickangle=45)) 
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Selecciona más de un activo para ver la matriz de correlación.")
            
    # --- Separador ---
    st.markdown("---")
            
    # --- Fila 4: Datos Crudos ---
    st.subheader("Datos Históricos (Últimos 10 días) ")
    st.dataframe(data_historica[activos_seleccionados].tail(10))

else:
    st.error("No se pudieron cargar los datos. Revisa la conexión o los tickers.")