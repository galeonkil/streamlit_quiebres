import streamlit as st
import datetime

def mostrar_barra_usuario():
    """Barra de usuario mejorada con HTML/CSS responsive"""
    
    if not st.session_state.get('logged_in'):
        return
    
    # CSS para la barra de usuario
    header_css = """
    <style>
    .user-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .header-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 1rem;
    }
    
    .welcome-section {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .user-avatar {
        font-size: 2rem;
        background: rgba(255,255,255,0.2);
        border-radius: 50%;
        width: 50px;
        height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .welcome-text h3 {
        margin: 0;
        font-size: 1.2rem;
        font-weight: 600;
    }
    
    .welcome-text p {
        margin: 0;
        opacity: 0.9;
        font-size: 0.9rem;
    }
    
    .header-stats {
        display: flex;
        gap: 1.5rem;
        align-items: center;
    }
    
    .stat-item {
        text-align: center;
        padding: 0.5rem 1rem;
        background: rgba(255,255,255,0.1);
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .stat-value {
        font-weight: 700;
        font-size: 1.1rem;
        margin: 0;
    }
    
    .stat-label {
        font-size: 0.8rem;
        opacity: 0.8;
        margin: 0;
    }
    
    .logout-section {
        display: flex;
        align-items: center;
    }
    
    /* Botón de logout personalizado */
    .logout-btn {
        background: rgba(255,255,255,0.2) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    
    .logout-btn:hover {
        background: rgba(255,255,255,0.3) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .user-header {
            padding: 1rem;
        }
        
        .header-content {
            flex-direction: column;
            align-items: stretch;
            text-align: center;
        }
        
        .welcome-section {
            justify-content: center;
        }
        
        .header-stats {
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .stat-item {
            flex: 1;
            min-width: 100px;
        }
        
        .logout-section {
            justify-content: center;
        }
    }
    
    @media (max-width: 480px) {
        .header-stats {
            flex-direction: column;
            width: 100%;
        }
        
        .stat-item {
            width: 100%;
        }
    }
    </style>
    """
    
    st.markdown(header_css, unsafe_allow_html=True)
    
    # Obtener datos reales de la sesión
    username = st.session_state.username
    fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y")
    hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
    
    # Obtener estadísticas reales si existen
    total_registros = "0"
    total_skus = "0"
    
    if st.session_state.get('datos_cargados') is not None:
        datos = st.session_state.datos_cargados
        total_registros = f"{len(datos):,}"
        total_skus = f"{datos['id_insumo'].nunique():,}"
    
    # HTML del header
    header_html = f"""
    <div class="user-header">
        <div class="header-content">
            <div class="welcome-section">
                <div class="user-avatar">👋</div>
                <div class="welcome-text">
                    <h3>¡Hola, {username}!</h3>
                    <p>Bienvenido al Sistema de Inventarios</p>
                </div>
            </div>
        </div>
    </div>
    """
    
    st.markdown(header_html, unsafe_allow_html=True)
    
    # Botón de logout (Streamlit nativo para funcionalidad)
    col1, col2, col3 = st.columns([3, 1, 1])
    with col3:
        if st.button("🚪 **Cerrar Sesión**", use_container_width=True, key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()
    
    st.markdown("---")