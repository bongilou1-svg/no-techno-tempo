"""
Módulo para almacenar y gestionar datos persistentes
Aislamiento de datos por usuario
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import hashlib


DATA_DIR = "data"
USERS_DIR = os.path.join(DATA_DIR, "users")


def get_user_id(email: str) -> str:
    """Genera un ID único para el usuario basado en su email"""
    return hashlib.md5(email.encode()).hexdigest()


def get_user_data_file(user_id: str) -> str:
    """Obtiene la ruta del archivo de datos del usuario"""
    user_dir = os.path.join(USERS_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, "no_techno_data.json")


def load_data(user_id: str) -> Dict:
    """Carga los datos guardados del usuario"""
    data_file = get_user_data_file(user_id)
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return get_default_data()
    return get_default_data()


def save_data(data: Dict, user_id: str):
    """Guarda los datos del usuario"""
    data_file = get_user_data_file(user_id)
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_default_data() -> Dict:
    """Retorna estructura de datos por defecto"""
    return {
        "discos": [],
        "estilos": {},
        "ultima_actualizacion": None,
        "rekordbox": None,
        "tiempos_busqueda": [],
        "spotify_credentials": None  # Guardar credenciales de Spotify de forma segura
    }


def add_discos(estilos: List[str], discos: List[Dict], user_id: str):
    """
    Añade o actualiza discos para estilos específicos
    
    Args:
        estilos: Lista de estilos usados en la búsqueda
        discos: Lista de discos encontrados
        user_id: ID del usuario
    """
    data = load_data(user_id)
    
    # Crear clave única para los estilos (ordenada)
    estilo_key = "|".join(sorted(estilos))
    
    # Actualizar información del estilo
    data["estilos"][estilo_key] = {
        "estilos": estilos,
        "fecha_busqueda": datetime.now().isoformat(),
        "total_discos": len(discos)
    }
    
    # Eliminar discos antiguos de estos estilos
    data["discos"] = [
        d for d in data["discos"] 
        if d.get("estilos_key") != estilo_key
    ]
    
    # Añadir nuevos discos con metadata
    for disco in discos:
        disco["estilos_key"] = estilo_key
        disco["estilos"] = estilos
        disco["fecha_busqueda"] = datetime.now().isoformat()
        data["discos"].append(disco)
    
    data["ultima_actualizacion"] = datetime.now().isoformat()
    save_data(data, user_id)


def get_all_discos(user_id: str) -> pd.DataFrame:
    """Obtiene todos los discos guardados como DataFrame"""
    data = load_data(user_id)
    if not data["discos"]:
        return pd.DataFrame()
    
    return pd.DataFrame(data["discos"])


def get_estilos_info(user_id: str) -> Dict:
    """Obtiene información de los estilos guardados"""
    data = load_data(user_id)
    return data.get("estilos", {})


def get_ultima_actualizacion(user_id: str) -> Optional[str]:
    """Obtiene la fecha de última actualización"""
    data = load_data(user_id)
    return data.get("ultima_actualizacion")


def save_rekordbox(rekordbox_df: pd.DataFrame, user_id: str):
    """
    Guarda el DataFrame de Rekordbox
    
    Args:
        rekordbox_df: DataFrame de Rekordbox
        user_id: ID del usuario
    """
    data = load_data(user_id)
    
    # Convertir DataFrame a lista de diccionarios
    if not rekordbox_df.empty:
        data["rekordbox"] = rekordbox_df.to_dict('records')
        data["rekordbox_fecha"] = datetime.now().isoformat()
    else:
        data["rekordbox"] = None
        data["rekordbox_fecha"] = None
    
    save_data(data, user_id)


def get_rekordbox(user_id: str) -> pd.DataFrame:
    """
    Obtiene el DataFrame de Rekordbox guardado
    
    Returns:
        DataFrame de Rekordbox o DataFrame vacío
    """
    data = load_data(user_id)
    
    if data.get("rekordbox") is not None:
        return pd.DataFrame(data["rekordbox"])
    
    return pd.DataFrame()


def get_rekordbox_fecha(user_id: str) -> Optional[str]:
    """Obtiene la fecha de carga de Rekordbox"""
    data = load_data(user_id)
    return data.get("rekordbox_fecha")


def clear_rekordbox(user_id: str):
    """Elimina los datos de Rekordbox guardados"""
    data = load_data(user_id)
    data["rekordbox"] = None
    data["rekordbox_fecha"] = None
    save_data(data, user_id)


def save_tiempo_busqueda(tiempo_segundos: float, total_items: int, user_id: str):
    """
    Guarda el tiempo de búsqueda para calcular estimaciones
    
    Args:
        tiempo_segundos: Tiempo que tardó la búsqueda en segundos
        total_items: Total de items comparados
        user_id: ID del usuario
    """
    data = load_data(user_id)
    
    if "tiempos_busqueda" not in data:
        data["tiempos_busqueda"] = []
    
    data["tiempos_busqueda"].append({
        "tiempo": tiempo_segundos,
        "items": total_items,
        "fecha": datetime.now().isoformat()
    })
    
    # Mantener solo los últimos 50 registros
    if len(data["tiempos_busqueda"]) > 50:
        data["tiempos_busqueda"] = data["tiempos_busqueda"][-50:]
    
    save_data(data, user_id)


def get_tiempo_estimado(total_items: int, user_id: str) -> float:
    """
    Calcula tiempo estimado basado en búsquedas anteriores (sin outliers)
    
    Args:
        total_items: Total de items a comparar
        user_id: ID del usuario
    
    Returns:
        Tiempo estimado en segundos
    """
    data = load_data(user_id)
    tiempos = data.get("tiempos_busqueda", [])
    
    if not tiempos:
        return None
    
    # Calcular tiempo por item de cada búsqueda
    tiempos_por_item = []
    for registro in tiempos:
        if registro["items"] > 0:
            tiempo_por_item = registro["tiempo"] / registro["items"]
            tiempos_por_item.append(tiempo_por_item)
    
    if not tiempos_por_item:
        return None
    
    # Eliminar outliers (valores fuera de Q1-1.5*IQR y Q3+1.5*IQR)
    import numpy as np
    if len(tiempos_por_item) > 3:
        q1 = np.percentile(tiempos_por_item, 25)
        q3 = np.percentile(tiempos_por_item, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        tiempos_por_item = [t for t in tiempos_por_item if lower_bound <= t <= upper_bound]
    
    if not tiempos_por_item:
        return None
    
    # Calcular media
    tiempo_promedio = sum(tiempos_por_item) / len(tiempos_por_item)
    
    # Estimar tiempo total
    return tiempo_promedio * total_items


def clear_data(user_id: str):
    """Limpia todos los datos guardados del usuario"""
    save_data(get_default_data(), user_id)


def save_spotify_credentials(client_id: str, client_secret: str, redirect_uri: str, user_id: str):
    """
    Guarda las credenciales de Spotify de forma segura por usuario
    
    Args:
        client_id: Client ID de Spotify
        client_secret: Client Secret de Spotify
        redirect_uri: Redirect URI configurado
        user_id: ID del usuario
    """
    data = load_data(user_id)
    data["spotify_credentials"] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "saved_at": datetime.now().isoformat()
    }
    save_data(data, user_id)


def get_spotify_credentials(user_id: str) -> Optional[Dict]:
    """
    Obtiene las credenciales guardadas de Spotify del usuario
    
    Args:
        user_id: ID del usuario
    
    Returns:
        Diccionario con credenciales o None si no existen
    """
    data = load_data(user_id)
    return data.get("spotify_credentials")


def clear_spotify_credentials(user_id: str):
    """Elimina las credenciales guardadas de Spotify"""
    data = load_data(user_id)
    data["spotify_credentials"] = None
    save_data(data, user_id)

