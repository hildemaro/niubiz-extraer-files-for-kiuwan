import requests
import re
import os
import shutil
import tkinter as tk
from tkinter import simpledialog
import config  # Importar credenciales desde config.py
from tqdm import tqdm  # Barra de progreso

# Crear ventana oculta para el cuadro de diálogo
root = tk.Tk()
root.withdraw()  # Oculta la ventana principal

# Pedir la URL del commit al usuario
COMMIT_URL = simpledialog.askstring(
    "Bitbucket - Ingresar URL",
    "Por favor, ingrese la URL del commit:",
    parent=root
)

# Validar la URL ingresada
if not COMMIT_URL:
    print("❌ No ingresaste ninguna URL. Saliendo...")
    exit(1)

# Expresión regular para extraer workspace, repo_slug y commit_id
match = re.search(r"https://bitbucket.org/([^/]+)/([^/]+)/commits/([a-f0-9]+)", COMMIT_URL)

if not match:
    print("❌ Error: La URL del commit no es válida.")
    exit(1)

WORKSPACE, REPO_SLUG, COMMIT_ID = match.groups()
COMMIT_ID_CORTO = COMMIT_ID[:7]  # Tomar solo los primeros 7 caracteres

# Configuración de autenticación desde config.py
USERNAME = config.USERNAME
APP_PASSWORD = config.APP_PASSWORD

# URL de la API de Bitbucket
API_URL = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{REPO_SLUG}/diffstat/{COMMIT_ID}"

# Autenticación usando usuario y App Password
response = requests.get(API_URL, auth=(USERNAME, APP_PASSWORD))

# Procesar la respuesta
if response.status_code == 200:
    data = response.json()

    archivos_modificados = []
    archivos_agregados = []
    archivos_eliminados = []

    for item in data.get("values", []):
        status = item.get("status")
        new_data = item.get("new")
        old_data = item.get("old")

        new_path = new_data.get("path") if new_data else None
        old_path = old_data.get("path") if old_data else None

        if status == "modified" and new_path:
            archivos_modificados.append(new_path)
        elif status == "added" and new_path:
            archivos_agregados.append(new_path)
        elif status == "removed" and old_path:
            archivos_eliminados.append(old_path)

    if not archivos_modificados and not archivos_agregados and not archivos_eliminados:
        print("📌 No se encontraron cambios en el commit.")
        exit(0)

    # Ruta del repositorio y de salida
    repo_path = os.path.abspath(REPO_SLUG)
    destino_base = f"{REPO_SLUG}_{COMMIT_ID_CORTO}"
    destino_path = os.path.abspath(destino_base)
    log_path = os.path.join(destino_path, "cambios.log")

    # Verificar si el repositorio realmente existe
    if not os.path.exists(repo_path):
        print(f"❌ Error: No se encontró el repositorio '{repo_path}'. Asegúrate de que está clonado en la raíz.")
        exit(1)

    # Crear carpeta de destino si no existe
    os.makedirs(destino_path, exist_ok=True)

    # Crear estructura de carpetas Kiuwan
    kiuwan_base = os.path.abspath(f"kiuwan_{destino_base}")
    os.makedirs(kiuwan_base, exist_ok=True)

    # Crear subdirectorios necesarios
    estructura_kiuwan = [
        f"Analisis_Kiuwan-{destino_base}",
        f"Analisis_Kiuwan-{destino_base}/Analisis de Codigo/Defectos",
        f"Analisis_Kiuwan-{destino_base}/Analisis de Codigo/Resumen",
        f"Analisis_Kiuwan-{destino_base}/Seguridad de Codigo/Resumen",
        f"Analisis_Kiuwan-{destino_base}/Seguridad de Codigo/Vulnerabilidades"
    ]

    for subdir in estructura_kiuwan:
        full_path = os.path.join(kiuwan_base, subdir)
        os.makedirs(full_path, exist_ok=True)

    # Copiar archivos XLSX desde la raíz del proyecto a la ubicación correcta
    shutil.copy2("Inventario de vulnerabilidades.xlsx",
                 os.path.join(kiuwan_base, f"Analisis_Kiuwan-{destino_base}", "Inventario de vulnerabilidades.xlsx"))
    shutil.copy2("Plantilla de reportesKiuwan.xlsx", os.path.join(kiuwan_base, "Plantilla de reportesKiuwan.xlsx"))


    # Copiar archivos modificados y agregados
    def copiar_archivo(archivo):
        origen = os.path.join(repo_path, archivo)
        base_nombre = os.path.basename(archivo)
        destino = os.path.join(destino_path, base_nombre)

        if os.path.exists(origen):
            contador = 1
            while os.path.exists(destino):
                nombre, extension = os.path.splitext(base_nombre)
                destino = os.path.join(destino_path, f"{nombre}_{contador}{extension}")
                contador += 1

            shutil.copy2(origen, destino)
            return f"✅ Copiado: {archivo} → {os.path.basename(destino)}"
        else:
            return f"⚠️ Archivo no encontrado: {archivo}"


    print("\n📌 Archivos Modificados:")
    for archivo in tqdm(archivos_modificados, desc="Copiando archivos modificados"):
        print(copiar_archivo(archivo))

    print("\n📌 Archivos Agregados:")
    for archivo in tqdm(archivos_agregados, desc="Copiando archivos agregados"):
        print(copiar_archivo(archivo))

    print(f"\n📁 Estructura Kiuwan creada en '{kiuwan_base}'.")
    print(f"📜 Registro guardado en '{log_path}'.")
else:
    print(f"❌ Error {response.status_code}: {response.text}")
