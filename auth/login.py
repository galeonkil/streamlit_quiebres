import streamlit as st
from auth.authenticaction import SistemaAutenticacion

def mostrar_login():
    # CSS personalizado para hacer el login responsive
    st.markdown("""
    <style>
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 20px;
    }
    @media (max-width: 768px) {
        .login-container {
            max-width: 60%;
            padding: 10px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Contenedor principal centrado
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            
            st.title("🔐 Sistema de Autenticación")
            st.markdown("---")
            
            # Inicializar sistema de autenticación
            if 'auth_system' not in st.session_state:
                st.session_state.auth_system = SistemaAutenticacion()
            
            tab1, tab2 = st.tabs(["🚪 **Iniciar Sesión**", "📝 **Registrarse**"])
            
            with tab1:
                with st.form("login_form", clear_on_submit=False):
                    st.subheader("Iniciar Sesión")
                    
                    username = st.text_input(
                        "**Usuario**", 
                        placeholder="Ingresa tu usuario",
                        key="login_user"
                    )
                    
                    password = st.text_input(
                        "**Contraseña**", 
                        type="password", 
                        placeholder="Ingresa tu contraseña",
                        key="login_pass"
                    )
                    
                    login_btn = st.form_submit_button(
                        "🎯 Ingresar al Sistema", 
                        type="primary",
                        use_container_width=True
                    )
                    
                    if login_btn:
                        if username and password:
                            with st.spinner("Verificando credenciales..."):
                                success, message = st.session_state.auth_system.verificar_login(username, password)
                                if success:
                                    st.session_state.logged_in = True
                                    st.session_state.username = username
                                    st.success(f"¡Bienvenido {username}!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
                        else:
                            st.error("⚠️ Por favor completa todos los campos")
            
            with tab2:
                with st.form("register_form", clear_on_submit=False):
                    st.subheader("Crear Nueva Cuenta")
                    
                    new_user = st.text_input(
                        "**Usuario**", 
                        placeholder="Elige un nombre de usuario",
                        key="reg_user"
                    )
                    
                    new_email = st.text_input(
                        "**Email**", 
                        placeholder="tu.email@ejemplo.com",
                        key="reg_email"
                    )
                    
                    col_pass1, col_pass2 = st.columns(2)
                    
                    with col_pass1:
                        new_pass = st.text_input(
                            "**Contraseña**", 
                            type="password", 
                            placeholder="Mínimo 6 caracteres",
                            key="reg_pass"
                        )
                    
                    with col_pass2:
                        confirm_pass = st.text_input(
                            "**Confirmar**", 
                            type="password", 
                            placeholder="Repite la contraseña",
                            key="reg_pass_confirm"
                        )
                    
                    register_btn = st.form_submit_button(
                        "✅ Crear Cuenta", 
                        type="primary",
                        use_container_width=True
                    )
                    
                    if register_btn:
                        if not all([new_user, new_email, new_pass, confirm_pass]):
                            st.error("⚠️ Todos los campos son obligatorios")
                        elif len(new_pass) < 6:
                            st.error("🔒 La contraseña debe tener al menos 6 caracteres")
                        elif new_pass != confirm_pass:
                            st.error("❌ Las contraseñas no coinciden")
                        else:
                            with st.spinner("Creando tu cuenta..."):
                                success, message = st.session_state.auth_system.registrar_usuario(new_user, new_pass, new_email)
                                if success:
                                    st.success("✅ " + message)
                                    # Auto-login después del registro
                                    st.session_state.logged_in = True
                                    st.session_state.username = new_user
                                    st.rerun()
                                else:
                                    st.error(f"❌ {message}")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Información adicional
            st.markdown("---")
            col_info1, col_info2, col_info3 = st.columns(3)
            with col_info1:
                st.markdown("**🔒 Seguro**")
                st.caption("Datos protegidos")
            with col_info2:
                st.markdown("**⚡ Rápido**")
                st.caption("Acceso inmediato")
            with col_info3:
                st.markdown("**📱 Responsive**")
                st.caption("Funciona en cualquier dispositivo")