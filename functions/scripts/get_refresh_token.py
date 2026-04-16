#!/usr/bin/env python3
"""
Script para obtener Refresh Token de OAuth 2.0 para Google Drive

PASOS:
1. Ve a https://console.cloud.google.com/ → APIs → Credenciales
2. Crea un "ID de cliente OAuth 2.0" tipo "Aplicación de escritorio"
3. Descarga el JSON y renómbralo a "client_secret.json"
4. Coloca client_secret.json en el mismo directorio que este script
5. Ejecuta: python get_refresh_token.py
6. Autoriza con tu cuenta Google cuando se abra el navegador
7. Copia el refresh_token mostrado y agrégalo a tu .env
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import json

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CLIENT_SECRET_FILE = 'client_secret.json'
TOKEN_PICKLE = 'token.pickle'


def main():
    # Verificar que existe el archivo de credenciales
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"ERROR: No se encontró '{CLIENT_SECRET_FILE}'")
        print("\nPASOS:")
        print("1. Ve a https://console.cloud.google.com/")
        print("2. APIs y servicios → Credenciales")
        print("3. Crear credenciales → ID de cliente OAuth 2.0")
        print("4. Tipo: Aplicación de escritorio")
        print("5. Descarga el JSON y renómbralo a 'client_secret.json'")
        print("6. Colócalo en el mismo directorio que este script")
        print("7. Ejecuta este script de nuevo")
        return

    creds = None
    
    # Cargar credenciales guardadas
    if os.path.exists(TOKEN_PICKLE):
        print("Cargando credenciales guardadas...")
        with open(TOKEN_PICKLE, 'rb') as token:
            creds = pickle.load(token)
    
    # Refrescar o crear nuevas credenciales
    if creds and creds.valid:
        print("Las credenciales ya son válidas.")
    elif creds and creds.expired and creds.refresh_token:
        print("Refrescando credenciales expiradas...")
        creds.refresh(Request())
    else:
        print("Iniciando flujo OAuth...")
        print("Se abrirá una ventana del navegador para autorizar.")
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
    
    # Guardar credenciales
    with open(TOKEN_PICKLE, 'wb') as token:
        pickle.dump(creds, token)
    
    # Extraer Client ID del archivo JSON
    with open(CLIENT_SECRET_FILE, 'r') as f:
        client_config = json.load(f)
        installed = client_config.get('installed', {})
        client_id = installed.get('client_id', 'NO_ENCONTRADO')
        client_secret = installed.get('client_secret', 'NO_ENCONTRADO')
    
    print("\n" + "="*60)
    print("CREDENCIALES OBTENIDAS")
    print("="*60)
    print(f"\nCopia estos valores a tu archivo .env:\n")
    print(f"GDRIVE_CLIENT_ID={client_id}")
    print(f"GDRIVE_CLIENT_SECRET={client_secret}")
    print(f"GDRIVE_REFRESH_TOKEN={creds.refresh_token}")
    print("\n" + "="*60)


if __name__ == '__main__':
    main()
