"""
Módulo de autenticación con Google OAuth
"""

import streamlit as st
from google.oauth2 import id_token
from google.auth.transport import requests
import os
from data_storage import get_user_id

# Obtener client_id desde secrets o variable de entorno
def get_google_client_id():
    """Obtiene el Client ID de Google desde secrets o variable de entorno"""
    try:
        # Intentar desde Streamlit secrets (para producción)
        return st.secrets["google_oauth"]["client_id"]
    except:
        # Intentar desde variable de entorno (para desarrollo)
        return os.getenv("GOOGLE_CLIENT_ID", "")


def check_auth():
    """
    Verifica si el usuario está autenticado
    Retorna el user_id si está autenticado, None si no
    """
    client_id = get_google_client_id()
    
    # Si no hay client_id configurado, usar modo desarrollo (sin auth)
    if not client_id:
        st.warning("⚠️ Google OAuth no configurado. Modo desarrollo activado.")
        # Para desarrollo: usar un user_id por defecto
        if 'user_id' not in st.session_state:
            st.session_state.user_id = get_user_id("dev@local.com")
            st.session_state.user_email = "dev@local.com"
        return st.session_state.user_id
    
    # Verificar si ya está autenticado
    if 'user_id' in st.session_state and st.session_state.user_id:
        return st.session_state.user_id
    
    # Mostrar botón de login
    st.markdown("## 🔐 Iniciar Sesión")
    st.markdown("Inicia sesión con tu cuenta de Google para acceder a NoTechnoTempo")
    
    # Botón de login (en producción, esto se implementaría con OAuth flow completo)
    # Por ahora, usamos un enfoque simplificado
    if st.button("🔵 Iniciar sesión con Google", type="primary", use_container_width=True):
        # En producción, aquí iría el flujo OAuth completo
        # Por ahora, pedimos el email manualmente para desarrollo
        email = st.text_input("Email (modo desarrollo)", placeholder="tu@email.com")
        if email:
            user_id = get_user_id(email)
            st.session_state.user_id = user_id
            st.session_state.user_email = email
            st.rerun()
    
    st.info("💡 **Nota**: En producción, esto se conectará automáticamente con Google OAuth.")
    
    return None


def get_current_user_id():
    """Obtiene el user_id del usuario actual"""
    return st.session_state.get('user_id')


def get_current_user_email():
    """Obtiene el email del usuario actual"""
    return st.session_state.get('user_email')

