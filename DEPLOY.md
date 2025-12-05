# Guía de Despliegue - NoTechnoTempo

## 📋 Checklist Pre-Despliegue

- [x] Autenticación con Google OAuth implementada
- [x] Aislamiento de datos por usuario
- [x] .gitignore configurado
- [x] requirements.txt actualizado
- [x] README.md actualizado

## 🚀 Pasos para Publicar

### 1. Preparar Repositorio Local

```bash
# Verificar que estás en el directorio del proyecto
cd dj-library-pro

# Inicializar git (si no está inicializado)
git init

# Verificar que .gitignore está presente
ls -la .gitignore

# Añadir todos los archivos (excepto los excluidos en .gitignore)
git add .

# Hacer commit inicial
git commit -m "Initial commit: NoTechnoTempo con autenticación"
```

### 2. Crear Repositorio en GitHub

1. Ve a [github.com](https://github.com) e inicia sesión
2. Haz clic en "New repository" (botón verde)
3. Configura:
   - **Nombre**: `no-techno-tempo` (o el que prefieras)
   - **Visibilidad**: Público o Privado (según prefieras)
   - **NO** marques "Initialize with README" (ya tenemos uno)
4. Haz clic en "Create repository"

### 3. Conectar y Subir Código

```bash
# Conectar repositorio local con GitHub
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git

# Cambiar a branch main
git branch -M main

# Subir código
git push -u origin main
```

### 4. Desplegar en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io)
2. Inicia sesión con tu cuenta de GitHub
3. Haz clic en "New app"
4. Configura:
   - **Repository**: Selecciona tu repositorio
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **Python version**: 3.8 o superior
5. Haz clic en "Deploy"

### 5. Configurar Google OAuth (Opcional pero Recomendado)

#### 5.1. Crear Proyecto en Google Cloud

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita "Google+ API" o "Google Identity API"
4. Ve a "APIs & Services" > "Credentials"
5. Haz clic en "Create Credentials" > "OAuth client ID"
6. Tipo: "Web application"
7. **Authorized redirect URIs**: Añade `https://TU_APP.streamlit.app`
8. Copia el **Client ID** y **Client Secret**

#### 5.2. Configurar Secrets en Streamlit Cloud

1. En Streamlit Cloud, ve a tu app
2. Haz clic en "Settings" (⚙️)
3. Ve a la pestaña "Secrets"
4. Añade:

```toml
[google_oauth]
client_id = "tu_client_id_aqui"
client_secret = "tu_client_secret_aqui"
```

5. Guarda los cambios

### 6. Verificar Despliegue

1. Tu app estará disponible en: `https://TU_APP.streamlit.app`
2. Comparte esta URL con tus colegas
3. Cada usuario necesitará iniciar sesión con Google

## 🔒 Seguridad

- ✅ Los datos de usuarios están aislados en `data/users/{user_id}/`
- ✅ El archivo `.gitignore` excluye todos los datos de usuarios
- ✅ Las credenciales de Google OAuth se guardan como secrets (no en el código)
- ✅ Cada usuario solo puede acceder a sus propios datos

## 📝 Notas Importantes

1. **Selenium en la nube**: Streamlit Cloud puede tener limitaciones con Selenium. Si el scraping no funciona, considera:
   - Usar Playwright en lugar de Selenium
   - O ejecutar el scraping localmente y subir los datos

2. **Datos persistentes**: Los datos se guardan en el servidor de Streamlit Cloud. Si eliminas la app, se perderán los datos.

3. **Límites de Streamlit Cloud**: 
   - Apps gratuitas tienen límites de CPU y memoria
   - El scraping puede ser lento en la nube

## 🆘 Solución de Problemas

### Error: "Module not found"
- Verifica que `requirements.txt` tiene todas las dependencias
- Streamlit Cloud reinstalará las dependencias automáticamente

### Error: "Google OAuth not configured"
- Configura los secrets en Streamlit Cloud
- O usa el modo desarrollo (sin OAuth) para testing

### El scraping no funciona
- Streamlit Cloud puede tener limitaciones con Selenium
- Considera ejecutar scraping localmente y subir los datos

## 📞 Compartir con Colegas

Una vez desplegado, comparte:
- URL de la app: `https://TU_APP.streamlit.app`
- Instrucciones: "Inicia sesión con tu cuenta de Google para acceder"

¡Listo! Tu app está en la nube y lista para compartir 🚀

