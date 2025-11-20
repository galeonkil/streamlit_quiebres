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