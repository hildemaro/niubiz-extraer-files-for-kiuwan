import requests
import re
import os
import shutil
import tkinter as tk
from tkinter import simpledialog
import config  # Importar credenciales desde config.py
from tqdm import tqdm  # Barra de progreso

# 🔹 Crear ventana oculta para el cuadro de diálogo
root = tk.Tk()
root.withdraw()  # Oculta la ventana principal

# 🔹 Pedir la URL del commit al usuario
COMMIT_URL = simpledialog.askstring(
    "Bitbucket - Ingresar URL",
    "Por favor, ingrese la URL del commit:",
    parent=root
)

# 🔹 Validar la URL ingresada
if not COMMIT_URL:
    print("❌ No ingresaste ninguna URL. Saliendo...")
    exit(1)

# 🔹 Expresión regular para extraer workspace, repo_slug y commit_id
match = re.search(r"https://bitbucket.org/([^/]+)/([^/]+)/commits/([a-f0-9]+)", COMMIT_URL)

if not match:
    print("❌ Error: La URL del commit no es válida.")
    exit(1)

WORKSPACE, REPO_SLUG, COMMIT_ID = match.groups()
COMMIT_ID_CORTO = COMMIT_ID[:7]  # Tomar solo los primeros 7 caracteres

# 🔹 Configuración de autenticación desde config.py
USERNAME = config.USERNAME
APP_PASSWORD = config.APP_PASSWORD

# 🔹 URL de la API de Bitbucket
API_URL = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{REPO_SLUG}/diffstat/{COMMIT_ID}"

# 🔹 Autenticación usando usuario y App Password
response = requests.get(API_URL, auth=(USERNAME, APP_PASSWORD))

# 🔹 Procesar la respuesta
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

    # 🔹 Ruta del repositorio en la raíz
    repo_path = os.path.abspath(REPO_SLUG)  # Carpeta donde está el repo
    destino_path = os.path.abspath(f"{REPO_SLUG}_{COMMIT_ID_CORTO}")  # Carpeta de salida
    log_path = os.path.join(destino_path, "cambios.log")  # Archivo de log

    # 🔹 Verificar si el repositorio realmente existe
    if not os.path.exists(repo_path):
        print(f"❌ Error: No se encontró el repositorio '{repo_path}'. Asegúrate de que está clonado en la raíz.")
        exit(1)

    # 🔹 Crear carpeta de destino si no existe
    os.makedirs(destino_path, exist_ok=True)

    # 🔹 Abrir archivo de log
    with open(log_path, "w", encoding="utf-8") as log_file:

        # 🔹 Función para copiar archivos sin mantener carpetas y renombrar duplicados
        def copiar_archivo(archivo):
            origen = os.path.join(repo_path, archivo)
            base_nombre = os.path.basename(archivo)
            destino = os.path.join(destino_path, base_nombre)

            if os.path.exists(origen):
                # Si el archivo ya existe, agregar un número incremental
                contador = 1
                while os.path.exists(destino):
                    nombre, extension = os.path.splitext(base_nombre)
                    destino = os.path.join(destino_path, f"{nombre}_{contador}{extension}")
                    contador += 1

                shutil.copy2(origen, destino)
                log_file.write(f"✅ Copiado: {archivo} → {os.path.basename(destino)}\n")
                return f"✅ {archivo} → {os.path.basename(destino)}"
            else:
                log_file.write(f"⚠️ Archivo no encontrado en el repositorio: {archivo}\n")
                return f"⚠️ Archivo no encontrado: {archivo}"


        # 🔹 Copiar archivos modificados con barra de progreso
        print("\n📌 Archivos Modificados:")
        for archivo in tqdm(archivos_modificados, desc="Copiando archivos modificados"):
            print(copiar_archivo(archivo))

        # 🔹 Copiar archivos agregados con barra de progreso
        print("\n📌 Archivos Agregados:")
        for archivo in tqdm(archivos_agregados, desc="Copiando archivos agregados"):
            print(copiar_archivo(archivo))

        # 🔹 Mostrar archivos eliminados y escribir en log
        print("\n📌 Archivos Eliminados:")
        for archivo in archivos_eliminados:
            log_file.write(f"❌ Eliminado: {archivo}\n")
            print(f"❌ Eliminado: {archivo}")

    print(
        f"\n📁 Todos los archivos modificados y agregados han sido copiados en '{destino_path}' sin estructura de carpetas.")
    print(f"📜 Se ha guardado un registro en '{log_path}'.")

else:
    print(f"❌ Error {response.status_code}: {response.text}")
