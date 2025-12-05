# NoTechnoTempo ⏱️🎧

Tu biblioteca musical definitiva - Una aplicación moderna para gestionar toda tu música en un solo lugar.

## 🎵 Características

NoTechnoTempo es una aplicación web multi-pestañas que te permite:

### 🎵 Pestaña 1: Buscar Discos
- **Scraping de Discos Paradiso**: Busca discos de vinilo del género Electronic
- **Filtrado por estilos**: Selecciona uno o más estilos musicales
- **Paginación automática**: Recorre todas las páginas disponibles
- **Exportación a CSV**: Descarga tus resultados

### 🎧 Pestaña 2: Spotify
- **Conexión OAuth**: Conecta de forma segura con tu cuenta de Spotify
- **Playlists**: Visualiza todas tus playlists y sus canciones
- **Canciones Guardadas**: Lista todas tus canciones favoritas
- **Exportación**: Descarga tus listas en formato CSV

### 💿 Pestaña 3: Música Local
- **Escaneo de carpetas**: Selecciona carpetas para escanear música
- **Múltiples formatos**: Soporta MP3, FLAC, WAV, M4A, OGG y más
- **Extracción de metadatos**: Artista, título, álbum, duración
- **Listado completo**: Genera una lista con toda tu música local

## 🔐 Autenticación

NoTechnoTempo utiliza **autenticación con Google OAuth** para:
- Aislar los datos de cada usuario
- Proteger información privada (credenciales de Spotify, listas de Rekordbox)
- Permitir acceso seguro desde cualquier dispositivo

**Al iniciar la aplicación, se te pedirá iniciar sesión con tu cuenta de Google.**

## 🚀 Instalación Local

1. Clona o descarga este proyecto

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Configura las credenciales de Google OAuth (opcional para desarrollo local):
   - Crea un proyecto en [Google Cloud Console](https://console.cloud.google.com/)
   - Habilita Google+ API
   - Crea credenciales OAuth 2.0
   - Configura las variables de entorno o usa Streamlit Secrets

## ▶️ Uso Local

1. Ejecuta la aplicación:
```bash
streamlit run app.py
```

2. La aplicación se abrirá automáticamente en tu navegador (normalmente en `http://localhost:8501`)

3. Inicia sesión con tu cuenta de Google

4. Navega entre las pestañas para usar las diferentes funcionalidades

## ☁️ Despliegue en Streamlit Cloud

### Paso 1: Subir a GitHub

1. Crea un nuevo repositorio en GitHub (público o privado)

2. Inicializa git en tu proyecto local:
```bash
git init
git add .
git commit -m "Initial commit: NoTechnoTempo"
```

3. Conecta con GitHub y sube el código:
```bash
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git branch -M main
git push -u origin main
```

### Paso 2: Desplegar en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)

2. Inicia sesión con tu cuenta de GitHub

3. Haz clic en "New app"

4. Selecciona tu repositorio y branch

5. Configura:
   - **Main file path**: `app.py`
   - **Python version**: 3.8 o superior

6. **Configurar Secrets** (importante para Google OAuth):
   - Ve a "Settings" > "Secrets"
   - Añade tus credenciales de Google OAuth:
   ```toml
   [google_oauth]
   client_id = "tu_client_id"
   client_secret = "tu_client_secret"
   ```

7. Haz clic en "Deploy"

8. ¡Tu app estará disponible en `https://TU_APP.streamlit.app`!

### Configuración de Google OAuth para Streamlit Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto o selecciona uno existente
3. Habilita "Google+ API"
4. Ve a "Credenciales" > "Crear credenciales" > "ID de cliente OAuth 2.0"
5. Tipo de aplicación: "Aplicación web"
6. **URIs de redirección autorizados**: Añade `https://TU_APP.streamlit.app`
7. Copia el Client ID y Client Secret
8. Añádelos como secrets en Streamlit Cloud

## 📋 Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Chrome/Chromium (para el scraping con Selenium)
- Cuenta de Spotify (opcional, para la pestaña de Spotify)

## 🔧 Configuración

### Spotify (Opcional)

Para usar la funcionalidad de Spotify:

1. Ve a [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Crea una nueva app
3. Copia el **Client ID** y **Client Secret**
4. Añade `http://localhost:8501` como Redirect URI en la configuración de tu app
5. Introduce las credenciales en la pestaña de Spotify

## 📁 Estructura del Proyecto

```
dj-library-pro/
├── app.py                 # Aplicación principal con pestañas
├── auth_module.py        # Módulo de autenticación con Google
├── data_storage.py       # Almacenamiento de datos por usuario
├── scraper.py            # Módulo de scraping de Discos Paradiso
├── rekordbox_module.py   # Módulo de procesamiento de Rekordbox
├── spotify_module.py     # Módulo de integración con Spotify
├── local_music.py        # Módulo de escaneo de música local
├── utils.py              # Utilidades (estilos, logo)
├── requirements.txt      # Dependencias
├── .streamlit/           # Configuración de Streamlit
│   └── config.toml       # Configuración de tema y servidor
├── .gitignore           # Archivos a excluir de Git
└── README.md            # Este archivo
```

**Nota**: Los datos de usuarios se guardan en `data/users/` y NO se suben a GitHub por seguridad.

## 🎨 Diseño

NoTechnoTempo tiene un diseño moderno y "vacilón" con:
- Gradientes vibrantes
- Animaciones sutiles
- Interfaz limpia y funcional
- Logo personalizado estilo "reloj-jog"

## 🎵 Estilos Disponibles (Discos Paradiso)

La aplicación permite filtrar por los siguientes estilos de Electronic:
Downtempo, Ambient, Experimental, Techno, Dub, House, Leftfield, Electro, Abstract, IDM, Disco, Balearic, Breaks, Breakbeat, Trance, Tech House, Tribal, Trip Hop, Deep House, Synth-pop, Industrial, Jungle, Drum n Bass, Dub Techno, Acid, Acid House, Future Jazz, Instrumental, Fusion, EBM, Minimal, Jazzy Hip-Hop, Krautrock, Funk

## 💿 Formatos de Audio Soportados

MP3, FLAC, WAV, M4A, AAC, OGG, OGA, OPUS, WMA, AIFF, MP4, y más...

## 🔒 Seguridad y Privacidad

- **Datos aislados por usuario**: Cada usuario tiene su propia carpeta de datos
- **Autenticación requerida**: No se puede acceder sin iniciar sesión con Google
- **Credenciales protegidas**: Las credenciales de Spotify se almacenan de forma segura por usuario
- **Datos locales**: Los datos se guardan localmente en `data/users/{user_id}/`

## ⚠️ Notas

- El scraping siempre filtra por género "Electronic" y formato "Vinyl"
- Los resultados dependen de la disponibilidad en el sitio web
- Respeta los términos de uso del sitio web
- Para Spotify, necesitas permisos de lectura de tu cuenta
- **Selenium en la nube**: Streamlit Cloud puede tener limitaciones con Selenium. Puede requerir configuración adicional

## 🛠️ Tecnologías Utilizadas

- **Streamlit**: Interfaz web
- **google-auth-st**: Autenticación con Google OAuth
- **BeautifulSoup4**: Parsing de HTML
- **Selenium**: Scraping de sitios con JavaScript
- **Spotipy**: Integración con Spotify API
- **Mutagen**: Extracción de metadatos de audio
- **Pandas**: Manejo de datos
- **Requests**: Peticiones HTTP
- **NumPy**: Cálculos estadísticos

## 📝 Licencia

Este proyecto es para uso personal/educacional.

## 🎉 ¡Disfruta de NoTechnoTempo!

Tu biblioteca musical definitiva en un solo lugar.
