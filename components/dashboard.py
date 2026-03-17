import streamlit as st
import time
import pandas as pd
import numpy as np
import os
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
# ⚙️ FUNCIONES PRINCIPALES DEL SISTEMA
# =====================================================
def generar_predicciones():
    """Genera predicciones automáticas"""
    with st.spinner("Procesando datos y generando predicciones..."):
        try:
            predictor = st.session_state.predictor
            
            progress_bar = st.progress(0)
            status_text = st.empty()

            progress_bar.progress(25)
            status_text.text("🔄 Cargando dataset mensual...")
            
            # Cargar dataset mensual
            ruta_dataset = "dataset/dataset_mensual_generado.xlsx"
            
            if os.path.exists(ruta_dataset):
                df_mensual = pd.read_excel(ruta_dataset)
                st.success(f"✅ Dataset cargado: {len(df_mensual)} registros")
            else:
                st.error(f"❌ No se encontró: {ruta_dataset}")
                return

            progress_bar.progress(50)
            status_text.text("🎯 Preparando características...")
            
            # Preparar features
            df_preparado = predictor.preparar_features(df_mensual)

            if len(df_preparado) == 0:
                mostrar_modal("error", "No hay datos suficientes")
                return

            progress_bar.progress(75)
            
            # Entrenar modelo si no está entrenado
            if predictor.model is None or not predictor.is_trained:
                status_text.text("🤖 Entrenando modelo...")
                modelo, metricas = predictor.entrenar_modelo(df_preparado)
                if metricas:
                    st.success(f"✅ Modelo entrenado - R²: {metricas.get('R2', 0):.3f}")
                predictor.guardar_modelo('modelo_compras/')

            progress_bar.progress(90)
            status_text.text("📊 Generando predicciones...")
            
            # Generar predicciones
            resultados_prediccion = predictor.predecir_consumo(df_preparado)
            
            # Obtener el último registro de cada producto del dataset mensual
            df_ultimos = df_mensual.sort_values(['producto_estado', 'mes']).groupby('producto_estado').last().reset_index()
            
            # Seleccionar columnas que necesitamos
            columnas_necesarias = ['producto_estado', 'descripcion', 'inventario_actual', 'precio_unitario', 'estado']
            columnas_existentes = [col for col in columnas_necesarias if col in df_ultimos.columns]
            
            # Unir las predicciones con los datos del dataset mensual
            df_final = pd.merge(
                resultados_prediccion[['producto_estado', 'consumo_predicho']],
                df_ultimos[columnas_existentes],
                on='producto_estado',
                how='inner'
            )
            
            st.session_state.resultados = df_final
            st.success(f"✅ Predicciones generadas: {len(df_final)} productos")

            progress_bar.progress(100)
            mostrar_modal("success", "✅ ¡Predicciones generadas!")

        except Exception as e:
            mostrar_modal("error", f"Error: {str(e)}")
            st.error(f"Error detallado: {e}")

def mostrar_resultados_detallados():
    """Muestra los resultados de las predicciones"""
    
    resultados_prediccion = st.session_state.resultados

    if resultados_prediccion is None:
        st.error("No hay datos disponibles")
        return
    
    # ==============================================
    # 🎯 SELECTOR DE TIPO DE PREDICCIÓN
    # ==============================================
    st.subheader("🎯 Selecciona el tipo de predicción")
    
    opcion_prediccion = st.radio(
        "**Selecciona el tipo de predicción a visualizar:**",
        ["📅 Predicción Mensual", "📊 Predicción Trimestral", "🎯 Predicción Anual"],
        horizontal=True,
        key="selector_prediccion"
    )
    
    # Crear copia de los resultados para no modificar los originales
    df_resultados = resultados_prediccion.copy()
    
    # Aplicar multiplicador según el tipo de predicción
    if opcion_prediccion == "📅 Predicción Mensual":
        titulo = "📊 Predicción Mensual"
        multiplicador = 1
    elif opcion_prediccion == "📊 Predicción Trimestral":
        titulo = "📊 Predicción Trimestral (3 meses)"
        multiplicador = 3
    elif opcion_prediccion == "🎯 Predicción Anual":
        titulo = "🎯 Predicción Anual (12 meses)"
        multiplicador = 12
    
    # Multiplicar el consumo predicho si existe
    if 'consumo_predicho' in df_resultados.columns:
        df_resultados['consumo_predicho'] = df_resultados['consumo_predicho'] * multiplicador
    
    # ==============================================
    # 📊 MÉTRICAS PRINCIPALES
    # ==============================================
    st.subheader(f"{titulo}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'inventario_actual' in df_resultados.columns and 'precio_unitario' in df_resultados.columns:
            # Calcular valor total del inventario actual
            valor_inventario = (df_resultados['inventario_actual'] * df_resultados['precio_unitario']).sum()
            st.metric("Valor Inventario Actual", f"S/{valor_inventario:,.2f}")
        elif 'precio_unitario' in df_resultados.columns:
            # Solo precio promedio si no hay inventario
            precio_promedio = df_resultados['precio_unitario'].mean()
            st.metric("Precio Promedio", f"S/{precio_promedio:,.2f}")
    
    with col2:
        if 'consumo_predicho' in df_resultados.columns:
            consumo_total = df_resultados['consumo_predicho'].sum()
            st.metric("Consumo Predicho Total", f"S/{consumo_total:,.0f}")
    
    with col3:
        total_productos = df_resultados['producto_estado'].nunique()
        st.metric("Total Productos", f"{total_productos:,}")

    # ==============================================
    # 📋 TABLA DE PREDICCIONES
    # ==============================================
    st.subheader("📋 Tabla de Predicciones")
    
    # Crear DataFrame para mostrar
    df_tabla = df_resultados.copy()
    
    # Agregar número secuencial
    df_tabla.insert(0, '#', range(1, len(df_tabla) + 1))
    
    # Renombrar columnas
    df_tabla = df_tabla.rename(columns={
        'producto_estado': 'ID Producto',
        'descripcion': 'Descripción',
        'inventario_actual': 'Inventario Actual',
        'precio_unitario': 'Precio Unitario',
        'consumo_predicho': 'Consumo Predicho',
        'estado': 'Estado'
    })
    
    # Definir columnas en el orden deseado
    columnas_mostrar = ['#', 'ID Producto', 'Descripción', 'Inventario Actual', 
                       'Precio Unitario', 'Consumo Predicho', 'Estado']
    
    # Filtrar solo las columnas que existen
    columnas_mostrar = [col for col in columnas_mostrar if col in df_tabla.columns]
    
    # Formatear valores
    if 'Precio Unitario' in df_tabla.columns:
        df_tabla['Precio Unitario'] = df_tabla['Precio Unitario'].apply(
            lambda x: f"S/{float(x):,.2f}" if pd.notnull(x) else "S/0.00"
        )
    
    # Formatear valores numéricos como enteros
    for col in ['Inventario Actual', 'Consumo Predicho']:
        if col in df_tabla.columns:
            df_tabla[col] = df_tabla[col].apply(
                lambda x: f"{int(float(x)):,}" if pd.notnull(x) else "0"
            )
    
    # Ordenar por Consumo Predicho descendente
    if 'Consumo Predicho' in df_tabla.columns:
        df_tabla['_orden'] = df_tabla['Consumo Predicho'].str.replace(',', '').astype(float)
        df_tabla = df_tabla.sort_values('_orden', ascending=False)
        df_tabla = df_tabla.drop('_orden', axis=1)
    
    # Mostrar tabla
    st.dataframe(
        df_tabla[columnas_mostrar],
        use_container_width=True,
        height=500,
        hide_index=True
    )
    
    st.caption(f"Mostrando {len(df_tabla):,} productos - {opcion_prediccion}")

    # ==============================================
    # 📥 EXPORTAR DATOS
    # ==============================================
    st.subheader("📥 Exportar Resultados")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv_tabla = df_tabla[columnas_mostrar].to_csv(index=False)
        nombre_archivo = "predicciones_mensuales.csv"
        if opcion_prediccion == "📊 Predicción Trimestral":
            nombre_archivo = "predicciones_trimestrales.csv"
        elif opcion_prediccion == "🎯 Predicción Anual":
            nombre_archivo = "predicciones_anuales.csv"
            
        st.download_button(
            label=f"📋 Descargar {opcion_prediccion.split(' ')[1]}",
            data=csv_tabla,
            file_name=nombre_archivo,
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        csv_original = df_resultados.to_csv(index=False)
        st.download_button(
            label="📊 Datos Completos",
            data=csv_original,
            file_name="predicciones_detalladas.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col3:
        # Exportar solo productos críticos
        if 'estado' in df_resultados.columns:
            df_criticos = df_resultados[df_resultados['estado'].isin(['QUIEBRE', 'ALTA'])]
            if len(df_criticos) > 0:
                csv_criticos = df_criticos.to_csv(index=False)
                st.download_button(
                    label="🚨 Productos Críticos",
                    data=csv_criticos,
                    file_name="productos_criticos.csv",
                    mime="text/csv",
                    use_container_width=True
                )

# =====================================================
# 📊 DASHBOARD PRINCIPAL
# =====================================================
def mostrar_dashboard():
    st.markdown("<h2 style='text-align: center;'>📊 Dashboard de Predicción de Consumo</h2>", unsafe_allow_html=True)

    # Botones principales
    if st.button("🚀 Generar Predicciones de Consumo", type="primary", use_container_width=True):
        generar_predicciones()
        st.rerun()
    
    # Verificar si tenemos el dataset mensual
    ruta_dataset = "dataset/dataset_mensual_generado.xlsx"
    
    if not os.path.exists(ruta_dataset):
        st.error(f"❌ No se encontró el archivo: {ruta_dataset}")
        st.warning("Por favor, asegúrate de que el archivo 'dataset_mensual_generado.xlsx' esté en la carpeta 'dataset/'")
        return
    
    # Si tenemos el dataset, mostrar información
    try:
        df_mensual = pd.read_excel(ruta_dataset)        
    except Exception as e:
        st.error(f"❌ Error al cargar el dataset: {e}")
        return

    # Mostrar resultados si existen
    if st.session_state.get('resultados') is not None:
        mostrar_resultados_detallados()
    else:
        st.info("💡 Haz clic en 'Generar Predicciones de Consumo' para ver los resultados")

# Función para inicializar el dashboard
def inicializar_dashboard():
    """Inicializar el dashboard"""
    inicializar_sistema()
    mostrar_dashboard()