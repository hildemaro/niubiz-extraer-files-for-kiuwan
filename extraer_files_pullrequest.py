import os
import requests
import re
import json
import shutil
import tkinter as tk
from tkinter import simpledialog
from tqdm import tqdm  # Para la barra de progreso
from config import USERNAME, APP_PASSWORD  # Importar credenciales desde config.py

# 🔹 Crear ventana para ingresar la URL del Pull Request
root = tk.Tk()
root.withdraw()
pr_url = simpledialog.askstring("URL del Pull Request", "Ingresa la URL del Pull Request:", parent=root)

if not pr_url:
    print("❌ No ingresaste ninguna URL. Saliendo...")
    exit(1)

# 🔹 Extraer workspace, repo_slug y PR ID desde la URL
match = re.search(r'bitbucket\.org/([^/]+)/([^/]+)/pull-requests/(\d+)', pr_url)
if not match:
    print("❌ URL no válida. Asegúrate de ingresar una URL correcta de Bitbucket.")
    exit(1)

workspace, repo_slug, pull_request_id = match.groups()

# 🔹 Construir la URL de la API para obtener archivos modificados
api_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/pullrequests/{pull_request_id}/diffstat"

# 🔹 Realizar la solicitud a la API de Bitbucket
response = requests.get(api_url, auth=(USERNAME, APP_PASSWORD))

if response.status_code != 200:
    print(f"❌ Error al obtener los archivos. Código {response.status_code}: {response.text}")
    exit(1)

# 🔹 Procesar la respuesta JSON
data = response.json()
archivos_a_copiar = []
archivos_eliminados = []

for item in data.get('values', []):
    status = item.get('status')  # "modified", "added" o "removed"
    archivo = item.get('new', {}).get('path', item.get('old', {}).get('path', 'Desconocido'))

    if status == "removed":
        archivos_eliminados.append(archivo)
    else:
        archivos_a_copiar.append(archivo)

# 🔹 Carpeta del repositorio (ya existe en la raíz)
repo_folder = repo_slug  # El nombre del repositorio ya está como carpeta
if not os.path.exists(repo_folder):
    print(f"❌ No se encontró la carpeta del repositorio '{repo_folder}'.")
    exit(1)

# 🔹 Carpeta de destino con la nomenclatura: (Nombre del Repo)_(PR ID)
destino_path = f"{repo_folder}_{pull_request_id}"
os.makedirs(destino_path, exist_ok=True)

# 🔹 Archivo de log dentro de la carpeta de destino
log_path = os.path.join(destino_path, "cambios.log")

# 🔹 Copiar archivos modificados/agregados y registrar en log
with open(log_path, "w", encoding="utf-8") as log_file:

    def copiar_archivo(archivo):
        origen = os.path.join(repo_folder, archivo)
        destino = os.path.join(destino_path, os.path.basename(archivo))

        # Si el archivo no existe en el repositorio, ignorarlo
        if not os.path.exists(origen):
            print(f"⚠️ Archivo no encontrado en el repo: {archivo}")
            return None

        # Si el archivo ya existe en la carpeta de destino, agregar un número incremental
        contador = 1
        while os.path.exists(destino):
            nombre, extension = os.path.splitext(os.path.basename(archivo))
            destino = os.path.join(destino_path, f"{nombre}_{contador}{extension}")
            contador += 1

        shutil.copy2(origen, destino)
        log_file.write(f"✅ Copiado: {archivo} → {os.path.basename(destino)}\n")
        return f"✅ {archivo} → {os.path.basename(destino)}"

    # 🔹 Mostrar barra de progreso
    print("\n📌 Copiando archivos:")
    for archivo in tqdm(archivos_a_copiar, desc="Progreso"):
        print(copiar_archivo(archivo))

# 🔹 Registrar archivos eliminados en el log y mostrarlos en pantalla
if archivos_eliminados:
    print("\n🗑️ Archivos eliminados en este Pull Request:")
    for archivo in archivos_eliminados:
        print(f"🗑️ {archivo}")
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"🗑️ Eliminado: {archivo}\n")

print(f"\n📁 Todos los archivos han sido copiados en '{destino_path}'.")
print(f"📜 Se ha guardado un registro en '{log_path}'.")
