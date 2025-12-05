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


def authenticate_spotify(client_id: str, client_secret: str, redirect_uri: str) -> bool:
    """
    Autentica con Spotify usando OAuth
    
    Args:
        client_id: Client ID de la app de Spotify
        client_secret: Client Secret de la app de Spotify
        redirect_uri: URI de redirección
    
    Returns:
        True si la autenticación fue exitosa
    """
    try:
        scope = "user-library-read playlist-read-private playlist-read-collaborative"
        
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_path=".spotify_cache"
        )
        
        # Obtener token
        token_info = auth_manager.get_access_token()
        
        if token_info:
            st.session_state['spotify_token'] = token_info['access_token']
            st.session_state['spotify_client_id'] = client_id
            st.session_state['spotify_client_secret'] = client_secret
            return True
        
        return False
    except Exception as e:
        st.error(f"Error en autenticación: {e}")
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
    results = sp.playlist_tracks(playlist_id, limit=100)
    
    while results:
        for item in results['items']:
            if item['track']:
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
        
        with st.expander("🔑 Configuración de Spotify"):
            st.markdown("""
            ### Pasos para obtener credenciales:
            
            1. Ve a [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
            2. Crea una nueva app
            3. Copia el **Client ID** y **Client Secret**
            4. Añade `http://localhost:8501` como Redirect URI en la configuración de tu app
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                client_id = st.text_input("Client ID", type="default")
            with col2:
                client_secret = st.text_input("Client Secret", type="password")
            
            redirect_uri = st.text_input("Redirect URI", value="http://localhost:8501")
            
            if st.button("🔗 Conectar con Spotify", type="primary"):
                if client_id and client_secret:
                    if authenticate_spotify(client_id, client_secret, redirect_uri):
                        st.success("✅ Conectado exitosamente!")
                        st.rerun()
                    else:
                        st.error("❌ Error al conectar. Verifica tus credenciales.")
                else:
                    st.warning("⚠️ Por favor, completa todos los campos")
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
        if st.button("🚪 Desconectar"):
            if 'spotify_token' in st.session_state:
                del st.session_state['spotify_token']
            st.rerun()

