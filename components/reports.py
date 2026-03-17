import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def mostrar_reportes_graficos():
    st.header("📈 Reportes Gráficos Avanzados")
    
    if st.session_state.get('resultados') is None:
        st.warning("⚠️ Primero genera predicciones en el Dashboard para ver los reportes")
        return
    
    resultados = st.session_state.resultados
    
    # ================== VERIFICAR QUÉ DATOS TENEMOS ==================
    st.info(f"📊 Total de productos analizados: {len(resultados):,}")
    
    if 'estado' not in resultados.columns:
        st.error("❌ No se encontró la columna 'estado' en los resultados")
        return
    
    # Contar productos por estado
    conteo_estados = resultados['estado'].value_counts()
    total_productos = len(resultados)
    
    # ================== MATRIZ DE GRÁFICOS 2x3 ==================
    st.subheader("📊 Análisis de Inventario")
    
    # PRIMERA FILA: DIAGRAMAS DE PIE
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 1. Porcentaje de QUIEBRES
        if 'QUIEBRE' in conteo_estados:
            porcentaje_quiebre = (conteo_estados['QUIEBRE'] / total_productos) * 100
            
            fig_quiebre_pie = px.pie(
                values=[porcentaje_quiebre, 100 - porcentaje_quiebre],
                names=['En Quiebre', 'No en Quiebre'],
                title=f"🔄 Quiebres: {porcentaje_quiebre:.1f}%",
                color=['En Quiebre', 'No en Quiebre'],
                color_discrete_map={'En Quiebre': '#FF6B6B', 'No en Quiebre': '#4ECDC4'},
                hole=0.3
            )
            fig_quiebre_pie.update_traces(textinfo='percent+label', textposition='inside')
            fig_quiebre_pie.update_layout(
                height=400,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_quiebre_pie, use_container_width=True)
        else:
            st.info("No hay productos en estado QUIEBRE")
    
    with col2:
        # 2. Porcentaje de SOBRE STOCK
        if 'SOBRE STOCK' in conteo_estados:
            porcentaje_sobre_stock = (conteo_estados['SOBRE STOCK'] / total_productos) * 100
            
            fig_sobre_stock_pie = px.pie(
                values=[porcentaje_sobre_stock, 100 - porcentaje_sobre_stock],
                names=['Sobre Stock', 'No Sobre Stock'],
                title=f"📦 Sobre Stock: {porcentaje_sobre_stock:.1f}%",
                color=['Sobre Stock', 'No Sobre Stock'],
                color_discrete_map={'Sobre Stock': '#FFA500', 'No Sobre Stock': '#00D4AA'},
                hole=0.3
            )
            fig_sobre_stock_pie.update_traces(textinfo='percent+label', textposition='inside')
            fig_sobre_stock_pie.update_layout(
                height=400,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_sobre_stock_pie, use_container_width=True)
        else:
            st.info("No hay productos en estado SOBRE STOCK")
    
    with col3:
        # 3. Distribución completa por Estado
        fig_distribucion_pie = px.pie(
            values=conteo_estados.values,
            names=conteo_estados.index,
            title="🏷️ Distribución por Estado",
            color=conteo_estados.index,
            color_discrete_map={
                'QUIEBRE': '#FF6B6B',
                'SOBRE STOCK': '#FFA500', 
                'OPTIMO': '#00D4AA'
            },
            hole=0.3
        )
        fig_distribucion_pie.update_traces(
            textinfo='percent+label', 
            textposition='inside',
            textfont_size=14
        )
        fig_distribucion_pie.update_layout(
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5,
                font=dict(size=12)
            )
        )
        st.plotly_chart(fig_distribucion_pie, use_container_width=True)
    
    # SEGUNDA FILA: DIAGRAMAS DE BARRA
    st.markdown("### 📊 Segunda Fila: Diagramas de Barras (Cantidades)")
    
    col4, col5, col6 = st.columns(3)
    
    with col4:
        # 4. Barras: Cantidad de QUIEBRES
        if 'QUIEBRE' in conteo_estados:
            fig_quiebre_bar = px.bar(
                x=['En Quiebre', 'No en Quiebre'],
                y=[conteo_estados['QUIEBRE'], total_productos - conteo_estados['QUIEBRE']],
                title=f"⚠️ Cantidad en Quiebre: {conteo_estados['QUIEBRE']:,}",
                labels={'x': 'Estado', 'y': 'Cantidad'},
                color=['En Quiebre', 'No en Quiebre'],
                color_discrete_map={'En Quiebre': '#FF6B6B', 'No en Quiebre': '#4ECDC4'},
                text_auto=True
            )
            fig_quiebre_bar.update_traces(
                texttemplate='%{y:,}',
                textposition='outside'
            )
            fig_quiebre_bar.update_layout(
                height=400,
                xaxis_title="",
                yaxis_title="Cantidad de Productos",
                showlegend=False
            )
            fig_quiebre_bar.update_yaxes(range=[0, total_productos * 1.1])
            st.plotly_chart(fig_quiebre_bar, use_container_width=True)
    
    with col5:
        # 5. Barras: Cantidad de SOBRE STOCK
        if 'SOBRE STOCK' in conteo_estados:
            fig_sobre_stock_bar = px.bar(
                x=['Sobre Stock', 'No Sobre Stock'],
                y=[conteo_estados['SOBRE STOCK'], total_productos - conteo_estados['SOBRE STOCK']],
                title=f"📦 Cantidad Sobre Stock: {conteo_estados['SOBRE STOCK']:,}",
                labels={'x': 'Estado', 'y': 'Cantidad'},
                color=['Sobre Stock', 'No Sobre Stock'],
                color_discrete_map={'Sobre Stock': '#FFA500', 'No Sobre Stock': '#00D4AA'},
                text_auto=True
            )
            fig_sobre_stock_bar.update_traces(
                texttemplate='%{y:,}',
                textposition='outside'
            )
            fig_sobre_stock_bar.update_layout(
                height=400,
                xaxis_title="",
                yaxis_title="Cantidad de Productos",
                showlegend=False
            )
            fig_sobre_stock_bar.update_yaxes(range=[0, total_productos * 1.1])
            st.plotly_chart(fig_sobre_stock_bar, use_container_width=True)
    
    with col6:
        # 6. Barras: Distribución completa
        fig_distribucion_bar = px.bar(
            x=conteo_estados.index,
            y=conteo_estados.values,
            title="📊 Cantidad por Estado",
            labels={'x': 'Estado', 'y': 'Cantidad'},
            color=conteo_estados.index,
            color_discrete_map={
                'QUIEBRE': '#FF6B6B',
                'SOBRE STOCK': '#FFA500', 
                'OPTIMO': '#00D4AA'
            },
            text_auto=True
        )
        fig_distribucion_bar.update_traces(
            texttemplate='%{y:,}',
            textposition='outside'
        )
        fig_distribucion_bar.update_layout(
            height=400,
            xaxis_title="Estado del Inventario",
            yaxis_title="Cantidad de Productos",
            showlegend=False,
            xaxis={'categoryorder':'total descending'}
        )
        st.plotly_chart(fig_distribucion_bar, use_container_width=True)
    
    # ================== TABLAS DETALLADAS ==================
    st.subheader("📋 Listados Detallados por Estado")
    
    # Añadir pestaña de Análisis de Valor si tenemos los datos necesarios
    if 'inventario_actual' in resultados.columns and 'precio_unitario' in resultados.columns:
        # Calcular valor del inventario
        resultados['valor_inventario'] = resultados['inventario_actual'] * resultados['precio_unitario']
        valor_por_estado = resultados.groupby('estado')['valor_inventario'].sum().sort_values(ascending=False)
        
        tab1, tab2, tab3, tab4 = st.tabs(["📦 Sobre Stock", "⚠️ En Quiebre", "✅ Óptimos", "💰 Valor del Inventario"])
    else:
        tab1, tab2, tab3 = st.tabs(["📦 Sobre Stock", "⚠️ En Quiebre", "✅ Óptimos"])
    
    with tab1:
        if 'SOBRE STOCK' in conteo_estados:
            sobre_stock_df = resultados[resultados['estado'] == 'SOBRE STOCK']
            columnas = ['producto_estado', 'descripcion', 'inventario_actual', 'precio_unitario']
            columnas = [c for c in columnas if c in sobre_stock_df.columns]
            
            st.dataframe(
                sobre_stock_df[columnas].head(50),
                use_container_width=True,
                height=400
            )
        else:
            st.info("No hay productos en estado SOBRE STOCK")
    
    with tab2:
        if 'QUIEBRE' in conteo_estados:
            quiebre_df = resultados[resultados['estado'] == 'QUIEBRE']
            columnas = ['producto_estado', 'descripcion', 'inventario_actual', 'precio_unitario', 'consumo_predicho']
            columnas = [c for c in columnas if c in quiebre_df.columns]
            
            st.dataframe(
                quiebre_df[columnas].head(50),
                use_container_width=True,
                height=400
            )
        else:
            st.info("No hay productos en estado QUIEBRE")
    
    with tab3:
        if 'OPTIMO' in conteo_estados:
            optimo_df = resultados[resultados['estado'] == 'OPTIMO']
            columnas = ['producto_estado', 'descripcion', 'inventario_actual', 'precio_unitario']
            columnas = [c for c in columnas if c in optimo_df.columns]
            
            st.dataframe(
                optimo_df[columnas].head(50),
                use_container_width=True,
                height=400
            )
        else:
            st.info("No hay productos en estado OPTIMO")
    
    # Pestaña de Valor del Inventario (solo si tenemos los datos)
    if 'inventario_actual' in resultados.columns and 'precio_unitario' in resultados.columns:
        with tab4:
            st.subheader("💰 Análisis de Valor del Inventario")
            
            # Mostrar métricas resumen
            st.info(f"""
            **📊 Resumen de Valor del Inventario:**
            - **Total valor inventario:** S/{valor_por_estado.sum():,.2f}
            - **Valor promedio por producto:** S/{resultados['valor_inventario'].mean():,.2f}
            - **Producto con mayor valor:** S/{resultados['valor_inventario'].max():,.2f}
            - **Producto con menor valor:** S/{resultados['valor_inventario'].min():,.2f}
            """)
            
            col7, col8 = st.columns(2)
            
            with col7:
                # Gráfico de torta para valor
                fig_valor_pie = px.pie(
                    values=valor_por_estado.values,
                    names=valor_por_estado.index,
                    title="💵 Distribución del Valor del Inventario",
                    color=valor_por_estado.index,
                    color_discrete_map={
                        'QUIEBRE': '#FF6B6B',
                        'SOBRE STOCK': '#FFA500', 
                        'OPTIMO': '#00D4AA'
                    },
                    hole=0.3
                )
                fig_valor_pie.update_traces(
                    textinfo='percent+label',
                    textposition='inside',
                    textfont_size=12,
                    hovertemplate='<b>%{label}</b><br>Valor: S/%{value:,.2f}<br>%{percent}'
                )
                fig_valor_pie.update_layout(height=450)
                st.plotly_chart(fig_valor_pie, use_container_width=True)
            
            with col8:
                # Gráfico de barras para valor
                fig_valor_bar = px.bar(
                    x=valor_por_estado.index,
                    y=valor_por_estado.values,
                    title="📈 Valor Total por Estado (S/)",
                    labels={'x': 'Estado', 'y': 'Valor en Soles'},
                    color=valor_por_estado.index,
                    color_discrete_map={
                        'QUIEBRE': '#FF6B6B',
                        'SOBRE STOCK': '#FFA500', 
                        'OPTIMO': '#00D4AA'
                    },
                    text_auto=True
                )
                fig_valor_bar.update_traces(
                    texttemplate='S/%{y:,.0f}',
                    textposition='outside'
                )
                fig_valor_bar.update_layout(
                    height=450,
                    xaxis_title="Estado del Inventario",
                    yaxis_title="Valor Total (S/)",
                    showlegend=False,
                    xaxis={'categoryorder':'total descending'}
                )
                st.plotly_chart(fig_valor_bar, use_container_width=True)
            
            # Mostrar tabla con los productos de mayor valor
            st.markdown("### 🏆 Productos con Mayor Valor en Inventario")
            
            # Ordenar por valor descendente
            productos_mayor_valor = resultados.sort_values('valor_inventario', ascending=False)
            
            # Seleccionar columnas para mostrar
            columnas_valor = ['producto_estado', 'descripcion', 'inventario_actual', 
                            'precio_unitario', 'valor_inventario', 'estado']
            columnas_valor = [c for c in columnas_valor if c in productos_mayor_valor.columns]
            
            st.dataframe(
                productos_mayor_valor[columnas_valor].head(20),
                use_container_width=True,
                height=400
            )