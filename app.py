"""
NoTechnoTempo - Tu biblioteca musical definitiva
Portada principal: Comparación de coincidencias
Pestañas: Configuración y búsqueda
"""

import streamlit as st
import pandas as pd
from scraper import scrape_discos_paradiso, get_available_styles
from utils import apply_custom_css, render_header
from auth_module import check_auth, get_current_user_id, get_current_user_email
from data_storage import (
    load_data, save_data, add_discos, get_all_discos, 
    get_estilos_info, get_ultima_actualizacion
)
from rekordbox_module import find_matches_with_progress, render_progress_animation, parse_rekordbox_txt
from datetime import datetime
import time

# Configuración de la página
st.set_page_config(
    page_title="NoTechnoTempo",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== AUTENTICACIÓN ====================
# Verificar autenticación
user_id = check_auth()

if not user_id:
    st.stop()  # Detener ejecución si no está autenticado

# Aplicar estilos personalizados
apply_custom_css()

# Renderizar header
render_header()

# Mostrar información del usuario
user_email = get_current_user_email()
if user_email:
    st.sidebar.markdown(f"👤 **{user_email}**")

# ==================== PORTADA PRINCIPAL: COMPARACIÓN ====================
# Cargar datos guardados del usuario
all_discos_df = get_all_discos(user_id)
estilos_info = get_estilos_info(user_id)
ultima_actualizacion = get_ultima_actualizacion(user_id)

# Cargar Rekordbox guardado
from data_storage import get_rekordbox, get_rekordbox_fecha
rekordbox_df = get_rekordbox(user_id)
rekordbox_fecha = get_rekordbox_fecha(user_id)

# Si hay Rekordbox en session state (recién cargado), guardarlo
if 'rekordbox_df' in st.session_state and st.session_state['rekordbox_df'] is not None:
    rekordbox_df = st.session_state['rekordbox_df']
    from data_storage import save_rekordbox
    save_rekordbox(rekordbox_df, user_id)
    rekordbox_fecha = get_rekordbox_fecha(user_id)

# ==================== DASHBOARD PRINCIPAL ====================
# Métricas principales en grid compacto
col1, col2, col3, col4 = st.columns(4)
with col1:
    if rekordbox_df is not None and not rekordbox_df.empty:
        st.metric("📋 Pistas Rekordbox", len(rekordbox_df), 
                 delta=f"Cargado: {datetime.fromisoformat(rekordbox_fecha).strftime('%d/%m/%Y')}" if rekordbox_fecha else None)
    else:
        st.metric("📋 Pistas Rekordbox", "No cargadas", 
                 delta="Cargar en pestaña Rekordbox", delta_color="off")
        
with col2:
    if not all_discos_df.empty:
        st.metric("💿 Discos Guardados", len(all_discos_df))
    else:
        st.metric("💿 Discos Guardados", "0", 
                 delta="Buscar en pestaña Discos", delta_color="off")
        
with col3:
    if ultima_actualizacion:
        fecha = datetime.fromisoformat(ultima_actualizacion).strftime("%d/%m/%Y %H:%M")
        st.metric("🕐 Última Actualización", fecha.split()[0], 
                 delta=f"{fecha.split()[1]}")
    else:
        st.metric("🕐 Última Actualización", "Nunca", 
                 delta="Ejecutar búsqueda", delta_color="off")
        
with col4:
    if estilos_info:
        total_estilos = len(estilos_info)
        st.metric("🎵 Estilos Guardados", total_estilos)
    else:
        st.metric("🎵 Estilos Guardados", "0", 
                 delta="Buscar estilos", delta_color="off")

# ==================== PESTAÑAS PRINCIPALES ====================
tab_main, tab_discos, tab_spotify, tab_local, tab_rekordbox = st.tabs([
    "🔍 Buscar Coincidencias", 
    "⚙️ Buscar Discos", 
    "🎧 Spotify", 
    "💿 Música Local", 
    "📋 Rekordbox TXT"
])

# ==================== PESTAÑA PRINCIPAL: COINCIDENCIAS ====================
with tab_main:
    # Dashboard resumen
    if estilos_info:
        col_info1, col_info2 = st.columns([3, 1])
        with col_info1:
            estilos_text = ", ".join([", ".join(info['estilos']) for info in estilos_info.values()])
            st.caption(f"📊 Estilos: {estilos_text}")
        with col_info2:
            total_discos = sum([info['total_discos'] for info in estilos_info.values()])
            st.caption(f"💿 Total: {total_discos} discos")
    
    # ==================== BÚSQUEDA DE COINCIDENCIAS ====================
    if rekordbox_df is not None and not rekordbox_df.empty and len(rekordbox_df) > 0:
        if not all_discos_df.empty:
            # Panel de configuración compacto
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                artist_threshold = st.slider(
                    "Umbral Artista",
                    min_value=0.5,
                    max_value=1.0,
                    value=0.7,
                    step=0.05
                )
            with col2:
                title_threshold = st.slider(
                    "Umbral Título",
                    min_value=0.5,
                    max_value=1.0,
                    value=0.7,
                    step=0.05
                )
            with col3:
                buscar_cruzado = st.checkbox(
                    "🔀 Cruzado",
                    value=False,
                    help="Buscar cruzado"
                )
                if st.button("🔍 Buscar", type="primary", use_container_width=True):
                    # Calcular total de items y tiempo estimado
                    total_items = len(rekordbox_df) * len(all_discos_df)
                    from data_storage import get_tiempo_estimado, save_tiempo_busqueda
                    tiempo_estimado = get_tiempo_estimado(total_items, user_id)
                    
                    # Contenedor para la animación
                    progress_container = st.empty()
                    
                    # Realizar búsqueda con progreso
                    matches_df = pd.DataFrame()
                    tiempo_total = 0
                    
                    try:
                        from rekordbox_module import find_matches_with_progress, render_progress_animation
                        
                        for progreso, matches_parciales, tiempo_transcurrido in find_matches_with_progress(
                            rekordbox_df, 
                            all_discos_df,
                            artist_threshold=artist_threshold,
                            title_threshold=title_threshold,
                            buscar_cruzado=buscar_cruzado
                        ):
                            matches_df = matches_parciales
                            tiempo_total = tiempo_transcurrido
                            
                            # Actualizar animación
                            html_animacion = render_progress_animation(progreso, tiempo_transcurrido, tiempo_estimado)
                            progress_container.markdown(html_animacion, unsafe_allow_html=True)
                            
                            # Pequeña pausa para que se vea la animación
                            time.sleep(0.05)
                        
                        # Guardar tiempo de búsqueda
                        save_tiempo_busqueda(tiempo_total, total_items, user_id)
                        
                        # Limpiar animación y mostrar resultados
                        progress_container.empty()
                        
                        if not matches_df.empty:
                            # Estadísticas compactas
                            col1, col2, col3, col4, col5 = st.columns(5)
                            with col1:
                                st.metric("Coincidencias", len(matches_df))
                            with col2:
                                porcentaje = (len(matches_df) / len(rekordbox_df)) * 100
                                st.metric("% de tu lista", f"{porcentaje:.1f}%")
                            with col3:
                                total_precio = sum([
                                    float(str(precio).replace('€', '').replace(',', '.')) 
                                    for precio in matches_df['precio'] 
                                    if precio != 'N/A' and '€' in str(precio)
                                ])
                                st.metric("Precio Total", f"{total_precio:.0f}€")
                            with col4:
                                estilos_unicos = matches_df['estilos'].nunique() if 'estilos' in matches_df.columns else 0
                                st.metric("Estilos", estilos_unicos)
                            with col5:
                                st.metric("⏱️", f"{tiempo_total:.1f}s")
                            
                            # Mostrar coincidencias
                            display_cols = ['artista_rekordbox', 'titulo_rekordbox', 'artista_disco', 'titulo_disco', 'precio']
                            if 'estilos' in matches_df.columns:
                                display_cols.append('estilos')
                            if 'similitud_total' in matches_df.columns:
                                display_cols.append('similitud_total')
                            if 'tipo_match' in matches_df.columns:
                                display_cols.append('tipo_match')
                            
                            st.dataframe(
                                matches_df[display_cols],
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    'artista_rekordbox': 'Artista (Rekordbox)',
                                    'titulo_rekordbox': 'Título (Rekordbox)',
                                    'artista_disco': 'Artista (Disco)',
                                    'titulo_disco': 'Título (Disco)',
                                    'precio': 'Precio',
                                    'estilos': 'Estilos',
                                    'similitud_total': 'Similitud',
                                    'tipo_match': 'Tipo'
                                }
                            )
                            
                            # Botón de descarga
                            csv = matches_df.to_csv(index=False).encode('utf-8-sig')
                            st.download_button(
                                label="📥 Descargar Coincidencias (CSV)",
                                data=csv,
                                file_name=f"coincidencias_rekordbox_{int(time.time())}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        else:
                            progress_container.empty()
                            st.warning("No se encontraron coincidencias con los umbrales seleccionados.")
                            st.info("💡 **Sugerencias:**\n- Reduce los umbrales de similitud (artista/título)\n- Activa la búsqueda cruzada\n- Busca más discos en la pestaña 'Buscar Discos'")
                    
                    except ImportError:
                        # Fallback si no está disponible la función con progreso
                        from rekordbox_module import find_matches
                        matches_df = find_matches(
                            rekordbox_df, 
                            all_discos_df,
                            artist_threshold=artist_threshold,
                            title_threshold=title_threshold
                        )
                        
                        if not matches_df.empty:
                            st.success(f"🎉 ¡Se encontraron {len(matches_df)} coincidencias!")
                            
                            # Estadísticas
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Coincidencias", len(matches_df))
                            with col2:
                                porcentaje = (len(matches_df) / len(rekordbox_df)) * 100
                                st.metric("% de tu lista", f"{porcentaje:.1f}%")
                            with col3:
                                total_precio = sum([
                                    float(str(precio).replace('€', '').replace(',', '.')) 
                                    for precio in matches_df['precio'] 
                                    if precio != 'N/A' and '€' in str(precio)
                                ])
                                st.metric("Precio Total", f"{total_precio:.0f}€")
                            with col4:
                                estilos_unicos = matches_df['estilos'].nunique() if 'estilos' in matches_df.columns else 0
                                st.metric("Estilos", estilos_unicos)
                            
                            st.markdown("---")
                            st.markdown("#### 📋 Coincidencias Encontradas")
                            
                            # Mostrar coincidencias
                            display_cols = ['artista_rekordbox', 'titulo_rekordbox', 'artista_disco', 'titulo_disco', 'precio']
                            if 'estilos' in matches_df.columns:
                                display_cols.append('estilos')
                            if 'similitud_total' in matches_df.columns:
                                display_cols.append('similitud_total')
                            
                            st.dataframe(
                                matches_df[display_cols],
                                use_container_width=True,
                                hide_index=True,
                                column_config={
                                    'artista_rekordbox': 'Artista (Rekordbox)',
                                    'titulo_rekordbox': 'Título (Rekordbox)',
                                    'artista_disco': 'Artista (Disco)',
                                    'titulo_disco': 'Título (Disco)',
                                    'precio': 'Precio',
                                    'estilos': 'Estilos',
                                    'similitud_total': 'Similitud'
                                }
                            )
                            
                            # Botón de descarga
                            csv = matches_df.to_csv(index=False).encode('utf-8-sig')
                            st.download_button(
                                label="📥 Descargar Coincidencias (CSV)",
                                data=csv,
                                file_name=f"coincidencias_rekordbox_{int(time.time())}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        else:
                            st.warning("No se encontraron coincidencias con los umbrales seleccionados.")
                            st.info("💡 Prueba a reducir los umbrales de similitud o busca más discos en la pestaña de configuración.")
                    except Exception as e:
                        st.error(f"Error durante la búsqueda: {e}")
        else:
            st.warning("⚠️ No hay discos guardados. Ve a la pestaña '⚙️ Buscar Discos'.")
    else:
        st.info("👆 Carga tu lista en la pestaña '📋 Rekordbox TXT'")

# ==================== PESTAÑA 2: BUSCAR DISCOS ====================
with tab_discos:
    # Layout compacto
    col_filters, col_results = st.columns([1, 2], gap="medium")
    
    with col_filters:
        available_styles = get_available_styles()
        selected_styles = st.multiselect(
            "Estilos",
            options=available_styles,
            default=[],
            help="Selecciona estilos"
        )
        ejecutar = st.button("🚀 Buscar", type="primary", use_container_width=True)
        st.caption("Género: Electronic | Formato: Vinyl")
        if selected_styles:
            estilo_key = "|".join(sorted(selected_styles))
            if estilo_key in estilos_info:
                info = estilos_info[estilo_key]
                fecha = datetime.fromisoformat(info['fecha_busqueda']).strftime("%d/%m/%Y")
                st.caption(f"📅 {fecha} | 💿 {info['total_discos']} discos")
    
    with col_results:
        if ejecutar:
            if not selected_styles:
                st.warning("Por favor, selecciona al menos un estilo antes de buscar.")
            else:
                with st.spinner(f"Buscando discos con estilos: {', '.join(selected_styles)}..."):
                    # Ejecutar scraping
                    resultados = scrape_discos_paradiso(styles=selected_styles)
                    
                    if resultados:
                        st.success(f"Se encontraron {len(resultados)} discos")
                        
                        # Guardar discos
                        add_discos(selected_styles, resultados, user_id)
                        st.success("✅ Discos guardados correctamente")
                        
                        # Recargar datos
                        all_discos_df = get_all_discos(user_id)
                        estilos_info = get_estilos_info(user_id)
                        st.rerun()
                        
                        # Convertir a DataFrame
                        df = pd.DataFrame(resultados)
                        
                        # Mostrar tabla compacta
                        st.dataframe(
                            df,
                            use_container_width=True,
                            hide_index=True,
                            height=300,
                            column_config={
                                "artista": "Artista",
                                "titulo": "Título",
                                "precio": "Precio"
                            }
                        )
                    else:
                        st.error("No se encontraron resultados.")
        else:
            st.info("👈 Selecciona estilos y haz clic en 'Buscar'")
    
    # ==================== LISTA DE DISCOS GUARDADOS ====================
    if not all_discos_df.empty:
        st.markdown("---")
        st.markdown("### 💿 Lista de Discos Guardados")
        
        # Filtros compactos
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            # Filtro por estilos
            if 'estilos' in all_discos_df.columns:
                estilos_unicos = set()
                for estilos_str in all_discos_df['estilos']:
                    if isinstance(estilos_str, list):
                        estilos_unicos.update(estilos_str)
                    elif isinstance(estilos_str, str):
                        estilos_unicos.update([e.strip() for e in estilos_str.split(',')])
                
                estilo_filtro = st.multiselect(
                    "Estilos",
                    options=sorted(estilos_unicos),
                    default=[],
                    help="Filtrar por estilos"
                )
            else:
                estilo_filtro = []
        
        with col2:
            # Búsqueda de texto
            busqueda_texto = st.text_input(
                "🔍 Buscar",
                placeholder="Artista o título...",
                help="Buscar en artistas y títulos"
            )
        
        with col3:
            st.caption(f"Total: {len(all_discos_df)}")
        
        # Aplicar filtros
        discos_filtrados = all_discos_df.copy()
        
        if estilo_filtro:
            # Filtrar por estilos
            mask = discos_filtrados['estilos'].apply(
                lambda x: any(estilo in str(x) for estilo in estilo_filtro)
            )
            discos_filtrados = discos_filtrados[mask]
        
        if busqueda_texto:
            # Filtrar por texto
            busqueda_lower = busqueda_texto.lower()
            mask = (
                discos_filtrados['artista'].astype(str).str.lower().str.contains(busqueda_lower, na=False) |
                discos_filtrados['titulo'].astype(str).str.lower().str.contains(busqueda_lower, na=False)
            )
            discos_filtrados = discos_filtrados[mask]
        
        # Mostrar tabla compacta
        if not discos_filtrados.empty:
            # Columnas a mostrar
            display_cols = ['artista', 'titulo', 'precio']
            if 'estilos' in discos_filtrados.columns:
                display_cols.append('estilos')
            if 'fecha_busqueda' in discos_filtrados.columns:
                display_cols.append('fecha_busqueda')
            
            # Formatear fechas
            discos_display = discos_filtrados[display_cols].copy()
            if 'fecha_busqueda' in discos_display.columns:
                discos_display['fecha_busqueda'] = discos_display['fecha_busqueda'].apply(
                    lambda x: datetime.fromisoformat(x).strftime("%d/%m/%Y %H:%M") if pd.notna(x) else "N/A"
                )
            
            st.dataframe(
                discos_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "artista": "Artista",
                    "titulo": "Título",
                    "precio": "Precio",
                    "estilos": "Estilos",
                    "fecha_busqueda": "Fecha Búsqueda"
                }
            )
            
            # Botón de descarga compacto
            csv_filtrado = discos_filtrados[['artista', 'titulo', 'precio', 'estilos']].to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Descargar CSV",
                data=csv_filtrado,
                file_name=f"discos_{int(time.time())}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.info("No hay discos que coincidan con los filtros.")
    else:
        st.info("💡 No hay discos guardados. Busca discos arriba para comenzar.")

# ==================== PESTAÑA 3: SPOTIFY ====================
with tab_spotify:
    try:
        from spotify_module import render_spotify_tab
        render_spotify_tab(user_id)
    except ImportError:
        st.info("🔧 Módulo en desarrollo")

# ==================== PESTAÑA 4: MÚSICA LOCAL ====================
with tab_local:
    try:
        from local_music import render_local_music_tab
        render_local_music_tab()
    except ImportError:
        st.info("🔧 Módulo en desarrollo")

# ==================== PESTAÑA 5: REKORDBOX TXT ====================
with tab_rekordbox:
    try:
        from rekordbox_module import render_rekordbox_tab
        render_rekordbox_tab(user_id)
    except ImportError:
        st.info("🔧 Módulo en desarrollo")
