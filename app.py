import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Predicción de Inventarios",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Importar componentes
from components.layout import crear_sidebar, aplicar_estilos_globales
from components.header import mostrar_barra_usuario

# Importar módulos existentes
from auth.login import mostrar_login
from components.dashboard import mostrar_dashboard, inicializar_sistema
from components.reports import mostrar_reportes_graficos
from components.records import mostrar_registros
from components.config import mostrar_configuracion

def main():
    # Aplicar estilos globales
    aplicar_estilos_globales()
    
    # Verificar si el usuario está logueado
    if not st.session_state.get('logged_in'):
        mostrar_login()
        return
    
    # Inicializar sistema
    inicializar_sistema()
    
    # Mostrar barra de usuario (tu función original mejorada)
    mostrar_barra_usuario()
    
    # Sidebar
    opcion_seleccionada = crear_sidebar()
    
    # Navegación
    if opcion_seleccionada == "dashboard":
        mostrar_dashboard()
    elif opcion_seleccionada == "reportes":
        mostrar_reportes_graficos()
    elif opcion_seleccionada == "registros":
        mostrar_registros()
    elif opcion_seleccionada == "configuracion":
        mostrar_configuracion()

if __name__ == "__main__":
    main()