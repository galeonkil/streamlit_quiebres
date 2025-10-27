import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.predictor import PredictorComprasMejorado
import joblib
import os

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Predicción de Inventarios",
    page_icon="📊",
    layout="wide"
)

# Título principal
st.title("🚀 Sistema Inteligente de Predicción de Inventarios")
st.markdown("---")

# ================== CARGA AUTOMÁTICA DE DATOS ==================
@st.cache_data
def cargar_datos_automaticamente():
    """Cargar datos automáticamente desde la carpeta dataset"""
    try:
        # Buscar archivos en la carpeta dataset
        dataset_path = "dataset"
        archivos = os.listdir(dataset_path)
        
        # Prioridad: Excel primero, luego CSV
        archivos_excel = [f for f in archivos if f.endswith(('.xlsx', '.xls'))]
        archivos_csv = [f for f in archivos if f.endswith('.csv')]
        
        if archivos_excel:
            archivo = archivos_excel[0]  # Tomar el primer Excel
            df = pd.read_excel(f"{dataset_path}/{archivo}")
            st.success(f"✅ Datos cargados automáticamente desde: {archivo}")
            return df
        elif archivos_csv:
            archivo = archivos_csv[0]  # Tomar el primer CSV
            df = pd.read_csv(f"{dataset_path}/{archivo}")
            st.success(f"✅ Datos cargados automáticamente desde: {archivo}")
            return df
        else:
            st.error("❌ No se encontraron archivos en la carpeta 'dataset'")
            return None
            
    except Exception as e:
        st.error(f"❌ Error al cargar datos automáticamente: {str(e)}")
        return None

# ================== INICIALIZACIÓN AUTOMÁTICA ==================
def inicializar_sistema():
    """Inicializar el sistema con datos y modelo"""
    
    # Cargar datos automáticamente
    if 'datos_cargados' not in st.session_state:
        with st.spinner("🔄 Cargando datos automáticamente..."):
            datos = cargar_datos_automaticamente()
            if datos is not None:
                st.session_state.datos_cargados = datos
                st.session_state.datos_automaticos = True
    
    # Inicializar predictor
    if 'predictor' not in st.session_state:
        st.session_state.predictor = PredictorComprasMejorado(use_log_transform=True)
    
    # Intentar cargar modelo pre-entrenado
    if st.session_state.predictor.model is None:
        modelo_cargado = st.session_state.predictor.cargar_modelo('modelo_compras/')
        if modelo_cargado:
            st.success("✅ Modelo pre-entrenado cargado")
        else:
            st.info("🤖 No hay modelo pre-entrenado. Se entrenará uno nuevo.")

# ================== EJECUTAR INICIALIZACIÓN ==================
inicializar_sistema()

# ================== FUNCIONES PRINCIPALES ==================
def mostrar_dashboard():
    st.header("📊 Dashboard de Inventarios")
    
    if st.session_state.get('datos_cargados') is None:
        st.error("No se pudieron cargar los datos automáticamente.")
        st.info("""
        **Solución:**
        1. Asegúrate de que existe la carpeta 'dataset' 
        2. Coloca tu archivo Excel o CSV en la carpeta 'dataset'
        3. Reinicia la aplicación
        """)
        return
    
    # Mostrar información de los datos cargados
    datos = st.session_state.datos_cargados
    st.success(f"📁 Datos listos: {len(datos):,} registros, {datos['id_insumo'].nunique():,} SKUs")
    
    # Botón para generar predicciones
    if st.button("🚀 Generar Predicciones Automáticamente", type="primary", use_container_width=True):
        generar_predicciones()
    
    # Mostrar resultados si ya existen
    if st.session_state.get('resultados') is not None:
        mostrar_resultados_detallados()
def mostrar_reportes_graficos():
    st.header("📈 Reportes Gráficos Avanzados")
    
    if st.session_state.get('resultados') is None:
        st.warning("⚠️ Primero genera predicciones en el Dashboard para ver los reportes")
        return
    
    resultados = st.session_state.resultados
    
    # ================== ANÁLISIS DE RIESGOS ==================
    st.subheader("🚨 Análisis de Riesgos de Inventario")
    
    # 1. DETECCIÓN DE SOBRE STOCK
    st.markdown("### 📦 Análisis de Sobre Stock")
    
    # Calcular días de inventario
    resultados['dias_inventario'] = np.where(
        resultados['consumo_predicho'] > 0,
        (resultados['saldo final'] / resultados['consumo_predicho']) * 30,
        0
    )
    
    # Identificar sobre stock (más de 90 días de inventario)
    sobre_stock = resultados[resultados['dias_inventario'] > 90]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de torta - Distribución de sobre stock
        if not sobre_stock.empty:
            fig_sobre_stock = px.pie(
                values=[len(sobre_stock), len(resultados) - len(sobre_stock)],
                names=['Con Sobre Stock', 'Sin Sobre Stock'],
                title="📊 Porcentaje de SKUs con Sobre Stock",
                color=['Con Sobre Stock', 'Sin Sobre Stock'],
                color_discrete_map={'Con Sobre Stock': '#FF6B6B', 'Sin Sobre Stock': '#4ECDC4'}
            )
            st.plotly_chart(fig_sobre_stock, use_container_width=True)
        else:
            st.info("🎉 No se detectaron SKUs con sobre stock")
    
    with col2:
        # Top SKUs con mayor sobre stock
        if not sobre_stock.empty:
            top_sobre_stock = sobre_stock.nlargest(10, 'dias_inventario')[['id_insumo', 'dias_inventario', 'saldo final', 'consumo_predicho']]
            top_sobre_stock['exceso_dias'] = top_sobre_stock['dias_inventario'] - 90
            
            fig_top_sobre = px.bar(
                top_sobre_stock,
                x='exceso_dias',
                y='id_insumo',
                orientation='h',
                title="📈 Top 10 SKUs con Mayor Exceso de Inventario",
                labels={'exceso_dias': 'Días por encima del límite', 'id_insumo': 'SKU'},
                color='exceso_dias',
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig_top_sobre, use_container_width=True)
    
    # 2. DETECCIÓN DE QUIEBRES
    st.markdown("### ⚠️ Análisis de Riesgo de Quiebre")
    
    # Calcular riesgo de quiebre (stock < 15 días de consumo)
    resultados['riesgo_quiebre'] = resultados['dias_inventario'] < 15
    riesgo_quiebre = resultados[resultados['riesgo_quiebre'] == True]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de riesgo de quiebre
        if not riesgo_quiebre.empty:
            fig_riesgo_quiebre = px.pie(
                values=[len(riesgo_quiebre), len(resultados) - len(riesgo_quiebre)],
                names=['Riesgo Quiebre', 'Sin Riesgo'],
                title="📊 Porcentaje de SKUs con Riesgo de Quiebre",
                color=['Riesgo Quiebre', 'Sin Riesgo'],
                color_discrete_map={'Riesgo Quiebre': '#FFA500', 'Sin Riesgo': '#00D4AA'}
            )
            st.plotly_chart(fig_riesgo_quiebre, use_container_width=True)
        else:
            st.info("✅ No se detectaron SKUs con riesgo de quiebre")
    
    with col2:
        # Top SKUs con mayor riesgo de quiebre
        if not riesgo_quiebre.empty:
            top_riesgo = riesgo_quiebre.nsmallest(10, 'dias_inventario')[['id_insumo', 'dias_inventario', 'saldo final', 'consumo_predicho']]
            
            fig_top_riesgo = px.bar(
                top_riesgo,
                x='dias_inventario',
                y='id_insumo',
                orientation='h',
                title="📉 Top 10 SKUs con Mayor Riesgo de Quiebre",
                labels={'dias_inventario': 'Días de Inventario Restantes', 'id_insumo': 'SKU'},
                color='dias_inventario',
                color_continuous_scale='Oranges'
            )
            st.plotly_chart(fig_top_riesgo, use_container_width=True)
    
    # ================== GRÁFICOS ADICIONALES ==================
    st.markdown("### 📋 Gráficos de Distribución")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribución de días de inventario
        fig_distribucion_dias = px.histogram(
            resultados,
            x='dias_inventario',
            nbins=20,
            title="📊 Distribución de Días de Inventario",
            labels={'dias_inventario': 'Días de Inventario'},
            color_discrete_sequence=['#3366CC']
        )
        fig_distribucion_dias.add_vline(x=90, line_dash="dash", line_color="red", annotation_text="Límite Sobre Stock")
        fig_distribucion_dias.add_vline(x=15, line_dash="dash", line_color="orange", annotation_text="Límite Quiebre")
        st.plotly_chart(fig_distribucion_dias, use_container_width=True)
    
    with col2:
        # Gráfico de dispersión: Stock vs Consumo Predicho
        fig_dispersion = px.scatter(
            resultados,
            x='consumo_predicho',
            y='saldo final',
            size='cantidad_comprar',
            color='prioridad',
            title="🎯 Relación: Consumo Predicho vs Stock Actual",
            labels={'consumo_predicho': 'Consumo Predicho', 'saldo final': 'Stock Actual'},
            color_discrete_map={'ALTA': '#FF4B4B', 'MEDIA': '#FFA500', 'BAJA': '#00D4AA'},
            hover_data=['id_insumo']
        )
        st.plotly_chart(fig_dispersion, use_container_width=True)
    
    # ================== TABLAS DETALLADAS ==================
    st.markdown("### 📋 Listados Detallados")
    
    tab1, tab2, tab3 = st.tabs(["📦 SKUs con Sobre Stock", "⚠️ SKUs con Riesgo de Quiebre", "📊 Resumen General"])
    
    with tab1:
        if not sobre_stock.empty:
            st.dataframe(
                sobre_stock[['id_insumo', 'dias_inventario', 'saldo final', 'consumo_predicho', 'prioridad']].sort_values('dias_inventario', ascending=False),
                use_container_width=True
            )
            
            # Exportar sobre stock
            csv_sobre = sobre_stock.to_csv(index=False)
            st.download_button(
                label="📥 Descargar Lista de Sobre Stock",
                data=csv_sobre,
                file_name="sobre_stock_analisis.csv",
                mime="text/csv"
            )
        else:
            st.info("No hay SKUs con sobre stock detectados")
    
    with tab2:
        if not riesgo_quiebre.empty:
            st.dataframe(
                riesgo_quiebre[['id_insumo', 'dias_inventario', 'saldo final', 'consumo_predicho', 'prioridad']].sort_values('dias_inventario'),
                use_container_width=True
            )
            
            # Exportar riesgo quiebre
            csv_riesgo = riesgo_quiebre.to_csv(index=False)
            st.download_button(
                label="📥 Descargar Lista de Riesgo Quiebre",
                data=csv_riesgo,
                file_name="riesgo_quiebre_analisis.csv",
                mime="text/csv"
            )
        else:
            st.info("No hay SKUs con riesgo de quiebre detectados")
    
    with tab3:
        # Métricas resumen
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("SKUs Analizados", f"{len(resultados):,}")
        
        with col2:
            st.metric("Con Sobre Stock", f"{len(sobre_stock):,}")
        
        with col3:
            st.metric("Riesgo Quiebre", f"{len(riesgo_quiebre):,}")
        
        with col4:
            skus_optimos = len(resultados) - len(sobre_stock) - len(riesgo_quiebre)
            st.metric("Inventario Óptimo", f"{skus_optimos:,}")
        
        # Gráfico de resumen general
        fig_resumen = px.bar(
            x=['Sobre Stock', 'Riesgo Quiebre', 'Óptimo'],
            y=[len(sobre_stock), len(riesgo_quiebre), skus_optimos],
            title="📈 Resumen General del Estado del Inventario",
            labels={'x': 'Estado', 'y': 'Cantidad de SKUs'},
            color=['Sobre Stock', 'Riesgo Quiebre', 'Óptimo'],
            color_discrete_map={'Sobre Stock': '#FF6B6B', 'Riesgo Quiebre': '#FFA500', 'Óptimo': '#00D4AA'}
        )
        st.plotly_chart(fig_resumen, use_container_width=True)
def mostrar_registros():
    st.header("🔍 Buscar Registros")
    
    if st.session_state.get('datos_cargados') is None:
        st.error("No hay datos cargados en el sistema")
        return
    
    datos = st.session_state.datos_cargados.copy()
    
    # ================== CONVERTIR DATOS NUMÉRICOS ==================
    if 'canti salida' in datos.columns:
        datos['canti salida'] = pd.to_numeric(datos['canti salida'], errors='coerce').fillna(0)
    
    if 'saldo final' in datos.columns:
        datos['saldo final'] = pd.to_numeric(datos['saldo final'], errors='coerce').fillna(0)
    
    if 'canti entrada' in datos.columns:
        datos['canti entrada'] = pd.to_numeric(datos['canti entrada'], errors='coerce').fillna(0)
    
    # ================== BÚSQUEDA SIMPLE ==================
    st.subheader("Filtrar Registros")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        buscar_texto = st.text_input(
            "Buscar por ID o Descripción:", 
            placeholder="Ej: 501001001 o Llanta",
            key="buscar_texto"
        )
    
    with col2:
        limite_registros = st.slider("Registros a mostrar", 10, 100, 50)
    
    # Aplicar filtro de búsqueda
    if buscar_texto:
        mask_sku = datos['id_insumo'].astype(str).str.contains(buscar_texto, na=False, case=False)
        mask_desc = pd.Series(False, index=datos.index)
        if 'descripcion' in datos.columns:
            mask_desc = datos['descripcion'].astype(str).str.contains(buscar_texto, na=False, case=False)
        mask_total = mask_sku | mask_desc
        datos_filtrados = datos[mask_total]
    else:
        datos_filtrados = datos
    
    # ================== ALERTAS DE PREDICCIÓN ==================
    if st.session_state.get('resultados') is not None and len(datos_filtrados) > 0:
        st.subheader("🚨 Alertas de Predicción")
        
        resultados = st.session_state.resultados
        skus_unicos = datos_filtrados['id_insumo'].unique()
        
        alertas_encontradas = 0
        
        for sku in skus_unicos[:10]:  # Mostrar máximo 10 SKUs
            info_sku = resultados[resultados['id_insumo'] == sku]
            
            if not info_sku.empty:
                info = info_sku.iloc[0]
                alertas_encontradas += 1
                
                # Determinar tipo de alerta
                if info['prioridad'] == 'ALTA':
                    with st.container():
                        st.error(f"**🚨 ALERTA CRÍTICA - SKU {sku}**")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Stock Actual", f"{info['saldo final']:.0f}")
                        with col2:
                            st.metric("Consumo Predicho", f"{info['consumo_predicho']:.0f}")
                        with col3:
                            st.metric("Comprar Urgente", f"{info['cantidad_comprar']:.0f}")
                        st.progress(0.2, text="🔄 Riesgo de quiebre inminente")
                        st.markdown("---")
                
                elif info['prioridad'] == 'BAJA':
                    with st.container():
                        st.warning(f"**📦 SOBRE STOCK - SKU {sku}**")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Stock Actual", f"{info['saldo final']:.0f}")
                        with col2:
                            st.metric("Consumo Predicho", f"{info['consumo_predicho']:.0f}")
                        with col3:
                            st.metric("Recomendación", "NO COMPRAR")
                        # Calcular días de inventario excedente
                        dias_inventario = (info['saldo final'] / info['consumo_predicho']) * 30 if info['consumo_predicho'] > 0 else 0
                        st.progress(0.8, text=f"📊 {dias_inventario:.0f} días de inventario")
                        st.markdown("---")
                
                else:  # PRIORIDAD MEDIA
                    with st.container():
                        st.info(f"**✅ SITUACIÓN NORMAL - SKU {sku}**")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Stock Actual", f"{info['saldo final']:.0f}")
                        with col2:
                            st.metric("Consumo Predicho", f"{info['consumo_predicho']:.0f}")
                        with col3:
                            st.metric("Comprar", f"{info['cantidad_comprar']:.0f}")
                        st.progress(0.5, text="📈 Inventario en nivel óptimo")
                        st.markdown("---")
        
        if alertas_encontradas == 0:
            st.info("ℹ️ No se encontraron predicciones para los SKUs filtrados")
    
    elif st.session_state.get('resultados') is None:
        st.warning("⚠️ **Genera predicciones primero** en el Dashboard para ver alertas de compra")
        if st.button("📊 Ir al Dashboard para generar predicciones"):
            # Esto recargará la app en la pestaña del dashboard
            st.session_state.current_page = "Dashboard"
            st.rerun()
    
    # ================== MOSTRAR RESULTADOS ==================
    st.subheader(f"📊 Resultados ({len(datos_filtrados)} registros)")
    
    if len(datos_filtrados) > 0:
        # Seleccionar columnas a mostrar
        columnas_mostrar = ['id_insumo', 'fecha', 'canti salida', 'saldo final']
        if 'descripcion' in datos_filtrados.columns:
            columnas_mostrar.append('descripcion')
        if 'canti entrada' in datos_filtrados.columns:
            columnas_mostrar.append('canti entrada')
        
        # Mostrar dataframe
        st.dataframe(
            datos_filtrados[columnas_mostrar].head(limite_registros),
            use_container_width=True,
            height=400
        )
        
        # Mostrar estadísticas simples
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("SKUs únicos", datos_filtrados['id_insumo'].nunique())
        
        with col2:
            try:
                total_consumo = datos_filtrados['canti salida'].sum()
                st.metric("Total consumo", f"{total_consumo:,.0f}")
            except:
                st.metric("Total consumo", "N/A")
        
        with col3:
            try:
                stock_promedio = datos_filtrados['saldo final'].mean()
                st.metric("Stock promedio", f"{stock_promedio:.0f}")
            except:
                st.metric("Stock promedio", "N/A")
            
    else:
        if buscar_texto:
            st.info("No se encontraron registros con ese criterio de búsqueda")
            
            if len(datos) > 0:
                with st.expander("Ver IDs disponibles como referencia"):
                    skus_sample = datos['id_insumo'].astype(str).unique()[:10]
                    for sku in skus_sample:
                        st.write(f"- {sku}")
        else:
            st.info("Ingresa un término de búsqueda para filtrar los registros")
    
    # ================== INFORMACIÓN GENERAL ==================
    st.markdown("---")
    st.subheader("📋 Información del Dataset")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total registros", f"{len(datos):,}")
    
    with col2:
        st.metric("SKUs únicos", f"{datos['id_insumo'].nunique():,}")
    
    with col3:
        if 'fecha' in datos.columns:
            try:
                fechas = pd.to_datetime(datos['fecha'], errors='coerce').dropna()
                if not fechas.empty:
                    fecha_min = fechas.min().strftime('%Y-%m-%d')
                    fecha_max = fechas.max().strftime('%Y-%m-%d')
                    st.metric("Rango fechas", f"{fecha_min} a {fecha_max}")
                else:
                    st.metric("Rango fechas", "No disponible")
            except:
                st.metric("Rango fechas", "Error")
        else:
            st.metric("Rango fechas", "N/A")
def generar_predicciones():
    """Generar predicciones automáticamente"""
    with st.spinner("Procesando datos y generando predicciones..."):
        try:
            predictor = st.session_state.predictor
            datos = st.session_state.datos_cargados
            
            # Progreso paso a paso
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 1. Crear dataset mensual
            progress_bar.progress(25)
            status_text.text("🔄 Transformando datos a formato mensual...")
            df_mensual = predictor.crear_dataset_mensual(datos)
            
            if len(df_mensual) == 0:
                st.error("❌ No se pudieron crear datos mensuales")
                return
            
            # 2. Preparar características
            progress_bar.progress(50)
            status_text.text("🎯 Creando características para el modelo...")
            df_preparado = predictor.preparar_features(df_mensual)
            
            if len(df_preparado) == 0:
                st.error("❌ No hay datos suficientes después de la preparación")
                return
            
            # 3. Entrenar modelo si es necesario
            progress_bar.progress(75)
            if predictor.model is None:
                status_text.text("🤖 Entrenando modelo...")
                predictor.entrenar_modelo(df_preparado)
                predictor.guardar_modelo('modelo_compras/')
            
            # 4. Generar predicciones
            progress_bar.progress(90)
            status_text.text("📊 Generando recomendaciones de compra...")
            resultados = predictor.calcular_cantidad_comprar(df_preparado)
            st.session_state.resultados = resultados
            
            progress_bar.progress(100)
            status_text.text("✅ ¡Listo!")
            st.success("Predicciones generadas exitosamente!")
            
        except Exception as e:
            st.error(f"❌ Error en la predicción: {str(e)}")

def mostrar_resultados_detallados():
    """Mostrar resultados de las predicciones"""
    resultados = st.session_state.resultados
    
    st.header("🎯 Resultados de Predicción")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_skus = len(resultados)
        st.metric("Total SKUs", f"{total_skus:,}")
    
    with col2:
        skus_comprar = (resultados['cantidad_comprar'] > 0).sum()
        st.metric("SKUs a Comprar", f"{skus_comprar:,}")
    
    with col3:
        total_unidades = resultados['cantidad_comprar'].sum()
        st.metric("Unidades a Comprar", f"{total_unidades:,.0f}")
    
    with col4:
        if 'prioridad' in resultados.columns:
            alta_prioridad = (resultados['prioridad'] == 'ALTA').sum()
            st.metric("Prioridad ALTA", f"{alta_prioridad:,}")
    
    # Mostrar tabla de resultados
    st.subheader("📋 Recomendaciones de Compra")
    columnas_mostrar = ['id_insumo', 'mes', 'consumo', 'saldo final', 
                       'consumo_predicho', 'cantidad_comprar', 'recomendacion', 'prioridad']
    
    columnas_mostrar = [col for col in columnas_mostrar if col in resultados.columns]
    
    st.dataframe(
        resultados[columnas_mostrar].head(100),
        use_container_width=True,
        height=500
    )
    
    # Botón de exportación
    st.subheader("📥 Exportar Resultados")
    csv = resultados.to_csv(index=False)
    st.download_button(
        label="📥 Descargar CSV Completo",
        data=csv,
        file_name="compras_recomendadas.csv",
        mime="text/csv",
        use_container_width=True
    )

# ================== MENÚ PRINCIPAL ==================
st.sidebar.title("📋 Navegación")
opcion = st.sidebar.radio(
    "Selecciona una opción:",
    ["📊 Dashboard","📈 Reportes Gráficos","📝 Registros","⚙️ Configuración"]
)

if opcion == "📊 Dashboard":
    mostrar_dashboard()
if opcion == "📈 Reportes Gráficos":
    mostrar_reportes_graficos()
elif opcion == "📝 Registros":  # ← NUEVA OPCIÓN
    mostrar_registros()
elif opcion == "⚙️ Configuración":
    st.header("⚙️ Configuración del Sistema")
    st.info("""
    **Funcionamiento automático:**
    - Los datos se cargan automáticamente desde la carpeta 'dataset'
    - El modelo se entrena o carga automáticamente
    - Solo haz clic en 'Generar Predicciones' para obtener resultados
    """)
    
    if st.session_state.get('datos_cargados') is not None:
        datos = st.session_state.datos_cargados
        st.success(f"✅ Datos cargados: {len(datos):,} registros")
        st.success(f"✅ SKUs únicos: {datos['id_insumo'].nunique():,}")
    
    if st.button("🔄 Reiniciar Sistema"):
        st.session_state.clear()
        st.rerun()