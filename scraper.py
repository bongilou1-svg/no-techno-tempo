"""
Módulo para hacer scraping de discosparadiso.com
Extrae artistas, títulos y precios de los discos según filtros seleccionados
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import urlencode
import time
import re


def _extract_releases_from_page(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """
    Extrae los releases de una página parseada
    
    Args:
        soup: BeautifulSoup object con el HTML parseado
    
    Returns:
        Lista de diccionarios con 'artista', 'titulo' y 'precio'
    """
    resultados = []
    
    # Buscar primero con la estructura nueva: div.tile (sin releaseItem)
    releases = soup.find_all('div', class_='tile')
    
    # Si no encuentra, buscar con la estructura antigua
    if not releases:
        releases = soup.find_all('div', class_='tile releaseItem')
    
    for release in releases:
        try:
            # Buscar el contenedor artistsAndTitle
            artists_title_container = release.find('div', class_='artistsAndTitle')
            
            if artists_title_container:
                # Extraer artista - buscar p.artistName > a.singleArtistName
                artist_name_elem = artists_title_container.find('p', class_='artistName')
                if artist_name_elem:
                    artist_link = artist_name_elem.find('a', class_='singleArtistName')
                    if artist_link:
                        artista = artist_link.get_text(strip=True)
                    else:
                        artista = artist_name_elem.get_text(strip=True)
                else:
                    # Fallback: buscar cualquier p con clase artists
                    artist_elem = release.find('p', class_='artists') or release.find('p', class_=lambda x: x and 'artist' in str(x).lower())
                    if artist_elem:
                        artist_span = artist_elem.find('span')
                        if artist_span:
                            artista = artist_span.get_text(strip=True)
                        else:
                            artista = artist_elem.get_text(strip=True)
                    else:
                        artista = "N/A"
                
                # Extraer título - está en un <a> > <p> > <span> > <span>
                title_link = artists_title_container.find('a', href=lambda href: href and '/release/' in str(href))
                if title_link:
                    title_p = title_link.find('p')
                    if title_p:
                        # Buscar el span más interno que contiene el texto
                        title_spans = title_p.find_all('span')
                        if title_spans:
                            # El título suele estar en el primer span que tiene texto
                            for span in title_spans:
                                text = span.get_text(strip=True)
                                if text and text != '…' and len(text) > 1:
                                    titulo = text
                                    break
                            else:
                                titulo = title_p.get_text(strip=True)
                        else:
                            titulo = title_p.get_text(strip=True)
                    else:
                        titulo = title_link.get_text(strip=True)
                else:
                    # Fallback: buscar p.title
                    title_elem = release.find('p', class_='title')
                    if title_elem:
                        title_span = title_elem.find('span')
                        if title_span:
                            titulo = title_span.get_text(strip=True)
                        else:
                            titulo = title_elem.get_text(strip=True)
                    else:
                        titulo = "N/A"
            else:
                # Estructura antigua: buscar p.artists y p.title directamente
                artist_elem = release.find('p', class_='artists')
                if artist_elem:
                    artist_span = artist_elem.find('span')
                    if artist_span:
                        artista = artist_span.get_text(strip=True)
                    else:
                        artista = artist_elem.get_text(strip=True)
                else:
                    artista = "N/A"
                
                title_elem = release.find('p', class_='title')
                if title_elem:
                    title_span = title_elem.find('span')
                    if title_span:
                        titulo = title_span.get_text(strip=True)
                    else:
                        titulo = title_elem.get_text(strip=True)
                else:
                    titulo = "N/A"
            
            # Extraer precio - buscar span.price dentro de button.addToBasket o directamente
            price_elem = release.find('span', class_='price')
            if not price_elem:
                price_elem = release.find('p', class_='price')
            precio = price_elem.get_text(strip=True) if price_elem else "N/A"
            
            # Solo agregar si tiene artista y título válidos
            if artista != "N/A" and titulo != "N/A" and artista and titulo:
                resultados.append({
                    'artista': artista,
                    'titulo': titulo,
                    'precio': precio
                })
        except Exception as e:
            print(f"Error procesando un release: {e}")
            continue
    
    return resultados


def _get_total_pages(soup: BeautifulSoup, driver) -> int:
    """
    Detecta el número total de páginas desde el HTML o el DOM
    Busca específicamente el elemento con clase 'pageCount' que contiene "Page X of Y"
    
    Args:
        soup: BeautifulSoup object con el HTML parseado
        driver: Selenium WebDriver para buscar en el DOM
    
    Returns:
        Número total de páginas, o 1 si no se puede detectar
    """
    try:
        # Primero intentar con Selenium buscando el elemento pageCount
        try:
            page_count_elements = driver.find_elements(By.CSS_SELECTOR, "p.pageCount, .pageCount")
            for elem in page_count_elements:
                text = elem.text
                # Buscar patrón "Page X of Y"
                match = re.search(r'Page\s+\d+\s+of\s+(\d+)', text, re.IGNORECASE)
                if match:
                    return int(match.group(1))
        except Exception as e:
            print(f"Error buscando pageCount con Selenium: {e}")
        
        # Buscar en el HTML parseado el elemento con clase pageCount
        page_count_elem = soup.find('p', class_='pageCount')
        if not page_count_elem:
            page_count_elem = soup.find(class_='pageCount')
        
        if page_count_elem:
            text = page_count_elem.get_text()
            # Buscar patrón "Page X of Y"
            match = re.search(r'Page\s+\d+\s+of\s+(\d+)', text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        # Buscar en cualquier elemento que contenga "Page" y "of"
        try:
            page_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Page') and contains(text(), 'of')]")
            for elem in page_elements:
                text = elem.text
                match = re.search(r'Page\s+\d+\s+of\s+(\d+)', text, re.IGNORECASE)
                if match:
                    return int(match.group(1))
        except:
            pass
        
        # Buscar en el HTML parseado cualquier texto con "Page X of Y"
        all_texts = soup.find_all(text=True)
        for text in all_texts:
            if 'Page' in text and 'of' in text:
                match = re.search(r'Page\s+\d+\s+of\s+(\d+)', text, re.IGNORECASE)
                if match:
                    return int(match.group(1))
        
        # Como último recurso, buscar enlaces de paginación
        page_links = soup.find_all('a', href=lambda href: href and 'page=' in str(href))
        if page_links:
            max_page = 1
            for link in page_links:
                href = link.get('href', '')
                match = re.search(r'page=(\d+)', str(href))
                if match:
                    page_num = int(match.group(1))
                    max_page = max(max_page, page_num)
            if max_page > 1:
                return max_page
        
    except Exception as e:
        print(f"Error detectando número de páginas: {e}")
    
    return 1  # Por defecto, solo una página


def scrape_discos_paradiso(styles: List[str] = None) -> List[Dict[str, str]]:
    """
    Hace scraping de discosparadiso.com con los filtros especificados
    Recorre todas las páginas disponibles
    
    Args:
        styles: Lista de estilos a filtrar (ej: ['Downtempo', 'Ambient'])
    
    Returns:
        Lista de diccionarios con 'artista', 'titulo' y 'precio'
    """
    base_url = "https://www.discosparadiso.com/catalogue"
    
    # Construir parámetros base de la URL
    param_list = [('genres', 'Electronic'), ('formats', 'Vinyl')]
    if styles:
        for style in styles:
            param_list.append(('styles', style))
    
    # Configurar Selenium con Chrome
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Ejecutar sin abrir ventana
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = None
    todos_resultados = []
    
    try:
        # Inicializar el driver con webdriver-manager
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Primero cargar la página 1 para detectar el total de páginas
        query_string = urlencode(param_list)
        url_pagina1 = f"{base_url}?{query_string}"
        print(f"Scrapeando página 1: {url_pagina1}")
        
        driver.get(url_pagina1)
        
        # Esperar a que se cargue el contenido
        wait = WebDriverWait(driver, 15)
        try:
            # Buscar div.tile o div.tile.releaseItem
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.tile, .tile.releaseItem, .releaseItem")))
        except:
            # Si no encuentra, esperar un tiempo fijo para que cargue
            time.sleep(5)
        
        # Obtener HTML de la primera página
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extraer releases de la página 1
        resultados_pag1 = _extract_releases_from_page(soup)
        todos_resultados.extend(resultados_pag1)
        print(f"Página 1: {len(resultados_pag1)} discos encontrados")
        
        # Detectar número total de páginas
        total_pages = _get_total_pages(soup, driver)
        print(f"Total de páginas detectadas: {total_pages}")
        
        # Recorrer las páginas restantes (si hay más de 1)
        if total_pages > 1:
            for page_num in range(2, total_pages + 1):
                # Construir URL con parámetro page
                page_params = param_list + [('page', str(page_num))]
                query_string = urlencode(page_params)
                url = f"{base_url}?{query_string}"
                print(f"Scrapeando página {page_num}/{total_pages}: {url}")
                
                driver.get(url)
                
                # Esperar a que se cargue el contenido
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.tile, .tile.releaseItem, .releaseItem")))
                except:
                    time.sleep(3)
                
                # Obtener HTML de la página
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extraer releases
                resultados_pag = _extract_releases_from_page(soup)
                todos_resultados.extend(resultados_pag)
                print(f"Página {page_num}: {len(resultados_pag)} discos encontrados")
                
                # Pequeña pausa entre páginas para no sobrecargar el servidor
                time.sleep(1)
        
        print(f"\nTotal de discos encontrados: {len(todos_resultados)}")
        return todos_resultados
        
    except Exception as e:
        print(f"Error inesperado: {e}")
        return todos_resultados
    finally:
        if driver:
            driver.quit()


def get_available_styles() -> List[str]:
    """
    Retorna una lista de estilos disponibles para Electronic
    (Lista estática basada en los estilos comunes del sitio)
    """
    return [
        'Downtempo',
        'Ambient',
        'Experimental',
        'Techno',
        'Dub',
        'House',
        'Leftfield',
        'Electro',
        'Abstract',
        'IDM',
        'Disco',
        'Balearic',
        'Breaks',
        'Breakbeat',
        'Trance',
        'Tech House',
        'Tribal',
        'Trip Hop',
        'Deep House',
        'Synth-pop',
        'Industrial',
        'Jungle',
        'Drum n Bass',
        'Dub Techno',
        'Acid',
        'Acid House',
        'Future Jazz',
        'Instrumental',
        'Fusion',
        'EBM',
        'Minimal',
        'Jazzy Hip-Hop',
        'Krautrock',
        'Funk'
    ]

