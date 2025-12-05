"""
Módulo de integración con Spotify
Permite conectar con Spotify y obtener playlists y canciones guardadas
"""

import streamlit as st
import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import time
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs


def get_spotify_client() -> Optional[spotipy.Spotify]:
    """
    Obtiene un cliente de Spotify autenticado
    
    Returns:
        Cliente de Spotify o None si no está autenticado
    """
    # Verificar si hay credenciales en session state
    if 'spotify_token' not in st.session_state:
        return None
    
    try:
        sp = spotipy.Spotify(auth=st.session_state['spotify_token'])
        return sp
    except:
        return None


def get_auth_url(client_id: str, client_secret: str, redirect_uri: str) -> str:
    """
    Obtiene la URL de autorización de Spotify
    
    Args:
        client_id: Client ID de la app de Spotify
        client_secret: Client Secret de la app de Spotify
        redirect_uri: URI de redirección
    
    Returns:
        URL de autorización
    """
    if not client_id or not client_secret or not redirect_uri:
        raise ValueError("Client ID, Client Secret y Redirect URI son requeridos")
    
    scope = "user-library-read playlist-read-private playlist-read-collaborative"
    
    try:
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_path=None,
            show_dialog=True
        )
        
        # Guardar auth_manager para usar después
        st.session_state['spotify_auth_manager'] = auth_manager
        st.session_state['spotify_client_id'] = client_id
        st.session_state['spotify_client_secret'] = client_secret
        
        auth_url = auth_manager.get_authorize_url()
        
        if not auth_url or not auth_url.startswith("https://"):
            raise ValueError(f"URL de autorización inválida: {auth_url}")
        
        return auth_url
    except Exception as e:
        raise Exception(f"Error al crear auth manager: {str(e)}")


def process_callback_url(callback_url: str) -> bool:
    """
    Procesa la URL de callback después de autorizar
    
    Args:
        callback_url: URL completa de redirección
    
    Returns:
        True si la autenticación fue exitosa
    """
    try:
        if 'spotify_auth_manager' not in st.session_state:
            return False
        
        auth_manager = st.session_state['spotify_auth_manager']
        
        # Extraer código de la URL
        parsed = urlparse(callback_url)
        query_params = parse_qs(parsed.query)
        
        if 'code' not in query_params:
            if 'error' in query_params:
                error = query_params['error'][0]
                st.error(f"❌ Error de autorización: {error}")
            return False
        
        code = query_params['code'][0]
        
        # Intercambiar código por token
        token_info = auth_manager.get_access_token(code, as_dict=True)
        
        if token_info:
            st.session_state['spotify_token'] = token_info['access_token']
            if 'refresh_token' in token_info:
                st.session_state['spotify_refresh_token'] = token_info['refresh_token']
            return True
        
        return False
    except Exception as e:
        st.error(f"Error al procesar autorización: {str(e)}")
        return False


def get_user_playlists(sp: spotipy.Spotify) -> List[Dict]:
    """
    Obtiene todas las playlists del usuario
    
    Args:
        sp: Cliente de Spotify autenticado
    
    Returns:
        Lista de diccionarios con información de playlists
    """
    playlists = []
    try:
        results = sp.current_user_playlists(limit=50)
        
        while results:
            for playlist in results['items']:
                playlists.append({
                    'nombre': playlist['name'],
                    'id': playlist['id'],
                    'canciones': playlist['tracks']['total'],
                    'publica': playlist['public'],
                    'url': playlist['external_urls']['spotify']
                })
            
            if results['next']:
                results = sp.next(results)
            else:
                break
    except Exception as e:
        st.error(f"Error al cargar playlists: {str(e)}")
    
    return playlists


def get_playlist_tracks(sp: spotipy.Spotify, playlist_id: str) -> List[Dict]:
    """
    Obtiene las canciones de una playlist
    
    Args:
        sp: Cliente de Spotify autenticado
        playlist_id: ID de la playlist
    
    Returns:
        Lista de diccionarios con información de canciones
    """
    tracks = []
    try:
        results = sp.playlist_tracks(playlist_id, limit=100)
        
        while results:
            for item in results['items']:
                if item['track'] and item['track'] is not None:
                    track = item['track']
                    tracks.append({
                        'artista': ', '.join([artist['name'] for artist in track['artists']]),
                        'titulo': track['name'],
                        'album': track['album']['name'],
                        'duracion_ms': track['duration_ms'],
                        'url': track['external_urls']['spotify']
                    })
            
            if results['next']:
                results = sp.next(results)
            else:
                break
    except Exception as e:
        st.error(f"Error al cargar canciones: {str(e)}")
    
    return tracks


def get_saved_tracks(sp: spotipy.Spotify) -> List[Dict]:
    """
    Obtiene las canciones guardadas del usuario
    
    Args:
        sp: Cliente de Spotify autenticado
    
    Returns:
        Lista de diccionarios con información de canciones
    """
    tracks = []
    try:
        results = sp.current_user_saved_tracks(limit=50)
        
        while results:
            for item in results['items']:
                track = item['track']
                tracks.append({
                    'artista': ', '.join([artist['name'] for artist in track['artists']]),
                    'titulo': track['name'],
                    'album': track['album']['name'],
                    'duracion_ms': track['duration_ms'],
                    'url': track['external_urls']['spotify']
                })
            
            if results['next']:
                results = sp.next(results)
            else:
                break
    except Exception as e:
        st.error(f"Error al cargar canciones guardadas: {str(e)}")
    
    return tracks


def format_duration(ms: int) -> str:
    """Convierte milisegundos a formato mm:ss"""
    seconds = ms // 1000
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"


def render_spotify_tab():
    """Renderiza la pestaña de Spotify"""
    
    # Verificar si está autenticado
    sp = get_spotify_client()
    
    if not sp:
        st.info("🔐 Conecta tu cuenta de Spotify para comenzar")
        
        # Mostrar siempre visible, no en expander para evitar problemas
        st.markdown("### 🔑 Configuración de Spotify")
        st.markdown("""
        ### Pasos para obtener credenciales:
        
        1. Ve a [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
        2. Crea una nueva app
        3. Copia el **Client ID** y **Client Secret**
        4. Añade tu Redirect URI en la configuración:
           - **Local**: `http://localhost:8501`
           - **Streamlit Cloud**: `https://TU_APP.streamlit.app`
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            client_id = st.text_input("Client ID", type="default", key="spotify_client_id_input")
        with col2:
            client_secret = st.text_input("Client Secret", type="password", key="spotify_client_secret_input")
        
        # Detectar URL automáticamente - simplificado
        # En Streamlit Cloud, usar la URL de la app
        # En local, usar localhost
        try:
            # Verificar si estamos en Streamlit Cloud mirando la URL actual
            import urllib.parse
            # Intentar obtener la URL base
            default_redirect = "http://localhost:8501"
            
            # Si hay una variable de entorno de Streamlit Cloud, usarla
            streamlit_url = os.getenv("STREAMLIT_SERVER_BASE_URL", "")
            if streamlit_url and "streamlit.app" in streamlit_url:
                default_redirect = streamlit_url.rstrip('/')
            elif "streamlit.app" in os.getenv("_", ""):
                # Fallback: usar el nombre de la app si está disponible
                default_redirect = "https://no-techno-tempo.streamlit.app"
        except:
            default_redirect = "http://localhost:8501"
        
        redirect_uri = st.text_input(
            "Redirect URI", 
            value=default_redirect, 
            key="spotify_redirect_uri_input"
        )
        st.caption("⚠️ **IMPORTANTE:** Esta URL debe coincidir EXACTAMENTE con la configurada en Spotify (sin barra final `/`)")
        
        # Verificar si ya tenemos una URL de autorización pendiente
        if 'spotify_auth_url' in st.session_state:
                st.markdown("---")
                st.markdown("### 🔗 Autorización Pendiente")
                st.markdown(f"""
                **Paso 1:** Haz clic en el enlace para autorizar:
                
                **[🔓 Autorizar con Spotify]({st.session_state['spotify_auth_url']})**
                
                **Paso 2:** Después de autorizar, serás redirigido. Copia la **URL completa** de la página.
                
                **Paso 3:** Pega la URL aquí:
                """)
                
                callback_url = st.text_input(
                    "URL de redirección:",
                    key="spotify_callback_input",
                    placeholder="https://accounts.spotify.com/authorize?code=..."
                )
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("✅ Procesar", type="primary"):
                        if callback_url:
                            if process_callback_url(callback_url):
                                st.success("✅ ¡Conectado exitosamente!")
                                if 'spotify_auth_url' in st.session_state:
                                    del st.session_state['spotify_auth_url']
                                st.rerun()
                            else:
                                st.error("❌ Error. Verifica la URL.")
                        else:
                            st.warning("⚠️ Pega la URL de redirección")
                
                with col_btn2:
                    if st.button("❌ Cancelar"):
                        if 'spotify_auth_url' in st.session_state:
                            del st.session_state['spotify_auth_url']
                        st.rerun()
            else:
                # Mostrar información de debug si hay campos vacíos
                if not client_id or not client_secret or not redirect_uri:
                    missing = []
                    if not client_id:
                        missing.append("Client ID")
                    if not client_secret:
                        missing.append("Client Secret")
                    if not redirect_uri:
                        missing.append("Redirect URI")
                    st.warning(f"⚠️ Por favor, completa: {', '.join(missing)}")
                
                # Mensaje de estado antes del botón
                st.info("💡 Completa los campos arriba y haz clic en el botón para conectar")
                
                # Debug: mostrar valores actuales
                with st.expander("🔍 Debug Info (click para ver)"):
                    st.write(f"Client ID: {'✅' if client_id else '❌'}")
                    st.write(f"Client Secret: {'✅' if client_secret else '❌'}")
                    st.write(f"Redirect URI: {redirect_uri[:50] + '...' if redirect_uri and len(redirect_uri) > 50 else redirect_uri}")
                
                # Botón de conexión
                if st.button("🔗 Conectar con Spotify", type="primary", use_container_width=True, key="spotify_connect_btn"):
                    # Este mensaje DEBE aparecer si el botón funciona
                    st.markdown("### 🔥 BOTÓN PRESIONADO - PROCESANDO...")
                    st.write("🔍 Validando campos...")
                    st.write("✅ **BOTÓN PRESIONADO - INICIANDO PROCESO...**")
                    st.write(f"🔍 Client ID: {'✅ Presente' if client_id else '❌ Vacío'}")
                    st.write(f"🔍 Client Secret: {'✅ Presente' if client_secret else '❌ Vacío'}")
                    st.write(f"🔍 Redirect URI: {redirect_uri if redirect_uri else '❌ Vacío'}")
                    
                    # Validar campos
                    if not client_id:
                        st.error("❌ Client ID está vacío")
                    elif not client_secret:
                        st.error("❌ Client Secret está vacío")
                    elif not redirect_uri:
                        st.error("❌ Redirect URI está vacío")
                    else:
                        st.write("✅ Campos validados, generando URL...")
                        # Limpiar barra final si existe para evitar problemas
                        redirect_uri_clean = redirect_uri.strip().rstrip('/')
                        
                        st.info(f"🔍 Intentando conectar... Redirect URI: `{redirect_uri_clean}`")
                        
                        try:
                            auth_url = get_auth_url(client_id, client_secret, redirect_uri_clean)
                            
                            if auth_url and auth_url.startswith("https://"):
                                st.session_state['spotify_auth_url'] = auth_url
                                st.session_state['spotify_redirect_uri'] = redirect_uri_clean
                                st.success("✅ ¡URL de autorización generada!")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(f"❌ URL inválida generada: {auth_url}")
                        except Exception as e:
                            import traceback
                            error_msg = str(e)
                            st.error(f"❌ **Error al generar URL:** {error_msg}")
                            st.code(traceback.format_exc(), language="python")
                            st.info("💡 **Solución:**")
                            st.info("1. Verifica que el Redirect URI en Spotify sea: `https://no-techno-tempo.streamlit.app` (sin barra final)")
                            st.info("2. Verifica que las credenciales sean correctas")
                            st.info("3. Asegúrate de que la app de Spotify esté activa")
    else:
        st.success("✅ Conectado a Spotify")
        
        # Opciones: Playlists o Canciones Guardadas
        option = st.radio(
            "¿Qué quieres ver?",
            ["📋 Mis Playlists", "❤️ Canciones Guardadas"],
            horizontal=True
        )
        
        if option == "📋 Mis Playlists":
            st.subheader("📋 Tus Playlists")
            
            if st.button("🔄 Cargar Playlists", type="primary"):
                with st.spinner("Cargando playlists..."):
                    playlists = get_user_playlists(sp)
                    
                    if playlists:
                        st.success(f"✅ Encontradas {len(playlists)} playlists")
                        
                        # Mostrar lista de playlists
                        df_playlists = pd.DataFrame(playlists)
                        st.dataframe(
                            df_playlists[['nombre', 'canciones', 'publica']],
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                'nombre': 'Nombre',
                                'canciones': 'Canciones',
                                'publica': 'Pública'
                            }
                        )
                        
                        # Selector de playlist para ver canciones
                        playlist_names = [p['nombre'] for p in playlists]
                        selected_playlist = st.selectbox("Selecciona una playlist para ver sus canciones:", playlist_names)
                        
                        if selected_playlist:
                            playlist_id = next(p['id'] for p in playlists if p['nombre'] == selected_playlist)
                            
                            if st.button("🎵 Ver Canciones", type="primary"):
                                with st.spinner("Cargando canciones..."):
                                    tracks = get_playlist_tracks(sp, playlist_id)
                                    
                                    if tracks:
                                        # Formatear duración
                                        for track in tracks:
                                            track['duracion'] = format_duration(track['duracion_ms'])
                                        
                                        df_tracks = pd.DataFrame(tracks)
                                        st.dataframe(
                                            df_tracks[['artista', 'titulo', 'album', 'duracion']],
                                            use_container_width=True,
                                            hide_index=True,
                                            column_config={
                                                'artista': 'Artista',
                                                'titulo': 'Título',
                                                'album': 'Álbum',
                                                'duracion': 'Duración'
                                            }
                                        )
                                        
                                        # Botón de descarga
                                        csv = df_tracks.to_csv(index=False).encode('utf-8-sig')
                                        st.download_button(
                                            label="📥 Descargar CSV",
                                            data=csv,
                                            file_name=f"spotify_playlist_{selected_playlist}_{int(time.time())}.csv",
                                            mime="text/csv"
                                        )
        
        else:  # Canciones Guardadas
            st.subheader("❤️ Tus Canciones Guardadas")
            
            if st.button("🔄 Cargar Canciones Guardadas", type="primary"):
                with st.spinner("Cargando canciones guardadas..."):
                    tracks = get_saved_tracks(sp)
                    
                    if tracks:
                        st.success(f"✅ Encontradas {len(tracks)} canciones guardadas")
                        
                        # Formatear duración
                        for track in tracks:
                            track['duracion'] = format_duration(track['duracion_ms'])
                        
                        df_tracks = pd.DataFrame(tracks)
                        st.dataframe(
                            df_tracks[['artista', 'titulo', 'album', 'duracion']],
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                'artista': 'Artista',
                                'titulo': 'Título',
                                'album': 'Álbum',
                                'duracion': 'Duración'
                            }
                        )
                        
                        # Estadísticas
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Canciones", len(tracks))
                        with col2:
                            st.metric("Artistas Únicos", df_tracks['artista'].nunique())
                        with col3:
                            total_duration = sum(t['duracion_ms'] for t in tracks)
                            hours = total_duration // 3600000
                            minutes = (total_duration % 3600000) // 60000
                            st.metric("Duración Total", f"{hours}h {minutes}m")
                        
                        # Botón de descarga
                        csv = df_tracks.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            label="📥 Descargar CSV",
                            data=csv,
                            file_name=f"spotify_saved_tracks_{int(time.time())}.csv",
                            mime="text/csv"
                        )
        
        # Botón para desconectar
        st.markdown("---")
        if st.button("🚪 Desconectar"):
            keys_to_delete = [
                'spotify_token', 'spotify_refresh_token', 
                'spotify_auth_manager', 'spotify_client_id', 
                'spotify_client_secret', 'spotify_auth_url'
            ]
            for key in keys_to_delete:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("✅ Desconectado")
            st.rerun()

