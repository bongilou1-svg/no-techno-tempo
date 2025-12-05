"""
Módulo para procesar archivos TXT de Rekordbox
y comparar con discos scrapeados
"""

import streamlit as st
import pandas as pd
import io
import time
import re
from datetime import datetime
from typing import List, Dict, Tuple
from difflib import SequenceMatcher


def parse_rekordbox_txt(file_content: str) -> pd.DataFrame:
    """
    Parsea un archivo TXT de Rekordbox
    
    Args:
        file_content: Contenido del archivo como string
    
    Returns:
        DataFrame con las columnas parseadas
    """
    lines = file_content.strip().split('\n')
    
    if len(lines) < 2:
        return pd.DataFrame()
    
    # Primera línea son los headers
    headers = lines[0].split('\t')
    
    # Parsear datos
    data = []
    for line in lines[1:]:
        if line.strip():
            values = line.split('\t')
            if len(values) >= len(headers):
                row = {}
                for i, header in enumerate(headers):
                    row[header.strip()] = values[i].strip() if i < len(values) else ''
                data.append(row)
    
    df = pd.DataFrame(data)
    
    # Normalizar nombres de columnas comunes
    if 'Título de la pista' in df.columns:
        df = df.rename(columns={'Título de la pista': 'titulo'})
    if 'Artista' in df.columns:
        df = df.rename(columns={'Artista': 'artista'})
    
    # Separar artista y título si están juntos
    if 'artista' in df.columns and 'titulo' in df.columns:
        df = separate_artist_title(df)
    
    return df


def separate_artist_title(df: pd.DataFrame) -> pd.DataFrame:
    """
    Separa artista y título cuando están juntos en una sola columna
    
    Args:
        df: DataFrame con columnas artista y titulo
    
    Returns:
        DataFrame con artista y título separados
    """
    df = df.copy()
    
    # Si artista está vacío pero título tiene contenido, intentar separar
    for idx, row in df.iterrows():
        artista = str(row.get('artista', '')).strip()
        titulo = str(row.get('titulo', '')).strip()
        
        # Si artista está vacío y título tiene formato "Artista - Título"
        if not artista and titulo:
            # Buscar patrones comunes: "Artista - Título", "Artista / Título", etc.
            separators = [' - ', ' / ', ' – ', ' — ', ' | ']
            for sep in separators:
                if sep in titulo:
                    parts = titulo.split(sep, 1)
                    if len(parts) == 2:
                        df.at[idx, 'artista'] = parts[0].strip()
                        df.at[idx, 'titulo'] = parts[1].strip()
                        break
        
        # Si ambos tienen contenido pero título contiene el artista
        elif artista and titulo:
            # Si el título empieza con el artista, separar
            if titulo.startswith(artista):
                # Remover artista del inicio del título
                titulo_clean = titulo[len(artista):].strip()
                separators = [' - ', ' / ', ' – ', ' — ', ' | ']
                for sep in separators:
                    if titulo_clean.startswith(sep):
                        df.at[idx, 'titulo'] = titulo_clean[len(sep):].strip()
                        break
    
    return df


def normalize_text(text: str) -> str:
    """Normaliza texto para comparación"""
    if not text:
        return ""
    # Convertir a minúsculas, quitar acentos básicos, espacios extra
    text = text.lower().strip()
    # Remover caracteres especiales comunes
    text = re.sub(r'[^\w\s]', '', text)
    # Normalizar espacios
    text = re.sub(r'\s+', ' ', text)
    return text


def similarity_score(str1: str, str2: str) -> float:
    """Calcula similitud entre dos strings"""
    return SequenceMatcher(None, normalize_text(str1), normalize_text(str2)).ratio()


def find_matches_with_progress(rekordbox_df: pd.DataFrame, discos_df: pd.DataFrame, 
                                artist_threshold: float = 0.7, title_threshold: float = 0.7,
                                buscar_cruzado: bool = False):
    """
    Encuentra coincidencias con barra de progreso animada
    
    Args:
        rekordbox_df: DataFrame de Rekordbox
        discos_df: DataFrame de discos scrapeados
        artist_threshold: Umbral de similitud para artista (0-1)
        title_threshold: Umbral de similitud para título (0-1)
        buscar_cruzado: Si True, busca también artista de una lista con título de otra
    
    Yields:
        Tupla (progreso, matches, tiempo_transcurrido)
    """
    matches = []
    
    if rekordbox_df.empty or discos_df.empty:
        yield 100, pd.DataFrame(), 0
        return
    
    # Asegurar que tenemos las columnas necesarias
    if 'artista' not in rekordbox_df.columns or 'titulo' not in rekordbox_df.columns:
        yield 100, pd.DataFrame(), 0
        return
    
    if 'artista' not in discos_df.columns or 'titulo' not in discos_df.columns:
        yield 100, pd.DataFrame(), 0
        return
    
    total_items = len(rekordbox_df) * len(discos_df)
    items_procesados = 0
    inicio = time.time()
    
    for idx_rb, rekordbox_row in rekordbox_df.iterrows():
        rekordbox_artist = str(rekordbox_row.get('artista', '')).strip()
        rekordbox_title = str(rekordbox_row.get('titulo', '')).strip()
        
        if not rekordbox_artist and not rekordbox_title:
            items_procesados += len(discos_df)
            continue
        
        # Si solo tenemos título, buscar solo por título
        search_by_title_only = not rekordbox_artist or rekordbox_artist.lower() in ['unknown', 'desconocido', '']
        
        for idx_disco, disco_row in discos_df.iterrows():
            disco_artist = str(disco_row.get('artista', '')).strip()
            disco_title = str(disco_row.get('titulo', '')).strip()
            
            if not disco_artist and not disco_title:
                items_procesados += 1
                continue
            
            # Búsqueda normal
            if search_by_title_only:
                title_sim = similarity_score(rekordbox_title, disco_title)
                if title_sim >= title_threshold:
                    matches.append({
                        'artista_rekordbox': rekordbox_artist or 'N/A',
                        'titulo_rekordbox': rekordbox_title,
                        'artista_disco': disco_artist,
                        'titulo_disco': disco_title,
                        'precio': disco_row.get('precio', 'N/A'),
                        'estilos': ', '.join(disco_row.get('estilos', [])) if isinstance(disco_row.get('estilos'), list) else str(disco_row.get('estilos', '')),
                        'similitud_artista': 'N/A',
                        'similitud_titulo': f"{title_sim*100:.1f}%",
                        'similitud_total': f"{title_sim*100:.1f}%",
                        'tipo_match': 'Título'
                    })
            else:
                artist_sim = similarity_score(rekordbox_artist, disco_artist)
                title_sim = similarity_score(rekordbox_title, disco_title)
                
                # Coincidencia normal
                if artist_sim >= artist_threshold and title_sim >= title_threshold:
                    matches.append({
                        'artista_rekordbox': rekordbox_artist,
                        'titulo_rekordbox': rekordbox_title,
                        'artista_disco': disco_artist,
                        'titulo_disco': disco_title,
                        'precio': disco_row.get('precio', 'N/A'),
                        'estilos': ', '.join(disco_row.get('estilos', [])) if isinstance(disco_row.get('estilos'), list) else str(disco_row.get('estilos', '')),
                        'similitud_artista': f"{artist_sim*100:.1f}%",
                        'similitud_titulo': f"{title_sim*100:.1f}%",
                        'similitud_total': f"{(artist_sim + title_sim) / 2 * 100:.1f}%",
                        'tipo_match': 'Normal'
                    })
                # Título muy similar aunque artista no tanto
                elif title_sim >= 0.9 and artist_sim >= 0.5:
                    matches.append({
                        'artista_rekordbox': rekordbox_artist,
                        'titulo_rekordbox': rekordbox_title,
                        'artista_disco': disco_artist,
                        'titulo_disco': disco_title,
                        'precio': disco_row.get('precio', 'N/A'),
                        'estilos': ', '.join(disco_row.get('estilos', [])) if isinstance(disco_row.get('estilos'), list) else str(disco_row.get('estilos', '')),
                        'similitud_artista': f"{artist_sim*100:.1f}%",
                        'similitud_titulo': f"{title_sim*100:.1f}%",
                        'similitud_total': f"{(artist_sim + title_sim) / 2 * 100:.1f}%",
                        'tipo_match': 'Título fuerte'
                    })
            
            # Búsqueda cruzada (artista de una lista con título de otra)
            if buscar_cruzado and not search_by_title_only:
                # Artista de Rekordbox con Título de Disco
                artist_rb_title_disco = similarity_score(rekordbox_artist, disco_title)
                title_rb_artist_disco = similarity_score(rekordbox_title, disco_artist)
                
                if artist_rb_title_disco >= artist_threshold and title_rb_artist_disco >= title_threshold:
                    # Verificar que no sea duplicado
                    es_duplicado = any(
                        m.get('artista_rekordbox') == rekordbox_artist and
                        m.get('titulo_rekordbox') == rekordbox_title and
                        m.get('artista_disco') == disco_artist and
                        m.get('titulo_disco') == disco_title
                        for m in matches
                    )
                    
                    if not es_duplicado:
                        matches.append({
                            'artista_rekordbox': rekordbox_artist,
                            'titulo_rekordbox': rekordbox_title,
                            'artista_disco': disco_artist,
                            'titulo_disco': disco_title,
                            'precio': disco_row.get('precio', 'N/A'),
                            'estilos': ', '.join(disco_row.get('estilos', [])) if isinstance(disco_row.get('estilos'), list) else str(disco_row.get('estilos', '')),
                            'similitud_artista': f"{artist_rb_title_disco*100:.1f}%",
                            'similitud_titulo': f"{title_rb_artist_disco*100:.1f}%",
                            'similitud_total': f"{(artist_rb_title_disco + title_rb_artist_disco) / 2 * 100:.1f}%",
                            'tipo_match': 'Cruzado'
                        })
            
            items_procesados += 1
            
            # Actualizar progreso cada 50 items o al final
            if items_procesados % 50 == 0 or items_procesados == total_items:
                progreso = (items_procesados / total_items) * 100
                tiempo_transcurrido = time.time() - inicio
                yield progreso, pd.DataFrame(matches), tiempo_transcurrido
    
    # Final
    tiempo_total = time.time() - inicio
    yield 100, pd.DataFrame(matches), tiempo_total


def render_progress_animation(progreso: float, tiempo_transcurrido: float, tiempo_estimado: float = None):
    """Renderiza animación del monigote rebuscando"""
    # Emojis del monigote en diferentes posiciones
    frames = [
        "🧑‍💼📦🔍",
        "🧑‍💼📦  ",
        "🧑‍💼  📦",
        "  🧑‍💼📦",
    ]
    
    frame_index = int((progreso / 100) * len(frames)) % len(frames)
    monigote = frames[frame_index]
    
    # Crear HTML para la animación
    html = f"""
    <div style="text-align: center; padding: 2rem; background: #f8f9fa; border-radius: 10px; margin: 1rem 0;">
        <div style="font-size: 3rem; margin-bottom: 1rem;">{monigote}</div>
        <div style="font-size: 1.2rem; font-weight: 600; color: #212529; margin-bottom: 0.5rem;">
            Buscando coincidencias... {progreso:.1f}%
        </div>
        <div style="width: 100%; background: #e9ecef; border-radius: 10px; height: 20px; margin: 1rem 0;">
            <div style="width: {progreso}%; background: linear-gradient(90deg, #212529, #495057); height: 20px; border-radius: 10px; transition: width 0.3s;"></div>
        </div>
        <div style="font-size: 0.9rem; color: #6c757d;">
            Tiempo transcurrido: {tiempo_transcurrido:.1f}s
            {f' | Estimado: {tiempo_estimado:.1f}s' if tiempo_estimado else ''}
        </div>
    </div>
    """
    return html


def render_rekordbox_tab(user_id: str = None):
    """Renderiza la pestaña de Rekordbox (ahora solo para subir archivo)"""
    
    st.markdown("### Importar Lista de Rekordbox")
    st.markdown("Sube tu archivo TXT exportado de Rekordbox")
    st.markdown("---")
    
    # Uploader de archivo
    uploaded_file = st.file_uploader(
        "Selecciona tu archivo TXT de Rekordbox",
        type=['txt'],
        help="Exporta tu lista desde Rekordbox como TXT y súbela aquí"
    )
    
    if uploaded_file is not None:
        try:
            # Leer archivo con diferentes encodings
            file_bytes = uploaded_file.read()
            content = None
            
            # Intentar diferentes encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    content = file_bytes.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                # Si ninguno funciona, usar errors='replace' para ignorar caracteres problemáticos
                content = file_bytes.decode('utf-8', errors='replace')
            
            rekordbox_df = parse_rekordbox_txt(content)
            
            if not rekordbox_df.empty:
                st.success(f"✅ Archivo cargado correctamente: {len(rekordbox_df)} pistas encontradas")
                
                # Guardar en session state y en almacenamiento persistente
                st.session_state['rekordbox_df'] = rekordbox_df
                
                # Guardar de forma persistente
                if user_id:
                    try:
                        from data_storage import save_rekordbox
                        save_rekordbox(rekordbox_df, user_id)
                        st.success("💾 Lista guardada correctamente")
                    except Exception as e:
                        st.warning(f"No se pudo guardar la lista: {e}")
                
                # Mostrar preview
                with st.expander("👀 Vista previa de tu lista de Rekordbox"):
                    display_cols = ['artista', 'titulo']
                    if 'BPM' in rekordbox_df.columns:
                        display_cols.append('BPM')
                    if 'Género' in rekordbox_df.columns:
                        display_cols.append('Género')
                    
                    available_cols = [col for col in display_cols if col in rekordbox_df.columns]
                    if available_cols:
                        st.dataframe(
                            rekordbox_df[available_cols].head(20),
                            use_container_width=True,
                            hide_index=True
                        )
            else:
                st.error("No se pudieron parsear los datos del archivo")
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
    else:
        # Intentar cargar desde almacenamiento persistente
        if user_id:
            try:
                from data_storage import get_rekordbox, get_rekordbox_fecha, clear_rekordbox
                saved_rekordbox = get_rekordbox(user_id)
                
                if not saved_rekordbox.empty:
                    fecha_carga = get_rekordbox_fecha(user_id)
                    if fecha_carga:
                        fecha_str = datetime.fromisoformat(fecha_carga).strftime("%d/%m/%Y %H:%M")
                        st.info(f"📋 Lista guardada: {len(saved_rekordbox)} pistas (cargada el {fecha_str})")
                    else:
                        st.info(f"📋 Lista guardada: {len(saved_rekordbox)} pistas")
                    
                    # Cargar en session state
                    st.session_state['rekordbox_df'] = saved_rekordbox
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🔄 Recargar lista guardada", use_container_width=True):
                            st.session_state['rekordbox_df'] = saved_rekordbox
                            st.rerun()
                    with col2:
                        if st.button("🗑️ Eliminar lista", use_container_width=True):
                            clear_rekordbox(user_id)
                            if 'rekordbox_df' in st.session_state:
                                st.session_state.pop('rekordbox_df')
                            st.rerun()
            except Exception as e:
                pass
    
    with st.expander("ℹ️ Cómo exportar desde Rekordbox"):
        st.markdown("""
        **Pasos para exportar tu lista desde Rekordbox:**
        
        1. Abre Rekordbox
        2. Selecciona las pistas que quieres exportar
        3. Ve a **Archivo > Exportar > Lista de reproducción como texto**
        4. Guarda el archivo
        5. Súbelo aquí
        
        **Formato esperado:**
        El archivo debe ser un TXT con columnas separadas por tabs (formato estándar de Rekordbox)
        """)
