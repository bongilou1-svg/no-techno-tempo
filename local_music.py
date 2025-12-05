"""
Módulo para escanear música local del PC
Permite seleccionar carpetas y extraer metadatos de archivos de audio
"""

import streamlit as st
import pandas as pd
import os
from pathlib import Path
from typing import List, Dict
import time

try:
    from mutagen import File
    from mutagen.id3 import ID3NoHeaderError
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


# Formatos de audio soportados
AUDIO_EXTENSIONS = {
    '.mp3', '.flac', '.wav', '.m4a', '.aac', '.ogg', '.oga', '.opus',
    '.wma', '.aiff', '.aif', '.mp4', '.m4p', '.3gp', '.amr', '.ape',
    '.au', '.ra', '.rm', '.tta', '.vox', '.webm'
}


def scan_directory(directory: str) -> List[Dict]:
    """
    Escanea un directorio recursivamente buscando archivos de audio
    
    Args:
        directory: Ruta del directorio a escanear
    
    Returns:
        Lista de diccionarios con información de archivos de audio
    """
    audio_files = []
    directory_path = Path(directory)
    
    if not directory_path.exists():
        return []
    
    # Recorrer recursivamente
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in AUDIO_EXTENSIONS:
                audio_files.append(str(file_path))
    
    return audio_files


def extract_metadata(file_path: str) -> Dict:
    """
    Extrae metadatos de un archivo de audio
    
    Args:
        file_path: Ruta del archivo de audio
    
    Returns:
        Diccionario con metadatos extraídos
    """
    metadata = {
        'archivo': os.path.basename(file_path),
        'ruta': file_path,
        'artista': 'Desconocido',
        'titulo': os.path.splitext(os.path.basename(file_path))[0],
        'album': 'Desconocido',
        'duracion': 'N/A',
        'formato': os.path.splitext(file_path)[1].upper()
    }
    
    if not MUTAGEN_AVAILABLE:
        return metadata
    
    try:
        audio_file = File(file_path)
        
        if audio_file is not None:
            # Extraer artista
            if 'TPE1' in audio_file or 'ARTIST' in audio_file:
                artist = audio_file.get('TPE1', audio_file.get('ARTIST', ['Desconocido']))[0]
                if artist:
                    metadata['artista'] = str(artist)
            
            # Extraer título
            if 'TIT2' in audio_file or 'TITLE' in audio_file:
                title = audio_file.get('TIT2', audio_file.get('TITLE', [metadata['titulo']]))[0]
                if title:
                    metadata['titulo'] = str(title)
            
            # Extraer álbum
            if 'TALB' in audio_file or 'ALBUM' in audio_file:
                album = audio_file.get('TALB', audio_file.get('ALBUM', ['Desconocido']))[0]
                if album:
                    metadata['album'] = str(album)
            
            # Extraer duración
            if hasattr(audio_file, 'info') and hasattr(audio_file.info, 'length'):
                duration_sec = int(audio_file.info.length)
                minutes = duration_sec // 60
                seconds = duration_sec % 60
                metadata['duracion'] = f"{minutes}:{seconds:02d}"
        
    except (ID3NoHeaderError, Exception) as e:
        # Si no se pueden extraer metadatos, usar valores por defecto
        pass
    
    return metadata


def format_duration(seconds: float) -> str:
    """Formatea duración en segundos a mm:ss"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def render_local_music_tab():
    """Renderiza la pestaña de música local"""
    
    st.info("💡 Selecciona una carpeta para escanear archivos de audio")
    
    # Selector de carpeta
    folder_path = st.text_input(
        "📁 Ruta de la carpeta a escanear:",
        placeholder="Ej: C:\\Users\\TuUsuario\\Music o /home/usuario/Music",
        help="Introduce la ruta completa de la carpeta que contiene tu música"
    )
    
    if folder_path:
        if st.button("🔍 Escanear Carpeta", type="primary"):
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                with st.spinner("🔍 Escaneando carpeta... Esto puede tardar un poco..."):
                    # Escanear archivos
                    audio_files = scan_directory(folder_path)
                    
                    if audio_files:
                        st.success(f"✅ Encontrados {len(audio_files)} archivos de audio")
                        
                        # Barra de progreso
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Extraer metadatos
                        all_metadata = []
                        total_files = len(audio_files)
                        
                        for i, file_path in enumerate(audio_files):
                            metadata = extract_metadata(file_path)
                            all_metadata.append(metadata)
                            
                            # Actualizar progreso
                            progress = (i + 1) / total_files
                            progress_bar.progress(progress)
                            status_text.text(f"Procesando {i + 1}/{total_files}: {os.path.basename(file_path)}")
                        
                        progress_bar.empty()
                        status_text.empty()
                        
                        # Crear DataFrame
                        df = pd.DataFrame(all_metadata)
                        
                        # Mostrar resultados
                        st.subheader("📀 Archivos de Audio Encontrados")
                        st.dataframe(
                            df[['artista', 'titulo', 'album', 'duracion', 'formato']],
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                'artista': 'Artista',
                                'titulo': 'Título',
                                'album': 'Álbum',
                                'duracion': 'Duración',
                                'formato': 'Formato'
                            }
                        )
                        
                        # Estadísticas
                        st.markdown("---")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Archivos", len(all_metadata))
                        with col2:
                            st.metric("Artistas Únicos", df['artista'].nunique())
                        with col3:
                            st.metric("Álbumes Únicos", df['album'].nunique())
                        with col4:
                            formats = df['formato'].value_counts()
                            st.metric("Formatos", len(formats))
                        
                        # Distribución por formato
                        if len(formats) > 0:
                            st.subheader("📊 Distribución por Formato")
                            st.bar_chart(formats)
                        
                        # Botón de descarga
                        csv = df.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            label="📥 Descargar CSV",
                            data=csv,
                            file_name=f"musica_local_{int(time.time())}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    else:
                        st.warning("⚠️ No se encontraron archivos de audio en la carpeta especificada")
                        st.info("💡 Asegúrate de que la carpeta contenga archivos de audio en formatos soportados")
            else:
                st.error("❌ La ruta especificada no existe o no es un directorio válido")
    
    # Información sobre formatos soportados
    with st.expander("ℹ️ Formatos de Audio Soportados"):
        st.markdown("""
        ### Formatos compatibles:
        
        - **MP3** - Formato más común
        - **FLAC** - Audio sin pérdida
        - **WAV** - Audio sin comprimir
        - **M4A/AAC** - Formato de Apple
        - **OGG/OPUS** - Formatos abiertos
        - **WMA** - Windows Media Audio
        - **AIFF** - Audio Interchange File Format
        - Y muchos más...
        
        ### Nota:
        La extracción de metadatos depende del formato del archivo. 
        Algunos archivos pueden no tener metadatos completos.
        """)
    
    if not MUTAGEN_AVAILABLE:
        st.warning("⚠️ La biblioteca 'mutagen' no está instalada. La extracción de metadatos será limitada.")
        st.info("💡 Instala mutagen con: `pip install mutagen`")

