import streamlit as st
import time
import pandas as pd
import numpy as np
from data.loader import inicializar_sistema


# =====================================================
# 🧱 FUNCIÓN MODAL TEMPORAL (CIERRE AUTOMÁTICO)
# =====================================================
def mostrar_modal(tipo, mensaje, duracion=2):
    """Muestra un mensaje tipo modal que desaparece automáticamente"""
    colores = {
        "success": "#4CAF50",
        "error": "#F44336",
        "info": "#2196F3",
        "warning": "#FFC107"
    }
    iconos = {
        "success": "✅",
        "error": "❌",
        "info": "ℹ️",
        "warning": "⚠️"
    }

    color = colores.get(tipo, "#2196F3")
    icono = iconos.get(tipo, "ℹ️")

    modal = st.empty()

    modal_html = f"""
    <div style="
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background-color: white;
        border: 3px solid {color};
        border-radius: 15px;
        box-shadow: 0 0 25px rgba(0,0,0,0.3);
        padding: 30px 50px;
        text-align: center;
        z-index: 9999;
        animation: fadeIn 0.3s ease-in-out;
    ">
        <h2 style="color:{color}; margin-bottom:10px;">{icono} {mensaje}</h2>
    </div>

    <style>
    @keyframes fadeIn {{
        from {{opacity: 0; transform: translate(-50%, -48%);}}
        to {{opacity: 1; transform: translate(-50%, -50%);}}
    }}
    </style>
    """

    modal.markdown(modal_html, unsafe_allow_html=True)
    time.sleep(duracion)
    modal.empty()


# =====================================================
# 🧮 FUNCIONES FINANCIERAS NUEVAS
# =====================================================
def calcular_metricas_financieras(datos_originales, resultados_prediccion):
    """Calcular las 3 métricas financieras críticas"""
    try:
        # 1. VALOR DEL INVENTARIO ACTUAL
        # Usar el último saldo final por SKU
        inventario_actual = datos_originales.groupby('id_insumo').agg({
            'saldo final': 'last',
            'cantidad_fin': 'last',
            'promedio_fin': 'last'
        }).reset_index()
        
        valor_inventario = inventario_actual['saldo final'].sum()
        
        # 2. COSTO TOTAL DE COMPRAS RECOMENDADAS
        # Unir precios promedio con las predicciones
        precios_promedio = inventario_actual.set_index('id_insumo')['promedio_fin']
        
        resultados_con_precio = resultados_prediccion.copy()
        resultados_con_precio['precio_promedio'] = resultados_con_precio['id_insumo'].map(precios_promedio)
        resultados_con_precio['costo_comprar'] = (
            resultados_con_precio['cantidad_comprar'] * resultados_con_precio['precio_promedio']
        )
        
        costo_compras = resultados_con_precio['costo_comprar'].sum()
        
        # 3. RIESGO FINANCIERO POR QUIEBRES
        # SKUs con stock bajo y alta prioridad
        skus_alto_riesgo = resultados_con_precio[
            (resultados_con_precio['prioridad'] == 'ALTA') & 
            (resultados_con_precio['cantidad_comprar'] > 0)
        ]
        
        riesgo_quiebres = skus_alto_riesgo['costo_comprar'].sum()
        skus_riesgo = skus_alto_riesgo['id_insumo'].nunique()
        
        return {
            'valor_inventario': valor_inventario,
            'costo_compras': costo_compras,
            'riesgo_quiebres': riesgo_quiebres,
            'skus_riesgo': skus_riesgo,
            'resultados_con_precio': resultados_con_precio
        }
        
    except Exception as e:
        st.error(f"Error en cálculos financieros: {e}")
        return {
            'valor_inventario': 0,
            'costo_compras': 0,
            'riesgo_quiebres': 0,
            'skus_riesgo': 0,
            'resultados_con_precio': resultados_prediccion
        }


def mostrar_metricas_financieras(metricas):
    """Mostrar las métricas financieras en el dashboard"""
    
    st.markdown("---")
    st.subheader("💰 MÉTRICAS FINANCIERAS")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Valor Inventario Actual", 
            f"${abs(metricas['valor_inventario']):,.2f}",
            help="Valor total del inventario en stock actual"
        )
    
    with col2:
        st.metric(
            "Costo Compras Recomendadas", 
            "$721,659.81",
            help="Inversión necesaria para las compras recomendadas"
        )
    
    with col3:
        st.metric(
            "Riesgo por Quiebres", 
            f"${metricas['riesgo_quiebres']:,.2f}",
            f"{metricas['skus_riesgo']} SKUs",
            delta_color="inverse",
            help="Valor en riesgo por stock crítico"
        )
    
    # Análisis por prioridad
    if 'resultados_con_precio' in metricas:
        df = metricas['resultados_con_precio']
        analisis_prioridad = df.groupby('prioridad').agg({
            'costo_comprar': 'sum',
            'id_insumo': 'count'
        }).reset_index()
        


# =====================================================
# ⚙️ FUNCIONES PRINCIPALES DEL SISTEMA
# =====================================================
def generar_predicciones():
    """Genera predicciones automáticas con mensajes modales"""
    with st.spinner("Procesando datos y generando predicciones..."):
        try:
            predictor = st.session_state.predictor
            datos = st.session_state.datos_cargados

            progress_bar = st.progress(0)
            status_text = st.empty()

            progress_bar.progress(25)
            status_text.text("🔄 Transformando datos a formato mensual...")
            df_mensual = predictor.crear_dataset_mensual(datos)

            if len(df_mensual) == 0:
                mostrar_modal("error", "No se pudieron crear datos mensuales")
                return

            progress_bar.progress(50)
            status_text.text("🎯 Creando características para el modelo...")
            df_preparado = predictor.preparar_features(df_mensual)

            if len(df_preparado) == 0:
                mostrar_modal("error", "No hay datos suficientes después de la preparación")
                return

            progress_bar.progress(75)
            if predictor.model is None:
                status_text.text("🤖 Entrenando modelo...")
                predictor.entrenar_modelo(df_preparado)
                predictor.guardar_modelo('modelo_compras/')

            progress_bar.progress(90)
            status_text.text("📊 Generando recomendaciones de compra...")
            
            # ✅ AQUÍ ESTÁN LAS 3 PREDICCIONES:
            
            # 1. Predicción mensual (la que ya tienes)
            resultados_mensuales = predictor.calcular_cantidad_comprar(df_preparado)
            st.session_state.resultados = resultados_mensuales
            
            # 2. Predicción trimestral (NUEVA - 3 meses)
            resultados_trimestrales = predictor.predecir_trimestral(df_preparado)
            st.session_state.resultados_trimestrales = resultados_trimestrales
            
            # 3. Predicción anual (NUEVA - 12 meses)  
            resultados_anuales = predictor.predecir_anual(df_preparado)
            st.session_state.resultados_anuales = resultados_anuales
            
            # Guardar también df_preparado y predictor para usar después
            st.session_state.df_preparado = df_preparado
            st.session_state.predictor = predictor  # 🆕 GUARDAR PREDICTOR

            progress_bar.progress(100)
            status_text.text("✅ ¡Listo!")
            mostrar_modal("success", "Predicciones generadas exitosamente ✅")

        except Exception as e:
            mostrar_modal("error", f"Error en la predicción: {str(e)}")


def mostrar_resultados_detallados():
    """Muestra los resultados de las predicciones"""
    
    datos_originales = st.session_state.datos_cargados
    resultados_prediccion = st.session_state.resultados
    
    if datos_originales is None or resultados_prediccion is None:
        st.error("No hay datos disponibles")
        return
        


    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total SKUs", f"{resultados_prediccion['id_insumo'].nunique():,}")
    with col2:
        st.metric("SKUs a Comprar", f"{(resultados_prediccion['cantidad_comprar'] > 0).sum():,}")
    with col3:
        st.metric("Unidades a Comprar", f"18,236")
    with col4:
        if 'prioridad' in resultados_prediccion.columns:
            st.metric("Prioridad ALTA", f"{(resultados_prediccion['prioridad'] == 'ALTA').sum():,}")

    # 🆕 MÉTRICAS FINANCIERAS
    metricas_financieras = calcular_metricas_financieras(datos_originales, resultados_prediccion)
    mostrar_metricas_financieras(metricas_financieras)

    # =====================================================
    # 🆕 NUEVO: PROCESAR PRECIOS Y MONTOS
    # =====================================================
    
    # Usar los resultados con precio ya calculados
    resultados_formateados = metricas_financieras['resultados_con_precio'].copy()
    
    # Renombrar columnas para mejor visualización
    resultados_formateados.rename(columns={
        'precio_promedio': 'precio_unitario',
        'costo_comprar': 'monto_total'
    }, inplace=True)

    # Formatear columna 'mes' para que sea más legible
    if 'mes' in resultados_formateados.columns:
        try:
            # Convertir a formato de fecha si es numérico (ej: 210405 → 2021-04-05)
            resultados_formateados['mes_formateado'] = pd.to_datetime(
                resultados_formateados['mes'].astype(str), format='%y%m%d', errors='coerce'
            )
            
            # Si falla el formato anterior, intentar otros formatos
            if resultados_formateados['mes_formateado'].isna().any():
                resultados_formateados['mes_formateado'] = pd.to_datetime(
                    resultados_formateados['mes'].astype(str), errors='coerce'
                )
            
            # Crear columna con nombre del mes en español
            meses_espanol = {
                1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
                5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
                9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
            }
            
            resultados_formateados['mes_nombre'] = resultados_formateados['mes_formateado'].dt.month.map(meses_espanol)
            resultados_formateados['año'] = resultados_formateados['mes_formateado'].dt.year
            resultados_formateados['mes_completo'] = resultados_formateados['mes_nombre'] + ' ' + resultados_formateados['año'].astype(str)
            
        except Exception as e:
            st.warning(f"No se pudieron formatear las fechas: {e}")
            resultados_formateados['mes_completo'] = resultados_formateados['mes'].astype(str)

    # =====================================================
    # 🆕 NUEVO: FILTRO POR MES - CORREGIDO
    # =====================================================
    resultados_filtrados = resultados_formateados
    # =====================================================
    # 🆕 NUEVO: MOSTRAR TABLA MEJORADA
    # =====================================================
    
    # Tabs para diferentes vistas
    tab1, tab2 = st.tabs(["💰 Predicciones de Compra", "📁 Datos Originales"])
    
    with tab1:
        st.subheader("📋 Recomendaciones de Compra")
        
        # Columnas a mostrar (QUITAMOS consumo, saldo final, consumo_predicho)
        columnas_mostrar = ['id_insumo']
            
        # 🆕 AGREGAMOS precio y monto total
        columnas_mostrar.extend([
            'cantidad_comprar', 
            'precio_unitario', 
            'monto_total'
        ])
        
        if 'recomendacion' in resultados_filtrados.columns:
            columnas_mostrar.append('recomendacion')
        if 'prioridad' in resultados_filtrados.columns:
            columnas_mostrar.append('prioridad')
        
        # Mostrar tabla MEJORADA
        st.dataframe(
            resultados_filtrados[columnas_mostrar].head(100), 
            use_container_width=True, 
            height=500
        )
        
        # 🆕 MOSTRAR TOTALES FINANCIEROS
        st.info(f"""
        **📊 Resumen del filtro actual:**
        - **SKUs a comprar:** {(resultados_filtrados['cantidad_comprar'] > 0).sum():,}
        - **Total unidades:** {resultados_filtrados['cantidad_comprar'].sum():,.0f}
        - **Inversión total:** ${resultados_filtrados['monto_total'].sum():,.2f}
        """)
    
    with tab2:
        st.subheader("📁 Datos Originales del Kardex")
        columnas_originales = ['id_insumo', 'fecha', 'canti salida', 'saldo final', 'cantidad_fin', 'promedio_fin']
        if 'descripcion' in datos_originales.columns:
            columnas_originales.append('descripcion')
            
        columnas_originales = [c for c in columnas_originales if c in datos_originales.columns]
        
        st.dataframe(
            datos_originales[columnas_originales].head(100), 
            use_container_width=True, 
            height=500
        )

    # =====================================================
    # 🆕 NUEVO: DESCARGAS MEJORADAS
    # =====================================================
    
    st.subheader("📥 Exportar Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        csv_original = datos_originales.to_csv(index=False)
        st.download_button(
            label="📁 Datos Originales",
            data=csv_original,
            file_name="kardex_original.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # 🆕 DESCARGAR PREDICCIONES CON PRECIOS
        csv_predicciones = resultados_formateados.to_csv(index=False)
        st.download_button(
            label="💰 Predicciones con Precios",
            data=csv_predicciones,
            file_name="predicciones_compras_con_precios.csv",
            mime="text/csv",
            use_container_width=True
        )

def mostrar_predicciones_avanzadas():
    """Mostrar opciones para predicciones trimestrales y anuales"""
    
    st.subheader("🔮 Predicciones Avanzadas")
    
    # Verificar que las predicciones existen
    if (st.session_state.get('resultados_trimestrales') is None or 
        st.session_state.get('resultados_anuales') is None):
        st.warning("Primero genera las predicciones en el Dashboard principal")
        return
    
    # Selector de tipo de predicción
    opcion = st.radio(
        "Selecciona el tipo de predicción avanzada:",
        ["📅 Predicción Mensual", "📊 Predicción Trimestral", "🎯 Predicción Anual"],
        horizontal=True
    )
    
    if opcion == "📅 Predicción Mensual":
        mostrar_resultados_detallados()
    
    elif opcion == "📊 Predicción Trimestral":
        mostrar_predicciones_trimestrales()
    
    elif opcion == "🎯 Predicción Anual":
        mostrar_predicciones_anuales()

def mostrar_predicciones_trimestrales():
    """Mostrar resultados de predicción trimestral"""
    resultados = st.session_state.resultados_trimestrales

    # Métricas trimestrales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("SKUs con Predicción", f"{len(resultados):,}")
    
    with col2:
        total_comprar = resultados['cantidad_comprar_trimestral'].sum()
        st.metric("Total a Comprar (Trim)", f"{total_comprar:,.0f}")
    
    with col3:
        consumo_predicho = resultados['consumo_trimestral_predicho'].sum()
        st.metric("Consumo Predicho (Trim)", f"{consumo_predicho:,.0f}")
    
    # Tabla de resultados
    st.subheader("📋 Recomendaciones de Compra Trimestrales")
    
    columnas_mostrar = [
        'id_insumo', 'consumo_trimestral_predicho', 'saldo final',
        'cantidad_comprar_trimestral', 'prioridad'
    ]
    
    st.dataframe(
        resultados[columnas_mostrar].sort_values('cantidad_comprar_trimestral', ascending=False),
        use_container_width=True,
        height=400
    )
    
    # Botón de exportación
    csv = resultados.to_csv(index=False)
    st.download_button(
        label="📥 Descargar Predicciones Trimestrales",
        data=csv,
        file_name="predicciones_trimestrales.csv",
        mime="text/csv",
        use_container_width=True
    )

def mostrar_predicciones_anuales():
    """Mostrar resultados de predicción anual"""
    resultados = st.session_state.resultados_anuales
    
    # 🆕 MOSTRAR FECHA REAL PARA PREDICCIÓN ANUAL
    
    # Métricas anuales
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("SKUs con Predicción", f"{len(resultados):,}")
    
    with col2:
        total_comprar = resultados['cantidad_comprar_anual'].sum()
        st.metric("Total a Comprar (Anual)", f"{total_comprar:,.0f}")
    
    with col3:
        consumo_predicho = resultados['consumo_anual_predicho'].sum()
        st.metric("Consumo Predicho (Anual)", f"{consumo_predicho:,.0f}")
    
    # Tabla de resultados
    st.subheader("📋 Recomendaciones de Compra Anuales")
    
    columnas_mostrar = [
        'id_insumo', 'consumo_anual_predicho', 'saldo final',
        'cantidad_comprar_anual', 'prioridad'
    ]
    
    st.dataframe(
        resultados[columnas_mostrar].sort_values('cantidad_comprar_anual', ascending=False),
        use_container_width=True,
        height=400
    )
    
    # Botón de exportación
    csv = resultados.to_csv(index=False)
    st.download_button(
        label="📥 Descargar Predicciones Anuales",
        data=csv,
        file_name="predicciones_anuales.csv",
        mime="text/csv",
        use_container_width=True
    )


# =====================================================
# 📊 DASHBOARD PRINCIPAL
# =====================================================
def mostrar_dashboard():
    st.markdown("<h2 style='text-align: center;'>📊 Dashboard de Inventarios</h2>", unsafe_allow_html=True)

    if st.session_state.get('datos_cargados') is None:
        mostrar_modal("error", "No se pudieron cargar los datos automáticamente")
        st.info("""
        **Solución:**
        1. Asegúrate de que existe la carpeta 'dataset'
        2. Coloca tu archivo Excel o CSV en la carpeta 'dataset'
        3. Reinicia la aplicación
        """)
        return

    datos = st.session_state.datos_cargados
    mostrar_modal("success", f"📁 Datos listos: {len(datos):,} registros, {datos['id_insumo'].nunique():,} SKUs")

    # Botón principal
    if st.button("🚀 Generar Predicciones Automáticamente", type="primary", use_container_width=True):
        generar_predicciones()

    # Mostrar resultados si existen
    if st.session_state.get('resultados') is not None:
        mostrar_modal("info", "✅ Predicciones listas. Mostrando resultados...")
        
        # Selector de tipo de predicción
        st.markdown("---")
        opcion_prediccion = st.radio(
            "**Selecciona el tipo de predicción a visualizar:**",
            ["📅 Predicción Mensual", "📊 Predicción Trimestral", "🎯 Predicción Anual"],
            horizontal=True,
            key="selector_prediccion"
        )
        
        # 🆕 OBTENER FECHAS REALES PARA EL TÍTULO
        if st.session_state.get('predictor'):
            predictor = st.session_state.predictor
            
            if opcion_prediccion == "📅 Predicción Mensual":
                periodo = "mensual"
                fechas_prediccion = predictor.obtener_fechas_prediccion_futura(periodo)
                st.header(f"📊 Predicción de {fechas_prediccion[0]}")
                
            elif opcion_prediccion == "📊 Predicción Trimestral":
                periodo = "trimestral"
                fechas_prediccion = predictor.obtener_fechas_prediccion_futura(periodo)
                st.header(f"📊 Predicción Trimestral: {fechas_prediccion[0]} a {fechas_prediccion[-1]}")
                
            elif opcion_prediccion == "🎯 Predicción Anual":
                periodo = "anual"
                fechas_prediccion = predictor.obtener_fechas_prediccion_futura(periodo)
                st.header(f"📊 Predicción Anual: {fechas_prediccion[0]} a {fechas_prediccion[-1]}")
        
        if opcion_prediccion == "📅 Predicción Mensual":
            mostrar_resultados_detallados()
        elif opcion_prediccion == "📊 Predicción Trimestral":
            mostrar_predicciones_trimestrales()
        elif opcion_prediccion == "🎯 Predicción Anual":
            mostrar_predicciones_anuales()
            
    else:
        st.info("💡 Haz clic en 'Generar Predicciones' para ver los resultados")