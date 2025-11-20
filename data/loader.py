import streamlit as st
import pandas as pd
import os

@st.cache_data
def cargar_datos_automaticamente():
    """Cargar datos automáticamente desde la carpeta dataset"""
    try:
        dataset_path = "dataset"
        archivos = os.listdir(dataset_path)
        
        archivos_excel = [f for f in archivos if f.endswith(('.xlsx', '.xls'))]
        archivos_csv = [f for f in archivos if f.endswith('.csv')]
        
        if archivos_excel:
            archivo = archivos_excel[0]
            df = pd.read_excel(f"{dataset_path}/{archivo}")
            st.success(f"✅ Datos cargados automáticamente desde: {archivo}")
            return df
        elif archivos_csv:
            archivo = archivos_csv[0]
            df = pd.read_csv(f"{dataset_path}/{archivo}")
            st.success(f"✅ Datos cargados automáticamente desde: {archivo}")
            return df
        else:
            st.error("❌ No se encontraron archivos en la carpeta 'dataset'")
            return None
            
    except Exception as e:
        st.error(f"❌ Error al cargar datos automáticamente: {str(e)}")
        return None

def inicializar_sistema():
    """Inicializar el sistema con datos y modelo"""
    
    if 'datos_cargados' not in st.session_state:
        with st.spinner("🔄 Cargando datos automáticamente..."):
            datos = cargar_datos_automaticamente()
            if datos is not None:
                st.session_state.datos_cargados = datos
                st.session_state.datos_automaticos = True
    
    if 'predictor' not in st.session_state:
        from utils.predictor import PredictorComprasMejorado
        st.session_state.predictor = PredictorComprasMejorado(use_log_transform=True)