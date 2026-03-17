import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

def mostrar_registros():
    st.header("🔍 Buscar Productos en Predicciones")
    
    # ================== VERIFICAR DATOS ==================
    if st.session_state.get('resultados') is None:
        st.error("❌ No hay predicciones generadas")
        st.info("Primero genera predicciones en el Dashboard")
        return
    
    resultados = st.session_state.resultados
    
    # ================== MOSTRAR INFO DEL DATASET ==================
    st.info(f"📊 Dataset de Predicciones: {len(resultados):,} productos-mes analizados")
    
    # ================== BÚSQUEDA ESPECÍFICA ==================
    st.subheader("🔎 Buscar Producto Específico")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        codigo_buscar = st.text_input(
            "Ingresa el código del producto:", 
            placeholder="Ej: 0617001023-N",
            key="buscar_codigo"
        )
    
    with col2:
        st.metric("Total productos", f"{len(resultados):,}")
    
    with col3:
        if 'estado' in resultados.columns:
            quiebres = resultados[resultados['estado'] == 'QUIEBRE'].shape[0]
            st.metric("🚨 En quiebre", quiebres)
    
    # ================== BUSCAR Y MOSTRAR RESULTADO ==================
    if codigo_buscar:
        # Buscar en la columna producto_estado
        resultados_filtrados = resultados[resultados['producto_estado'].astype(str).str.contains(codigo_buscar, na=False, case=False)]
        
        if len(resultados_filtrados) == 0:
            # Intentar buscar en otras columnas
            for col in ['descripcion', 'producto', 'codigo', 'id_producto']:
                if col in resultados.columns:
                    resultados_filtrados = resultados[resultados[col].astype(str).str.contains(codigo_buscar, na=False, case=False)]
                    if len(resultados_filtrados) > 0:
                        break
        
        if len(resultados_filtrados) > 0:
            st.success(f"✅ Encontrado: {len(resultados_filtrados)} registro(s)")
            
            # ================== MOSTRAR TABLA DETALLADA ==================
            st.subheader("📋 Información del Producto")
            
            # Seleccionar columnas para mostrar (priorizando las importantes)
            columnas_mostrar = []
            
            # Columnas principales (en el orden que muestras)
            columnas_prioridad = [
                'producto_estado',
                'descripcion', 
                'inventario_actual',
                'consumo_predicho',
                'precio_unitario',
                'valor_inventario',
                'estado',
                'prioridad',
                'cantidad_comprar'
            ]
            
            for col in columnas_prioridad:
                if col in resultados_filtrados.columns:
                    columnas_mostrar.append(col)
            
            # Formatear la tabla para mejor visualización
            resultados_mostrar = resultados_filtrados[columnas_mostrar].copy()
            
            # Formatear columnas numéricas
            if 'precio_unitario' in resultados_mostrar.columns:
                resultados_mostrar['precio_unitario'] = resultados_mostrar['precio_unitario'].apply(
                    lambda x: f"S/{x:,.2f}" if pd.notnull(x) else "S/0.00"
                )
            
            if 'valor_inventario' in resultados_mostrar.columns:
                resultados_mostrar['valor_inventario'] = resultados_mostrar['valor_inventario'].apply(
                    lambda x: f"S/{x:,.2f}" if pd.notnull(x) else "S/0.00"
                )
            
            # Mostrar tabla formateada
            st.dataframe(
                resultados_mostrar,
                use_container_width=True,
                height=min(400, len(resultados_filtrados) * 35 + 100)
            )
            
            # ================== MOSTRAR ESTADÍSTICAS DEL PRODUCTO ==================
            st.subheader("📊 Análisis del Producto")
            
            for _, fila in resultados_filtrados.iterrows():
                producto = fila.get('producto_estado', 'Producto')
                descripcion = fila.get('descripcion', 'Sin descripción')
                estado = fila.get('estado', 'DESCONOCIDO')
                inventario = fila.get('inventario_actual', 0)
                consumo_pred = fila.get('consumo_predicho', 0)
                precio = fila.get('precio_unitario', 0)
                valor_inv = fila.get('valor_inventario', 0)
                comprar = fila.get('cantidad_comprar', 0)
                prioridad = fila.get('prioridad', 'MEDIA')
                
                # Tarjeta de información
                if estado == 'QUIEBRE':
                    color_borde = "#FF6B6B"
                    icono = "🚨"
                    mensaje = "URGENTE - Necesita reposición inmediata"
                elif estado == 'SOBRE STOCK':
                    color_borde = "#FFA500"
                    icono = "📦"
                    mensaje = "Exceso de inventario - No comprar"
                else:
                    color_borde = "#00D4AA"
                    icono = "✅"
                    mensaje = "Nivel óptimo de inventario"
                
                st.markdown(f"""
                <div style='border: 2px solid {color_borde}; border-radius: 10px; padding: 15px; margin: 10px 0; background-color: #f8f9fa;'>
                    <h3 style='color: {color_borde}; margin-top: 0;'>{icono} {producto} - {estado}</h3>
                    <p><strong>Descripción:</strong> {descripcion}</p>
                    <div style='display: flex; justify-content: space-between;'>
                        <div>
                            <p><strong>📦 Inventario actual:</strong> {inventario:,}</p>
                            <p><strong>📈 Consumo predicho/mes:</strong> {consumo_pred:,.0f}</p>
                        </div>
                        <div>
                            <p><strong>💰 Precio unitario:</strong> S/{precio:,.2f}</p>
                            <p><strong>💵 Valor inventario:</strong> S/{valor_inv:,.2f}</p>
                        </div>
                        <div>
                            <p><strong>🛒 Cantidad a comprar:</strong> {comprar:,}</p>
                            <p><strong>⚡ Prioridad:</strong> {prioridad}</p>
                        </div>
                    </div>
                    <p style='font-style: italic; margin-top: 10px;'>{mensaje}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Gráfico simple del estado
                fig = go.Figure()
                
                # Agregar barra para inventario
                fig.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=inventario,
                    title={'text': "📦 Inventario Actual"},
                    domain={'x': [0, 0.3], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [0, max(inventario*2, 100)]},
                        'bar': {'color': color_borde},
                        'steps': [
                            {'range': [0, consumo_pred*0.3], 'color': "#FF6B6B"},
                            {'range': [consumo_pred*0.3, consumo_pred*2], 'color': "#00D4AA"},
                            {'range': [consumo_pred*2, max(inventario*2, 100)], 'color': "#FFA500"}
                        ]
                    }
                ))
                
                # Agregar barra para consumo predicho
                fig.add_trace(go.Indicator(
                    mode="number",
                    value=consumo_pred,
                    title={'text': "📈 Consumo Predicho"},
                    domain={'x': [0.35, 0.65], 'y': [0, 1]},
                    number={'suffix': "/mes"}
                ))
                
                # Agregar indicador de acción
                if estado == 'QUIEBRE':
                    accion_text = "COMPRAR URGENTE"
                    accion_valor = 100
                elif estado == 'SOBRE STOCK':
                    accion_text = "NO COMPRAR"
                    accion_valor = 10
                else:
                    accion_text = "COMPRAR NORMAL"
                    accion_valor = 50
                
                fig.add_trace(go.Indicator(
                    mode="gauge+number",
                    value=accion_valor,
                    title={'text': "🛒 Recomendación"},
                    domain={'x': [0.7, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': color_borde},
                        'steps': [
                            {'range': [0, 33], 'color': "#FF6B6B"},
                            {'range': [33, 66], 'color': "#FFA500"},
                            {'range': [66, 100], 'color': "#00D4AA"}
                        ]
                    },
                    number={'suffix': '%', 'font': {'size': 24}}
                ))
                
                fig.update_layout(
                    height=300,
                    margin=dict(l=20, r=20, t=50, b=20),
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # ================== MOSTRAR HISTORIAL SI HAY DATOS ORIGINALES ==================
            if st.session_state.get('datos_cargados') is not None and len(resultados_filtrados) > 0:
                
                datos_originales = st.session_state.datos_cargados.copy()
                producto_codigo = resultados_filtrados.iloc[0]['producto_estado']
                
                # Buscar en datos originales
                if 'producto_estado' in datos_originales.columns:
                    historial = datos_originales[datos_originales['producto_estado'] == producto_codigo]
                    
                    if len(historial) > 0:
                        # Mostrar últimas 20 transacciones
                        columnas_historial = []
                        for col in ['fecha', 'canti salida', 'canti entrada', 'mes', 'anio']:
                            if col in historial.columns:
                                columnas_historial.append(col)
                        
                        st.write(f"📊 **{len(historial)} transacciones históricas encontradas**")
                        st.dataframe(
                            historial[columnas_historial].sort_values('fecha', ascending=False).head(20),
                            use_container_width=True,
                            height=300
                        )
                        
                        # Gráfico de serie de tiempo si hay fechas
                        if 'fecha' in historial.columns and 'canti salida' in historial.columns:
                            try:
                                historial['fecha'] = pd.to_datetime(historial['fecha'], errors='coerce')
                                historial = historial.dropna(subset=['fecha'])
                                
                                fig_hist = px.line(
                                    historial.sort_values('fecha'),
                                    x='fecha',
                                    y='canti salida',
                                    title=f"📈 Evolución de consumo - {producto_codigo}",
                                    markers=True
                                )
                                fig_hist.update_layout(height=400)
                                st.plotly_chart(fig_hist, use_container_width=True)
                            except:
                                pass
                    else:
                        st.info("No se encontró historial de transacciones para este producto")
        else:
            st.error(f"❌ No se encontró el producto: {codigo_buscar}")
            
            # Sugerir códigos similares
            if 'producto_estado' in resultados.columns:
                codigos_similares = resultados['producto_estado'].astype(str).unique()
                sugerencias = [c for c in codigos_similares if codigo_buscar in str(c)]
                
                if sugerencias:
                    st.info("¿Quizás quisiste decir?")
                    for sugerencia in sugerencias[:5]:  # Mostrar máximo 5 sugerencias
                        st.write(f"- {sugerencia}")
    else:
        # ================== VISTA GENERAL CUANDO NO HAY BÚSQUEDA ==================
        st.subheader("📋 Vista General del Dataset de Predicciones")
        
        # Mostrar primeras filas
        columnas_general = []
        for col in ['producto_estado', 'descripcion', 'inventario_actual', 'estado']:
            if col in resultados.columns:
                columnas_general.append(col)
        
        st.dataframe(
            resultados[columnas_general].head(20),
            use_container_width=True,
            height=400
        )
        
        # Estadísticas rápidas
        st.subheader("📊 Estadísticas Rápidas")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'estado' in resultados.columns:
                optimos = resultados[resultados['estado'] == 'OPTIMO'].shape[0]
                st.metric("✅ Óptimos", optimos)
        
        with col2:
            if 'estado' in resultados.columns:
                sobre_stock = resultados[resultados['estado'] == 'SOBRE STOCK'].shape[0]
                st.metric("📦 Sobre stock", sobre_stock)
        
        with col3:
            if 'estado' in resultados.columns:
                quiebres = resultados[resultados['estado'] == 'QUIEBRE'].shape[0]
                st.metric("🚨 Quiebres", quiebres)
        
        # Distribución gráfica
        if 'estado' in resultados.columns:
            fig_dist = px.pie(
                values=resultados['estado'].value_counts().values,
                names=resultados['estado'].value_counts().index,
                title="Distribución por Estado",
                color=resultados['estado'].value_counts().index,
                color_discrete_map={
                    'QUIEBRE': '#FF6B6B',
                    'SOBRE STOCK': '#FFA500',
                    'OPTIMO': '#00D4AA'
                }
            )
            st.plotly_chart(fig_dist, use_container_width=True)

# Necesitas importar plotly.graph_objects
import plotly.graph_objects as go