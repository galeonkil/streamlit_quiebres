# components/planificacion.py
import streamlit as st
import pandas as pd

def mostrar_planificacion():
    """Módulo de planificación de inventarios - Versión Calculadora Simple"""
    
    st.header("📅 Calculadora de Duración de Inventario")
    st.markdown("---")
    
    # Verificar si hay predicciones generadas
    if st.session_state.get('resultados') is None:
        st.error("❌ No hay predicciones generadas")
        st.info("Primero genera predicciones en el Dashboard")
        return
    
    resultados = st.session_state.resultados
    
    # ================== CALCULADORA SIMPLE ==================
    st.subheader("🧮 Calculadora")
    
    # Columna para seleccionar producto
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Selector de producto
        productos_disponibles = resultados['producto_estado'].unique()
        producto_seleccionado = st.selectbox(
            "Selecciona un producto:",
            options=productos_disponibles,
            key="producto_calc"
        )
        
        # Obtener información del producto
        producto_info = resultados[resultados['producto_estado'] == producto_seleccionado].iloc[0]
        consumo_mensual = producto_info.get('consumo_predicho', 0)
        descripcion = producto_info.get('descripcion', 'Sin descripción')
        
        st.caption(f"📝 {descripcion}")
    
    with col2:
        st.metric("Consumo mensual", f"{consumo_mensual:.0f} unidades")
    
    st.markdown("---")
    
    # ================== CALCULADORA PRINCIPAL ==================
    st.subheader("🔢 ¿Cuánto tiempo durará?")
    
    # Input de cantidad
    cantidad = st.number_input(
        "Ingresa la cantidad de unidades:",
        min_value=1,
        value=1,
        step=1,
        help="Escribe la cantidad de productos que tienes o piensas comprar"
    )
    
    # Calcular duración
    if consumo_mensual > 0:
        duracion_meses = cantidad / consumo_mensual
        
        # Mostrar resultado de forma clara y simple
        st.markdown("---")
        
        # Resultado principal en grande
        st.markdown(f"""
        <div style='background-color: #f0f2f6; padding: 30px; border-radius: 10px; text-align: center;'>
            <h2 style='color: #1E2B3C; margin: 0;'>📦 {cantidad} unidades</h2>
            <h1 style='color: #00D4AA; font-size: 48px; margin: 10px 0;'>{duracion_meses:.1f} meses</h1>
            <p style='font-size: 18px; color: #666;'>de duración estimada</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar en diferentes formatos
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "En meses",
                f"{duracion_meses:.1f} meses"
            )
        
        with col2:
            dias = duracion_meses * 30
            st.metric(
                "En días",
                f"{dias:.0f} días"
            )
        
        with col3:
            semanas = duracion_meses * 4
            st.metric(
                "En semanas",
                f"{semanas:.1f} semanas"
            )
        
        # Ejemplo práctico
        st.info(f"""
        💡 **Ejemplo:** Con {cantidad} unidades y un consumo de {consumo_mensual:.0f} unidad(es) por mes, 
        tendrás inventario para aproximadamente **{duracion_meses:.1f} meses**.
        """)
        
    else:
        st.warning("⚠️ No hay datos de consumo para este producto")
        
    # Mostrar productos similares como referencia
    with st.expander("📋 Ver consumos de otros productos"):
        # Mostrar una tabla pequeña con ejemplos
        ejemplos = resultados[['producto_estado', 'consumo_predicho']].dropna().head(10)
        ejemplos['consumo_predicho'] = ejemplos['consumo_predicho'].round(0).astype(int)
        ejemplos.columns = ['Producto', 'Consumo mensual']
        st.dataframe(ejemplos, use_container_width=True, height=300)