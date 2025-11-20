import streamlit as st
import hashlib
import json
import os
import pandas as pd

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