# Arquitectura Técnica - JC-GPS

## Visión General

JC-GPS es una Cloud Function de Firebase que actúa como pipeline de datos entre la API de Ezzloc (GPS tracking) y Google Drive. Se ejecuta automáticamente cada 60 minutos para mantener un archivo CSV actualizado con los datos de todos los dispositivos GPS.

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Firebase Cloud Functions                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                    run_ezzloc_process (scheduled)                        │  │
│  │                         every 60 minutes                                  │  │
│  │                    timezone: America/Santiago                             │  │
│  │                    max_instances: 1                                       │  │
│  │                    timeout: 300s (5 min)                                  │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                        │
│                                      ▼                                        │
│  ┌─────────────────┐    ┌──────────────────┐    ┌────────────────────────┐    │
│  │  EzzlocAuth     │───▶│  EzzlocClient    │───▶│  DataProcessor         │    │
│  │  (auth.py)      │    │  (client.py)     │    │  (processor.py)        │    │
│  └─────────────────┘    └──────────────────┘    └────────────────────────┘    │
│          │                       │                         │                     │
│          ▼                       ▼                         ▼                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                     generate_local_file()                               │  │
│  │              Ezzloc API → CSV (with timestamps)                         │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                        │
│                                      ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │              GoogleDriveOAuthUploader.upload_with_history()             │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
│                                      │                                        │
│                                      ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                         Google Drive                                    │  │
│  │  ┌────────────────┐    ┌─────────────────────────────────────────────┐ │  │
│  │  │ ROOT_FOLDER    │    │         ROOT_FOLDER/historico/              │ │  │
│  │  │ (actual.csv)   │    │    (yyyy-mm-dd_hh-mm-ss_devices.csv)        │ │  │
│  │  └────────────────┘    └─────────────────────────────────────────────┘ │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Módulos

### 1. `src/ezzloc/` - Módulo de Extracción Ezzloc

#### `config.py`
Configuración central del pipeline de Ezzloc.
- Carga variables de entorno con `python-dotenv`
- Define URLs base de API
- Configura credenciales y parámetros de paginación

#### `auth.py`
Módulo de autenticación con Ezzloc API.
- Maneja login y obtención de token
- Mantiene sesión autenticada

#### `client.py`
Cliente HTTP para comunicación con API de Ezzloc.
- `get_org_groups()` - Obtiene grupos organizacionales
- `get_group_details_bulk()` - Detalle de múltiples grupos
- `get_device_details_bulk()` - Detalle de múltiples dispositivos
- Manejo de tokens de autenticación en headers

#### `processor.py`
Procesamiento de datos crudos a DataFrame de pandas.
- `process_data_to_df()` - Transforma respuestas API a DataFrame
- `add_process_timestamps()` - Agrega marcas de tiempo del proceso
- `export_to_csv()` - Exporta a CSV con naming convention

#### `main.py`
Orquestador principal del pipeline Ezzloc.
```
Flow:
1. Autenticarse en Ezzloc
2. Obtener org_groups (jerarquía)
3. Para cada grupo → obtener devices
4. Merge de datasets
5. Exportar a CSV
```

### 2. `src/gdrive/` - Módulo de Google Drive

#### `oauth_uploader.py`
Clase principal para subir archivos a Google Drive usando OAuth 2.0.

**Propiedades:**
- `credentials` - OAuth credentials con refresh token automático
- `service` - Servicio de Google Drive API v3

**Métodos principales:**

| Método | Descripción |
|--------|-------------|
| `upload_local_file_to_drive()` | Sube archivo a carpeta específica |
| `get_or_create_folder()` | Obtiene o crea carpeta por nombre |
| `check_if_file_exists_today()` | Verifica si existe archivo en ventana horaria |
| `upload_or_update_file()` | Sube nuevo archivo o actualiza existente |
| `upload_with_history()` | Sube a raíz + carpeta historico |

**Configuración OAuth:**
- Scope: `https://www.googleapis.com/auth/drive.file`
- Token URI: `https://oauth2.googleapis.com/token`
- Refresh token flow automático

#### `uploader.py`
Uploader básico (alternativo, no usa OAuth).

### 3. `src/shared/` - Utilidades Compartidas

#### `config_utils.py`
Funciones utilitarias de configuración compartidas entre módulos.

## Flujo de Datos Detallado

### Paso 1: Verificación Previa
```
run_ezzloc_process()
  ├─ Check OAuth credentials exist
  └─ check_if_file_exists_today()
       ├─ Get/create "historico" folder
       └─ Query files with pattern YYYY-MM-DD_HH-MM-SS
```

### Paso 2: Extracción Ezzloc
```
generate_local_file()
  ├─ EzzlocAuth.login()
  │    └─ POST /login → {token}
  │
  ├─ get_org_groups()
  │    └─ GET /api/org_groups → [{org_group_id, ...}]
  │
  ├─ get_group_details_bulk(group_ids[])
  │    └─ GET /api/groups/{id} → [{group_id, device_id, ...}]
  │
  ├─ get_device_details_bulk(device_ids[])
  │    └─ GET /api/devices/{id} → [{device data}]
  │
  └─ merge(org_groups, groups, devices)
       └─ DataFrame: org_groups + groups + devices
```

### Paso 3: Procesamiento
```
DataProcessor
  ├─ process_data_to_df(raw_data)
  │    └─ Normaliza campos, maneja nulos
  │
  ├─ add_process_timestamps(df, process_start_time)
  │    └─ process_date, process_timestamp
  │
  └─ export_to_csv(df, PREFIX, timestamp)
       └─ ezzloc_devices_YYYY-MM-DD_HH-MM-SS.csv
```

### Paso 4: Subida a Google Drive
```
upload_with_history(csv_path)
  ├─ 1. upload_or_update_file(ezzloc_devices.csv)
  │    ├─ Search file in root folder
  │    └─ Create new OR update existing
  │
  └─ 2. Create/upload to historico folder
       ├─ get_or_create_folder("historico")
       └─ files().create() with filename
```

## Naming Convention

Archivos CSV generados:
```
ezzloc_devices_YYYY-MM-DD_HH-MM-SS.csv
  │          │        │    │   │   │
  │          │        │    │   │   └─ Segundos
  │          │        │    │   └─── Minutos
  │          │        │    └─────── Hora
  │          │        └───────────── Fecha
  │          └─────────────────────── Separador
  └───────────────────────────────── Prefijo configurable
```

## Dependencias Externas

### APIs/Servicios

| Servicio | Uso |
|----------|-----|
| **Ezzloc API** | Extracción de datos GPS |
| **Google Drive API v3** | Almacenamiento de archivos |
| **Firebase Cloud Functions** | Ambiente de ejecución serverless |

### Librerías Python

| Librería | Propósito |
|----------|----------|
| `firebase_functions` | Cloud Functions for Firebase |
| `requests` | HTTP client para Ezzloc API |
| `pandas` | Procesamiento de datos |
| `google-api-python-client` | Google Drive API |
| `google-auth-oauthlib` | OAuth 2.0 flow |
| `python-dotenv` | Carga de variables de entorno |

## Configuración de Entorno

### Desarrollo Local
```bash
# .env en functions/
EZZLOC_USERNAME=tu_usuario
EZZLOC_PASSWORD=tu_password
EZZLOC_BASE_URL=https://www.ezzloc.net/prod-api

GDRIVE_CLIENT_ID=xxx.apps.googleusercontent.com
GDRIVE_CLIENT_SECRET=xxx
GDRIVE_REFRESH_TOKEN=xxx
GDRIVE_FOLDER_ID=carpeta_root_id

GDRIVE_START_HOUR=8
TIMEZONE=America/Santiago
```

### Firebase Production
```bash
# Configurar via Firebase CLI
firebase functions:config:set ezzloc.username=tu_usuario
firebase functions:config:set gdrive.client_id=xxx
# etc.
```

## Consideraciones de Rendimiento

- **Max instances**: 1 (previene ejecuciones concurrentes)
- **Timeout**: 300 segundos (5 minutos máx)
- **Schedule**: Cada 60 minutos
- **Filtro de fecha**: Ventana horaria configurable (start_hour) para evitar duplicados en días laborables

## Modelo de Datos

### CSV Output

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `org_group_id` | string | ID del grupo organizacional |
| `group_id` | string | ID del grupo |
| `device_id` | string | ID del dispositivo |
| `vehicle_id` | string | ID del vehículo asociado |
| `lat`, `lng` | float | Coordenadas GPS |
| `speed` | float | Velocidad actual |
| `timestamp` | datetime | Última actualización |
| `process_date` | date | Fecha de ejecución del pipeline |
| `process_timestamp` | datetime | Timestamp exacto del proceso |
