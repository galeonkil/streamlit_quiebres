import streamlit as st
import pandas as pd

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
                # Limpiar y convertir a string
                datos['fecha'] = datos['fecha'].astype(str).str.strip()
                
                # Reemplazar el patrón problemático de milisegundos
                datos['fecha'] = datos['fecha'].str.replace(
                    r'(\d{2}:\d{2}:\d{2}):(\d{1,3})$', 
                    r'\1.\2', 
                    regex=True
                )
                
                # Parsear fechas con formato específico para milisegundos
                fechas = pd.to_datetime(datos['fecha'], format='%d/%m/%Y %H:%M:%S.%f', errors='coerce')
                
                # Filtrar solo fechas reales (a partir de 2024)
                fechas_reales = fechas[fechas >= pd.Timestamp('2024-01-01')]
                
                if len(fechas_reales) > 0:
                    fecha_min = fechas_reales.min().strftime('%d/%m/%Y')
                    fecha_max = fechas_reales.max().strftime('%d/%m/%Y')
                    st.metric("📅 Rango de Fechas", f"{fecha_min} a {fecha_max}")
                else:
                    st.metric("📅 Rango de Fechas", "No disponible")
                    
            except Exception as e:
                st.metric("📅 Rango de Fechas", "Error")
        else:
            st.metric("📅 Rango de Fechas", "N/A")