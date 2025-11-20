import streamlit as st

def mostrar_configuracion():
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
    
    if st.button("🔄 Reiniciar Sistema", use_container_width=True):
        st.session_state.clear()
        st.rerun()