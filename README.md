# JC-GPS - Ezzloc Data Pipeline

Cloud Function de Firebase que extrae datos de dispositivos GPS desde la API de Ezzloc y los sincroniza con Google Drive.

## Estructura del Proyecto

```
jc-gps/
├── functions/                 # Cloud Functions de Firebase
│   ├── main.py              # Entry point de Firebase
│   ├── main_ezzloc.py        # Función principal programada
│   ├── requirements.txt     # Dependencias Python
│   ├── scripts/             # Scripts auxiliares
│   │   └── get_refresh_token.py
│   └── src/
│       ├── ezzloc/          # Módulo de extracción Ezzloc
│       │   ├── auth.py      # Autenticación API
│       │   ├── client.py    # Cliente API
│       │   ├── config.py    # Configuración
│       │   ├── main.py      # Orquestador principal
│       │   └── processor.py # Procesamiento de datos
│       ├── gdrive/          # Módulo de Google Drive
│       │   ├── oauth_uploader.py  # Subida con OAuth
│       │   └── uploader.py       # Subida básica
│       └── shared/          # Utilidades compartidas
│           └── config_utils.py
├── firebase-commands.md      # Comandos Firebase
├── .firebaserc              # Configuración proyecto Firebase
└── firebase.json            # Configuración Firebase
```

## Requisitos

- Python 3.10+
- Firebase CLI
- Node.js (para Firebase CLI)
- Cuenta de Firebase con Cloud Functions habilitada
- Credenciales de Google Drive API

### Dependencias Python

```
firebase_functions~=0.5.0
requests
pandas
python-dotenv
google-api-python-client
google-auth
google-auth-oauthlib
pytz
```

## Variables de Entorno

### Ezzloc API

| Variable | Descripción | Valor por defecto |
|----------|-------------|------------------|
| `EZZLOC_USERNAME` | Usuario Ezzloc | - |
| `EZZLOC_PASSWORD` | Contraseña Ezzloc | - |
| `EZZLOC_BASE_URL` | URL base API | `https://www.ezzloc.net/prod-api` |
| `EZZLOC_PREFIX` | Prefijo archivos | `ezzloc_devices` |

### Google Drive

| Variable | Descripción |
|----------|-------------|
| `GDRIVE_CLIENT_ID` | Client ID de Google Cloud |
| `GDRIVE_CLIENT_SECRET` | Client Secret de Google Cloud |
| `GDRIVE_REFRESH_TOKEN` | Refresh Token OAuth |
| `GDRIVE_FOLDER_ID` | ID de carpeta destino en Drive |

### Configuración General

| Variable | Descripción | Valor por defecto |
|----------|-------------|------------------|
| `GDRIVE_START_HOUR` | Hora inicio ventana | `8` |
| `TIMEZONE` | Zona horaria | `America/Santiago` |

## Comandos Firebase

### Emulación Local

```bash
# Iniciar emulador de functions
firebase emulators:start --only functions

# Emular función específica
firebase emulators:start --only functions:run_ezzloc_process
```

### Despliegue

```bash
# Desplegar todas las funciones
firebase deploy --only functions

# Desplegar función específica
firebase deploy --only functions:run_ezzloc_process
```

## Flujo de Ejecución

La función `run_ezzloc_process` se ejecuta cada **60 minutos**:

```
┌──────────────────────────────────────────────────────────────────────┐
│                    run_ezzloc_process                                 │
├──────────────────────────────────────────────────────────────────────┤
│  1. Validar variables de entorno (OAuth GDrive)                       │
│  2. Verificar si ya existe archivo hoy (evitar duplicados)           │
│  3. Autenticarse en Ezzloc API                                       │
│  4. Obtener org_groups → groups → devices                             │
│  5. Procesar y fusionar datos en DataFrame                           │
│  6. Exportar a CSV con timestamp                                     │
│  7. Subir a Google Drive:                                             │
│     - Archivo raíz (actualizado diariamente)                         │
│     - Carpeta "historico" (cada ejecución)                           │
└──────────────────────────────────────────────────────────────────────┘
```

## Instalación Local para Desarrollo

```bash
# 1. Clonar repositorio
git clone https://github.com/gibam/jc-gps.git
cd jc-gps

# 2. Instalar Firebase CLI
npm install -g firebase-tools

# 3. Instalar dependencias Python
cd functions
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con credenciales

# 5. Iniciar emulador
firebase emulators:start --only functions
```

## Proyecto Firebase

- **ID de proyecto**: `jc-gps-fb`
- **Región por defecto**: `us-central1`
- **Zona horaria**: America/Santiago (UTC-4)
