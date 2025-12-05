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


def get_playlist_tracks(sp: spotipy.Spotify, playlist_id: str, include_features: bool = True) -> List[Dict]:
    """
    Obtiene las canciones de una playlist con estadísticas de audio
    
    Args:
        sp: Cliente de Spotify autenticado
        playlist_id: ID de la playlist
        include_features: Si incluir estadísticas de audio
    
    Returns:
        Lista de diccionarios con información de canciones
    """
    tracks = []
    track_ids = []
    try:
        results = sp.playlist_tracks(playlist_id, limit=100)
        
        while results:
            for item in results['items']:
                if item['track'] and item['track'] is not None:
                    track = item['track']
                    track_data = {
                        'artista': ', '.join([artist['name'] for artist in track['artists']]),
                        'titulo': track['name'],
                        'album': track['album']['name'],
                        'duracion_ms': track['duration_ms'],
                        'url': track['external_urls']['spotify'],
                        'id': track['id']
                    }
                    tracks.append(track_data)
                    if track['id']:
                        track_ids.append(track['id'])
            
            if results['next']:
                results = sp.next(results)
            else:
                break
        
        # Obtener audio features si se solicita
        if include_features and track_ids:
            # Filtrar None IDs
            valid_track_ids = [tid for tid in track_ids if tid]
            
            if valid_track_ids:
                # Spotify API limita a 100 tracks por request
                features_batch = []
                for i in range(0, len(valid_track_ids), 100):
                    batch = valid_track_ids[i:i+100]
                    try:
                        features = sp.audio_features(batch)
                        if features:
                            features_batch.extend([f for f in features if f])  # Filtrar None
                    except Exception as e:
                        st.warning(f"Error al obtener features para batch {i//100 + 1}: {str(e)}")
                
                # Mapear features a tracks
                features_dict = {f['id']: f for f in features_batch if f and f.get('id')}
                
                # Añadir estadísticas a todas las canciones (con valores por defecto si no hay)
                for track in tracks:
                    if track.get('id') and track['id'] in features_dict:
                        feat = features_dict[track['id']]
                        track.update({
                            'energia': round(feat.get('energy', 0) * 100, 1) if feat.get('energy') is not None else None,
                            'danceability': round(feat.get('danceability', 0) * 100, 1) if feat.get('danceability') is not None else None,
                            'valence': round(feat.get('valence', 0) * 100, 1) if feat.get('valence') is not None else None,
                            'acousticness': round(feat.get('acousticness', 0) * 100, 1) if feat.get('acousticness') is not None else None,
                            'instrumentalness': round(feat.get('instrumentalness', 0) * 100, 1) if feat.get('instrumentalness') is not None else None,
                            'liveness': round(feat.get('liveness', 0) * 100, 1) if feat.get('liveness') is not None else None,
                            'speechiness': round(feat.get('speechiness', 0) * 100, 1) if feat.get('speechiness') is not None else None,
                            'tempo': round(feat.get('tempo', 0), 1) if feat.get('tempo') is not None else None,
                            'key': feat.get('key'),
                            'mode': 'Mayor' if feat.get('mode') == 1 else 'Menor' if feat.get('mode') == 0 else None,
                            'time_signature': feat.get('time_signature')
                        })
                    else:
                        # Añadir None para tracks sin features
                        track.update({
                            'energia': None, 'danceability': None, 'valence': None,
                            'acousticness': None, 'instrumentalness': None, 'liveness': None,
                            'speechiness': None, 'tempo': None, 'key': None,
                            'mode': None, 'time_signature': None
                        })
    except Exception as e:
        st.error(f"Error al cargar canciones: {str(e)}")
    
    return tracks


def get_saved_tracks(sp: spotipy.Spotify, include_features: bool = True) -> List[Dict]:
    """
    Obtiene las canciones guardadas del usuario con estadísticas de audio
    
    Args:
        sp: Cliente de Spotify autenticado
        include_features: Si incluir estadísticas de audio
    
    Returns:
        Lista de diccionarios con información de canciones
    """
    tracks = []
    track_ids = []
    try:
        results = sp.current_user_saved_tracks(limit=50)
        
        while results:
            for item in results['items']:
                track = item['track']
                track_data = {
                    'artista': ', '.join([artist['name'] for artist in track['artists']]),
                    'titulo': track['name'],
                    'album': track['album']['name'],
                    'duracion_ms': track['duration_ms'],
                    'url': track['external_urls']['spotify'],
                    'id': track['id']
                }
                tracks.append(track_data)
                if track['id']:
                    track_ids.append(track['id'])
            
            if results['next']:
                results = sp.next(results)
            else:
                break
        
        # Obtener audio features si se solicita
        if include_features and track_ids:
            # Filtrar None IDs
            valid_track_ids = [tid for tid in track_ids if tid]
            
            if valid_track_ids:
                # Spotify API limita a 100 tracks por request
                features_batch = []
                for i in range(0, len(valid_track_ids), 100):
                    batch = valid_track_ids[i:i+100]
                    try:
                        features = sp.audio_features(batch)
                        if features:
                            features_batch.extend([f for f in features if f])  # Filtrar None
                    except Exception as e:
                        st.warning(f"Error al obtener features para batch {i//100 + 1}: {str(e)}")
                
                # Mapear features a tracks
                features_dict = {f['id']: f for f in features_batch if f and f.get('id')}
                
                # Añadir estadísticas a todas las canciones (con valores por defecto si no hay)
                for track in tracks:
                    if track.get('id') and track['id'] in features_dict:
                        feat = features_dict[track['id']]
                        track.update({
                            'energia': round(feat.get('energy', 0) * 100, 1) if feat.get('energy') is not None else None,
                            'danceability': round(feat.get('danceability', 0) * 100, 1) if feat.get('danceability') is not None else None,
                            'valence': round(feat.get('valence', 0) * 100, 1) if feat.get('valence') is not None else None,
                            'acousticness': round(feat.get('acousticness', 0) * 100, 1) if feat.get('acousticness') is not None else None,
                            'instrumentalness': round(feat.get('instrumentalness', 0) * 100, 1) if feat.get('instrumentalness') is not None else None,
                            'liveness': round(feat.get('liveness', 0) * 100, 1) if feat.get('liveness') is not None else None,
                            'speechiness': round(feat.get('speechiness', 0) * 100, 1) if feat.get('speechiness') is not None else None,
                            'tempo': round(feat.get('tempo', 0), 1) if feat.get('tempo') is not None else None,
                            'key': feat.get('key'),
                            'mode': 'Mayor' if feat.get('mode') == 1 else 'Menor' if feat.get('mode') == 0 else None,
                            'time_signature': feat.get('time_signature')
                        })
                    else:
                        # Añadir None para tracks sin features
                        track.update({
                            'energia': None, 'danceability': None, 'valence': None,
                            'acousticness': None, 'instrumentalness': None, 'liveness': None,
                            'speechiness': None, 'tempo': None, 'key': None,
                            'mode': None, 'time_signature': None
                        })
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
    
    # Verificar si hay código en query params (callback de OAuth)
    query_params = st.query_params
    if 'code' in query_params and 'spotify_auth_manager' in st.session_state:
        code = query_params['code']
        try:
            auth_manager = st.session_state['spotify_auth_manager']
            token_info = auth_manager.get_access_token(code, as_dict=True)
            if token_info:
                st.session_state['spotify_token'] = token_info['access_token']
                if 'refresh_token' in token_info:
                    st.session_state['spotify_refresh_token'] = token_info['refresh_token']
                # Limpiar query params y auth_url
                st.query_params.clear()
                if 'spotify_auth_url' in st.session_state:
                    del st.session_state['spotify_auth_url']
                st.success("✅ ¡Conectado exitosamente!")
                st.rerun()
        except Exception as e:
            st.error(f"Error al procesar autorización: {str(e)}")
    
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
            **Haz clic en el enlace para autorizar:**
            
            **[🔓 Autorizar con Spotify]({st.session_state['spotify_auth_url']})**
            
            ⚠️ **Importante:** Después de autorizar, serás redirigido automáticamente. Si no funciona, copia la URL completa de la página y pégala abajo.
            """)
            
            # Opción manual como fallback
            with st.expander("🔧 Si la redirección automática no funciona"):
                callback_url = st.text_input(
                    "Pega la URL de redirección aquí:",
                    key="spotify_callback_input",
                    placeholder="https://accounts.spotify.com/authorize?code=..."
                )
                
                if st.button("✅ Procesar URL manual", type="primary"):
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
            
            # Cargar playlists si no están en session_state
            if 'spotify_playlists' not in st.session_state:
                if st.button("🔄 Cargar Playlists", type="primary"):
                    with st.spinner("Cargando playlists..."):
                        playlists = get_user_playlists(sp)
                        if playlists:
                            st.session_state['spotify_playlists'] = playlists
                            st.success(f"✅ Encontradas {len(playlists)} playlists")
                            st.rerun()
            else:
                playlists = st.session_state['spotify_playlists']
                
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
                selected_playlist = st.selectbox("Selecciona una playlist para ver sus canciones:", playlist_names, key="spotify_playlist_selector")
                
                if selected_playlist:
                    playlist_id = next(p['id'] for p in playlists if p['nombre'] == selected_playlist)
                    
                    # Cargar canciones si no están cargadas o si cambió la playlist
                    playlist_key = f"spotify_playlist_tracks_{playlist_id}"
                    if playlist_key not in st.session_state or st.session_state.get('spotify_selected_playlist_id') != playlist_id:
                        if st.button("🎵 Cargar Canciones", type="primary", key="load_playlist_tracks"):
                            with st.spinner("Cargando canciones y estadísticas de audio..."):
                                tracks = get_playlist_tracks(sp, playlist_id, include_features=True)
                                if tracks:
                                    # Formatear duración
                                    for track in tracks:
                                        track['duracion'] = format_duration(track['duracion_ms'])
                                    
                                    # Verificar si se obtuvieron estadísticas
                                    tracks_with_stats = sum(1 for t in tracks if t.get('energia') is not None)
                                    if tracks_with_stats > 0:
                                        st.success(f"✅ Cargadas {len(tracks)} canciones con estadísticas de audio para {tracks_with_stats} canciones")
                                    else:
                                        st.warning(f"⚠️ Cargadas {len(tracks)} canciones, pero no se pudieron obtener estadísticas de audio")
                                    
                                    st.session_state[playlist_key] = tracks
                                    st.session_state['spotify_selected_playlist_id'] = playlist_id
                                    st.rerun()
                    else:
                        tracks = st.session_state[playlist_key]
                        
                        if tracks:
                            df_tracks = pd.DataFrame(tracks)
                            
                            # Columnas base siempre visibles
                            base_cols = ['artista', 'titulo', 'album', 'duracion']
                            
                            # Columnas de estadísticas (mostrar si existen en el DataFrame)
                            stats_cols = ['energia', 'danceability', 'valence', 'acousticness', 'tempo']
                            available_stats = [col for col in stats_cols if col in df_tracks.columns]
                            
                            # Columnas a mostrar
                            display_cols = base_cols + available_stats
                            
                            # Mostrar estadísticas promedio solo si hay datos
                            if available_stats:
                                st.markdown("### 📊 Estadísticas Promedio de la Playlist")
                                cols = st.columns(min(len(available_stats), 5))
                                for idx, stat_col in enumerate(available_stats[:5]):
                                    with cols[idx]:
                                        if stat_col == 'energia':
                                            avg = df_tracks[stat_col].mean()
                                            st.metric("⚡ Energía", f"{avg:.1f}%" if not pd.isna(avg) else "N/A")
                                        elif stat_col == 'danceability':
                                            avg = df_tracks[stat_col].mean()
                                            st.metric("💃 Danceability", f"{avg:.1f}%" if not pd.isna(avg) else "N/A")
                                        elif stat_col == 'valence':
                                            avg = df_tracks[stat_col].mean()
                                            st.metric("😊 Valence", f"{avg:.1f}%" if not pd.isna(avg) else "N/A")
                                        elif stat_col == 'acousticness':
                                            avg = df_tracks[stat_col].mean()
                                            st.metric("🎸 Acousticness", f"{avg:.1f}%" if not pd.isna(avg) else "N/A")
                                        elif stat_col == 'tempo':
                                            avg = df_tracks[stat_col].mean()
                                            st.metric("🎵 Tempo", f"{avg:.1f} BPM" if not pd.isna(avg) else "N/A")
                            
                            # Tabla de canciones
                            st.markdown("### 🎵 Canciones")
                            column_config = {
                                'artista': 'Artista',
                                'titulo': 'Título',
                                'album': 'Álbum',
                                'duracion': 'Duración'
                            }
                            
                            # Añadir config para estadísticas
                            if 'energia' in display_cols:
                                column_config['energia'] = st.column_config.NumberColumn('⚡ Energía', format="%.1f%%")
                            if 'danceability' in display_cols:
                                column_config['danceability'] = st.column_config.NumberColumn('💃 Danceability', format="%.1f%%")
                            if 'valence' in display_cols:
                                column_config['valence'] = st.column_config.NumberColumn('😊 Valence', format="%.1f%%")
                            if 'acousticness' in display_cols:
                                column_config['acousticness'] = st.column_config.NumberColumn('🎸 Acousticness', format="%.1f%%")
                            if 'tempo' in display_cols:
                                column_config['tempo'] = st.column_config.NumberColumn('🎵 Tempo', format="%.1f BPM")
                            
                            st.dataframe(
                                df_tracks[display_cols],
                                use_container_width=True,
                                hide_index=True,
                                column_config=column_config
                            )
                            
                            # Botón de descarga
                            csv = df_tracks.to_csv(index=False).encode('utf-8-sig')
                            st.download_button(
                                label="📥 Descargar CSV",
                                data=csv,
                                file_name=f"spotify_playlist_{selected_playlist.replace(' ', '_')}_{int(time.time())}.csv",
                                mime="text/csv"
                            )
                        
                        if st.button("🔄 Recargar Canciones"):
                            if playlist_key in st.session_state:
                                del st.session_state[playlist_key]
                            st.rerun()
                
                if st.button("🔄 Recargar Playlists"):
                    if 'spotify_playlists' in st.session_state:
                        del st.session_state['spotify_playlists']
                    if 'spotify_selected_playlist_id' in st.session_state:
                        del st.session_state['spotify_selected_playlist_id']
                    st.rerun()
        
        else:  # Canciones Guardadas
            st.subheader("❤️ Tus Canciones Guardadas")
            
            # Cargar canciones si no están en session_state
            if 'spotify_saved_tracks' not in st.session_state:
                if st.button("🔄 Cargar Canciones Guardadas", type="primary"):
                    with st.spinner("Cargando canciones guardadas y estadísticas de audio..."):
                        tracks = get_saved_tracks(sp, include_features=True)
                        if tracks:
                            # Formatear duración
                            for track in tracks:
                                track['duracion'] = format_duration(track['duracion_ms'])
                            
                            # Verificar si se obtuvieron estadísticas
                            tracks_with_stats = sum(1 for t in tracks if t.get('energia') is not None)
                            if tracks_with_stats > 0:
                                st.success(f"✅ Cargadas {len(tracks)} canciones con estadísticas de audio para {tracks_with_stats} canciones")
                            else:
                                st.warning(f"⚠️ Cargadas {len(tracks)} canciones, pero no se pudieron obtener estadísticas de audio")
                            
                            st.session_state['spotify_saved_tracks'] = tracks
                            st.rerun()
            else:
                tracks = st.session_state['spotify_saved_tracks']
                df_tracks = pd.DataFrame(tracks)
                
                # Estadísticas generales
                st.markdown("### 📊 Estadísticas Generales")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Canciones", len(tracks))
                with col2:
                    st.metric("Artistas Únicos", df_tracks['artista'].nunique())
                with col3:
                    total_duration = sum(t['duracion_ms'] for t in tracks)
                    hours = total_duration // 3600000
                    minutes = (total_duration % 3600000) // 60000
                    st.metric("Duración Total", f"{hours}h {minutes}m")
                with col4:
                    if 'album' in df_tracks.columns:
                        st.metric("Álbumes Únicos", df_tracks['album'].nunique())
                
                # Estadísticas promedio de audio
                if any(col in df_tracks.columns for col in ['energia', 'danceability', 'valence']):
                    st.markdown("### 📊 Estadísticas Promedio de Audio")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        if 'energia' in df_tracks.columns:
                            avg_energy = df_tracks['energia'].mean()
                            st.metric("⚡ Energía", f"{avg_energy:.1f}%")
                    with col2:
                        if 'danceability' in df_tracks.columns:
                            avg_dance = df_tracks['danceability'].mean()
                            st.metric("💃 Danceability", f"{avg_dance:.1f}%")
                    with col3:
                        if 'valence' in df_tracks.columns:
                            avg_valence = df_tracks['valence'].mean()
                            st.metric("😊 Valence", f"{avg_valence:.1f}%")
                    with col4:
                        if 'acousticness' in df_tracks.columns:
                            avg_acoustic = df_tracks['acousticness'].mean()
                            st.metric("🎸 Acousticness", f"{avg_acoustic:.1f}%")
                    with col5:
                        if 'tempo' in df_tracks.columns:
                            avg_tempo = df_tracks['tempo'].mean()
                            st.metric("🎵 Tempo", f"{avg_tempo:.1f} BPM")
                
                # Columnas base siempre visibles
                base_cols = ['artista', 'titulo', 'album', 'duracion']
                
                # Columnas de estadísticas (mostrar si existen en el DataFrame)
                stats_cols = ['energia', 'danceability', 'valence', 'acousticness', 'tempo']
                available_stats = [col for col in stats_cols if col in df_tracks.columns]
                
                # Columnas a mostrar
                display_cols = base_cols + available_stats
                
                # Tabla de canciones
                st.markdown("### 🎵 Canciones")
                column_config = {
                    'artista': 'Artista',
                    'titulo': 'Título',
                    'album': 'Álbum',
                    'duracion': 'Duración'
                }
                
                # Añadir config para estadísticas
                if 'energia' in display_cols:
                    column_config['energia'] = st.column_config.NumberColumn('⚡ Energía', format="%.1f%%")
                if 'danceability' in display_cols:
                    column_config['danceability'] = st.column_config.NumberColumn('💃 Danceability', format="%.1f%%")
                if 'valence' in display_cols:
                    column_config['valence'] = st.column_config.NumberColumn('😊 Valence', format="%.1f%%")
                if 'acousticness' in display_cols:
                    column_config['acousticness'] = st.column_config.NumberColumn('🎸 Acousticness', format="%.1f%%")
                if 'tempo' in display_cols:
                    column_config['tempo'] = st.column_config.NumberColumn('🎵 Tempo', format="%.1f BPM")
                
                st.dataframe(
                    df_tracks[display_cols],
                    use_container_width=True,
                    hide_index=True,
                    column_config=column_config
                )
                
                # Botón de descarga
                csv = df_tracks.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 Descargar CSV",
                    data=csv,
                    file_name=f"spotify_saved_tracks_{int(time.time())}.csv",
                    mime="text/csv"
                )
                
                if st.button("🔄 Recargar Canciones"):
                    if 'spotify_saved_tracks' in st.session_state:
                        del st.session_state['spotify_saved_tracks']
                    st.rerun()
        
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

