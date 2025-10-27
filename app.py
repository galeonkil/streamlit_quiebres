import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.predictor import PredictorComprasMejorado
import joblib
import os
import hashlib
import json

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Predicción de Inventarios",
    page_icon="📊",
    layout="wide"
)

# ================== SISTEMA DE AUTENTICACIÓN ==================
class SistemaAutenticacion:
    def __init__(self):
        self.archivo_usuarios = "usuarios.json"
        self.cargar_usuarios()
    
    def cargar_usuarios(self):
        """Cargar usuarios desde archivo JSON"""
        try:
            if os.path.exists(self.archivo_usuarios):
                with open(self.archivo_usuarios, 'r') as f:
                    st.session_state.usuarios = json.load(f)
            else:
                st.session_state.usuarios = {}
        except:
            st.session_state.usuarios = {}
    
    def guardar_usuarios(self):
        """Guardar usuarios en archivo JSON"""
        try:
            with open(self.archivo_usuarios, 'w') as f:
                json.dump(st.session_state.usuarios, f)
        except Exception as e:
            st.error(f"Error guardando usuarios: {e}")
    
    def hash_password(self, password):
        """Hashear contraseña para seguridad básica"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def registrar_usuario(self, username, password, email):
        """Registrar nuevo usuario"""
        if username in st.session_state.usuarios:
            return False, "El usuario ya existe"
        
        st.session_state.usuarios[username] = {
            'password': self.hash_password(password),
            'email': email,
            'fecha_registro': pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.guardar_usuarios()
        return True, "Usuario registrado exitosamente"
    
    def verificar_login(self, username, password):
        """Verificar credenciales de usuario"""
        if username not in st.session_state.usuarios:
            return False, "Usuario no encontrado"
        
        if st.session_state.usuarios[username]['password'] == self.hash_password(password):
            return True, "Login exitoso"
        else:
            return False, "Contraseña incorrecta"

# ================== PANTALLA DE LOGIN RESPONSIVE ==================
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
            
            # Tarjeta de login
            st.markdown('<div class="login-card">', unsafe_allow_html=True)
            
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
            
            st.markdown('</div>', unsafe_allow_html=True)  # Cierre de login-card
            st.markdown('</div>', unsafe_allow_html=True)  # Cierre de login-container
            
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

# ================== BARRA SUPERIOR CON INFO DE USUARIO ==================
def mostrar_barra_usuario():
    if st.session_state.get('logged_in'):
        # Usar columns para alinear a la derecha
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col3:
            st.write(f"👋 **{st.session_state.username}**")
        with col4:
            if st.button("🚪 **Cerrar Sesión**", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = None
                st.rerun()
        st.markdown("---")

# ================== CARGA AUTOMÁTICA DE DATOS ==================
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

# ================== INICIALIZACIÓN AUTOMÁTICA ==================
def inicializar_sistema():
    """Inicializar el sistema con datos y modelo"""
    
    if 'datos_cargados' not in st.session_state:
        with st.spinner("🔄 Cargando datos automáticamente..."):
            datos = cargar_datos_automaticamente()
            if datos is not None:
                st.session_state.datos_cargados = datos
                st.session_state.datos_automaticos = True
    
    if 'predictor' not in st.session_state:
        st.session_state.predictor = PredictorComprasMejorado(use_log_transform=True)
    
    if st.session_state.predictor.model is None:
        modelo_cargado = st.session_state.predictor.cargar_modelo('modelo_compras/')
        if modelo_cargado:
            st.success("✅ Modelo pre-entrenado cargado")
        else:
            st.info("🤖 No hay modelo pre-entrenado. Se entrenará uno nuevo.")

# ================== FUNCIONES PRINCIPALES (MANTENER TUS FUNCIONES ORIGINALES) ==================
def mostrar_dashboard():
    st.header("📊 Dashboard de Inventarios")
    
    if st.session_state.get('datos_cargados') is None:
        st.error("No se pudieron cargar los datos automáticamente.")
        st.info("""
        **Solución:**
        1. Asegúrate de que existe la carpeta 'dataset' 
        2. Coloca tu archivo Excel o CSV en la carpeta 'dataset'
        3. Reinicia la aplicación
        """)
        return
    
    datos = st.session_state.datos_cargados
    st.success(f"📁 Datos listos: {len(datos):,} registros, {datos['id_insumo'].nunique():,} SKUs")
    
    if st.button("🚀 Generar Predicciones Automáticamente", type="primary", use_container_width=True):
        generar_predicciones()
    
    if st.session_state.get('resultados') is not None:
        mostrar_resultados_detallados()

def mostrar_reportes_graficos():
    st.header("📈 Reportes Gráficos Avanzados")
    
    if st.session_state.get('resultados') is None:
        st.warning("⚠️ Primero genera predicciones en el Dashboard para ver los reportes")
        return
    
    # ... (mantener tu código original de reportes)

def mostrar_registros():
    st.header("🔍 Buscar Registros")
    
    if st.session_state.get('datos_cargados') is None:
        st.error("No hay datos cargados en el sistema")
        return
    
    # ... (mantener tu código original de registros)

def generar_predicciones():
    """Generar predicciones automáticamente"""
    with st.spinner("Procesando datos y generando predicciones..."):
        try:
            predictor = st.session_state.predictor
            datos = st.session_state.datos_cargados
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            progress_bar.progress(25)
            status_text.text("🔄 Transformando datos a formato mensual...")
            df_mensual = predictor.crear_dataset_mensual(datos)
            
            if len(df_mensual) == 0:
                st.error("❌ No se pudieron crear datos mensuales")
                return
            
            progress_bar.progress(50)
            status_text.text("🎯 Creando características para el modelo...")
            df_preparado = predictor.preparar_features(df_mensual)
            
            if len(df_preparado) == 0:
                st.error("❌ No hay datos suficientes después de la preparación")
                return
            
            progress_bar.progress(75)
            if predictor.model is None:
                status_text.text("🤖 Entrenando modelo...")
                predictor.entrenar_modelo(df_preparado)
                predictor.guardar_modelo('modelo_compras/')
            
            progress_bar.progress(90)
            status_text.text("📊 Generando recomendaciones de compra...")
            resultados = predictor.calcular_cantidad_comprar(df_preparado)
            st.session_state.resultados = resultados
            
            progress_bar.progress(100)
            status_text.text("✅ ¡Listo!")
            st.success("Predicciones generadas exitosamente!")
            
        except Exception as e:
            st.error(f"❌ Error en la predicción: {str(e)}")

def mostrar_resultados_detallados():
    """Mostrar resultados de las predicciones"""
    # ... (mantener tu código original de resultados)

# ================== APLICACIÓN PRINCIPAL ==================
def main():
    # Verificar si el usuario está logueado
    if not st.session_state.get('logged_in'):
        mostrar_login()
        return
    
    # Usuario logueado - mostrar aplicación normal
    mostrar_barra_usuario()
    
    # Inicializar sistema (solo si está logueado)
    inicializar_sistema()
    
    # Menú principal responsive
    st.sidebar.title("📋 Navegación")
    opcion = st.sidebar.radio(
        "Selecciona una opción:",
        ["📊 Dashboard", "📈 Reportes Gráficos", "📝 Registros", "⚙️ Configuración"]
    )
    
    if opcion == "📊 Dashboard":
        mostrar_dashboard()
    elif opcion == "📈 Reportes Gráficos":
        mostrar_reportes_graficos()
    elif opcion == "📝 Registros":
        mostrar_registros()
    elif opcion == "⚙️ Configuración":
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

# Ejecutar la aplicación
if __name__ == "__main__":
    main()