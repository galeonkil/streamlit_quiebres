import streamlit as st

def crear_sidebar():
    """Sidebar con botones funcionales pero visual estilo enlaces"""
    
    # Inicializar variable de navegación
    if "pagina_actual" not in st.session_state:
        st.session_state.pagina_actual = "dashboard"
    
    # --- CSS moderno para botones sin borde ---
    st.sidebar.markdown("""
    <style>
    /* Contenedor general del sidebar */
    .sidebar-container {
        display: flex;
        flex-direction: column;
        align-items: stretch;
        padding: 0;
        margin: 0;
    }

    /* Header con logo */
    .sidebar-header {
        text-align: center;
        padding: 1.5rem 0 1rem 0;
        border-bottom: 1px solid rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }

    .logo {
        font-size: 2.5rem;
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border-radius: 12px;
        width: 70px;
        height: 70px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        margin: 0 auto;
    }

    .logo-text h3 {
        margin: 0.5rem 0 0;
        color: #1f2937;
        font-size: 1.2rem;
        font-weight: 700;
    }

    .logo-text p {
        margin: 0;
        font-size: 0.85rem;
        color: #6b7280;
    }

    /* Estilo general para los botones Streamlit */
    div[data-testid="stSidebar"] button[kind="secondary"] {
        all: unset !important;
        display: block;
        width: 100%;
        text-align: left;
        padding: 0.8rem 1rem;
        margin: 0;
        font-size: 1rem;
        color: #374151;
        border-radius: 0;
        cursor: pointer;
        transition: all 0.2s ease;
        border-left: 4px solid transparent;
    }

    /* Hover */
    div[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: #eef2ff !important;
        color: #4338ca !important;
    }

    /* Activo */
    div[data-testid="stSidebar"] button[kind="secondary"].active {
        background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border-left: 4px solid #4f46e5 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- Logo e información ---
    st.sidebar.markdown("""
    <div class="sidebar-header">
        <div class="logo">📦</div>
        <div class="logo-text">
            <h3>InventoryPro</h3>
            <p>Gestión Predictiva</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # --- Menú de botones funcionales ---
    menu = {
        "📊 Dashboard": "dashboard",
        "📈 Reportes": "reportes",
        "🔍 Registros": "registros",
        "⚙️ Configuración": "configuracion"
    }

    st.sidebar.markdown('<div class="sidebar-container">', unsafe_allow_html=True)
    
    for label, key in menu.items():
        if st.sidebar.button(label, use_container_width=True, key=key):
            st.session_state.pagina_actual = key

        # Aplicar clase “active” visualmente (JS + CSS)
        active = "active" if st.session_state.pagina_actual == key else ""
        st.markdown(
            f"""
            <script>
            let btn = window.parent.document.querySelector('button[key="{key}"]');
            if (btn) btn.classList.toggle('active', '{active}' === 'active');
            </script>
            """,
            unsafe_allow_html=True
        )
    
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    return st.session_state.pagina_actual


def aplicar_estilos_globales():
    """Estilos globales limpios y responsivos"""
    st.markdown("""
    <style>
    .main-content {
        padding: 1.5rem;
    }

    @media (max-width: 768px) {
        .main-content { padding: 0.8rem; }
    }

    [data-testid="metric-container"] {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        border-left: 5px solid #6366f1;
    }

    .stButton > button {
        border-radius: 8px !important;
        transition: all 0.2s ease-in-out !important;
        background: #6366f1 !important;
        color: white !important;
        border: none !important;
    }

    .stButton > button:hover {
        background: #4f46e5 !important;
        transform: scale(1.02) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    }
    </style>
    """, unsafe_allow_html=True)
