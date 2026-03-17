import streamlit as st
import pandas as pd
import os

@st.cache_data
def cargar_datos_automaticamente():
    """Cargar datos automáticamente - PRIMERO busca procesados"""
    try:
        # ============================================
        # 1. PRIMERO: Buscar datos YA procesados
        # ============================================
        if os.path.exists("dataset_mensual_generado.xlsx"):
            df = pd.read_excel("dataset_mensual_generado.xlsx")
            st.success("✅ Datos cargados desde archivo procesado")
            return df
        
        # ============================================
        # 2. SEGUNDO: Si no existen procesados, buscar en carpeta dataset
        # ============================================
        dataset_path = "dataset"
        
        if not os.path.exists(dataset_path):
            st.error("❌ No se encontró la carpeta 'dataset'")
            return None
        
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
    
    # Cargar datos (automáticamente busca procesados primero)
    if 'datos_cargados' not in st.session_state:
        with st.spinner("🔄 Cargando datos..."):
            datos = cargar_datos_automaticamente()
            if datos is not None:
                st.session_state.datos_cargados = datos
                st.session_state.datos_automaticos = True
    
    # Inicializar predictor
    if 'predictor' not in st.session_state:
        from utils.predictor import PredictorComprasMejorado
        st.session_state.predictor = PredictorComprasMejorado(use_log_transform=True)