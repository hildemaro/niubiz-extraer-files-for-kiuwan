import os
import re
import shutil
import requests
import tkinter as tk
from tkinter import simpledialog
from tqdm import tqdm
import config

# Crear ventana oculta para el cuadro de diálogo
root = tk.Tk()
root.withdraw()

# 🔹 Pedir número de historia
def pedir_numero_historia():
    while True:
        historia = simpledialog.askstring(
            "Número de Historia",
            "Ingrese el número de historia (ej: ABCD-1234):",
            parent=root
        )
        if not historia:
            print("❌ No ingresaste el número de historia. Saliendo...")
            exit(1)
        # Expresión regular para validar el formato de la historia
        if re.match(r"^[A-Z]{3,5}-\d{1,5}$", historia):
            return historia
        else:
            print("❌ Formato de historia no válido. Debe ser ABCD-1234. Intente de nuevo.")

NUMERO_HISTORIA = pedir_numero_historia()

# 🔹 Menú de selección
opcion = simpledialog.askstring(
    "Selección de Extracción",
    "Seleccione el tipo de extracción:\n1. Commit\n2. Pull Request\n3. Repositorio",
    parent=root
)

if opcion not in ["1", "2", "3"]:
    print("❌ Opción inválida. Saliendo...")
    exit(1)

# 🔹 Variables comunes
WORKSPACE, REPO_SLUG, IDENTIFICADOR, RAMA = None, None, None, None
archivos_modificados, archivos_agregados, archivos_eliminados = [], [], []

def get_branch_from_commit(workspace, repo_slug, commit_hash):
    """
    Obtiene la rama de un commit específico.
    """
    branches_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/refs/branches"
    auth = (config.USERNAME, config.APP_PASSWORD)
    try:
        response = requests.get(branches_url, auth=auth)
        response.raise_for_status()
        branches_data = response.json()
        for branch in branches_data.get("values", []):
            branch_name = branch.get("name")
            commits_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/commits?include={branch_name}"
            while commits_url:
                commits_response = requests.get(commits_url, auth=auth)
                commits_response.raise_for_status()
                commits_data = commits_response.json()
                for commit in commits_data.get("values", []):
                    if commit.get("hash") == commit_hash:
                        return branch_name
                commits_url = commits_data.get("next")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con la API de Bitbucket: {e}")
        return None

if opcion == "1":  # Commit
    COMMIT_URL = simpledialog.askstring("Bitbucket - Ingresar URL", "Ingrese la URL del commit:", parent=root)
    if not COMMIT_URL:
        print("❌ No ingresaste ninguna URL. Saliendo...")
        exit(1)
    match = re.search(r"https://bitbucket.org/([^/]+)/([^/]+)/commits/([a-f0-9]+)", COMMIT_URL)
    if not match:
        print("❌ Error: La URL del commit no es válida.")
        exit(1)
    WORKSPACE, REPO_SLUG, COMMIT_ID = match.groups()
    IDENTIFICADOR = COMMIT_ID[:7]
    RAMA = get_branch_from_commit(WORKSPACE, REPO_SLUG, COMMIT_ID)
    if not RAMA:
        print("❌ No se pudo encontrar la rama para el commit especificado.")
        exit(1)

elif opcion == "2":  # Pull Request
    PR_URL = simpledialog.askstring("Bitbucket - Ingresar URL", "Ingrese la URL del Pull Request:", parent=root)
    if not PR_URL:
        print("❌ No ingresaste ninguna URL. Saliendo...")
        exit(1)
    match = re.search(r"bitbucket\.org/([^/]+)/([^/]+)/pull-requests/(\d+)", PR_URL)
    if not match:
        print("❌ URL no válida. Saliendo...")
        exit(1)
    WORKSPACE, REPO_SLUG, IDENTIFICADOR = match.groups()
    try:
        api_url = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{REPO_SLUG}/pullrequests/{IDENTIFICADOR}"
        response = requests.get(api_url, auth=(config.USERNAME, config.APP_PASSWORD))
        response.raise_for_status()
        pr_data = response.json()
        RAMA = pr_data['source']['branch']['name']
    except (requests.exceptions.RequestException, KeyError) as e:
        print(f"❌ Error al obtener la rama del Pull Request: {e}")
        exit(1)

elif opcion == "3":  # Repositorio
    REPO_SLUG = simpledialog.askstring("Seleccionar Carpeta", "Ingrese el nombre del repositorio a copiar:", parent=root)
    if not REPO_SLUG or not os.path.exists(REPO_SLUG):
        print("❌ Error: No se encontró la carpeta del repositorio.")
        exit(1)
    IDENTIFICADOR = "repo"
    RAMA = simpledialog.askstring("Nombre de la Rama", "Ingrese el nombre de la rama asociada:", parent=root)
    if not RAMA:
        print("❌ No ingresaste el nombre de la rama. Saliendo...")
        exit(1)

# 🔹 Definir rutas de salida con nomenclatura Kiuwan y el número de historia
DESTINO_BASE = f"{REPO_SLUG}_{IDENTIFICADOR}_{NUMERO_HISTORIA}"
KIUWAN_BASE = os.path.abspath(f"kiuwan_{DESTINO_BASE}")
os.makedirs(KIUWAN_BASE, exist_ok=True)

# 🔹 Crear estructura de carpetas Kiuwan
estructura_kiuwan = [
    f"Analisis_Kiuwan-{DESTINO_BASE}",
    f"Analisis_Kiuwan-{DESTINO_BASE}/Analisis de Codigo/Defectos",
    f"Analisis_Kiuwan-{DESTINO_BASE}/Analisis de Codigo/Resumen",
    f"Analisis_Kiuwan-{DESTINO_BASE}/Seguridad de Codigo/Resumen",
    f"Analisis_Kiuwan-{DESTINO_BASE}/Seguridad de Codigo/Vulnerabilidades"
]
for subdir in estructura_kiuwan:
    os.makedirs(os.path.join(KIUWAN_BASE, subdir), exist_ok=True)

# 🔹 Copiar archivos XLSX
shutil.copy2("Inventario de vulnerabilidades.xlsx", os.path.join(KIUWAN_BASE, f"Analisis_Kiuwan-{DESTINO_BASE}", "Inventario de vulnerabilidades.xlsx"))
shutil.copy2("Plantilla de reportesKiuwan.xlsx", os.path.join(KIUWAN_BASE, "Plantilla de reportesKiuwan.xlsx"))

# 🔹 Obtener archivos modificados según la opción seleccionada
if opcion == "1":  # Commit
    API_URL = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{REPO_SLUG}/diffstat/{IDENTIFICADOR}"
elif opcion == "2":  # Pull Request
    API_URL = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{REPO_SLUG}/pullrequests/{IDENTIFICADOR}/diffstat"

if opcion in ["1", "2"]:
    response = requests.get(API_URL, auth=(config.USERNAME, config.APP_PASSWORD))
    if response.status_code != 200:
        print(f"❌ Error {response.status_code}: {response.text}")
        exit(1)
    data = response.json()
    for item in data.get("values", []):
        status = item.get("status")
        new_data = item.get("new") or {}
        old_data = item.get("old") or {}
        new_path = new_data.get("path")
        old_path = old_data.get("path")

        if status == "modified" and new_path:
            archivos_modificados.append(new_path)
        elif status == "added" and new_path:
            archivos_agregados.append(new_path)
        elif status == "removed" and old_path:
            archivos_eliminados.append(old_path)

elif opcion == "3":  # Repositorio
    for root_dir, _, files in os.walk(REPO_SLUG):
        for file in files:
            archivos_modificados.append(os.path.relpath(os.path.join(root_dir, file), REPO_SLUG))

# 🔹 Copiar archivos extraídos a la carpeta de destino
REPO_PATH = os.path.abspath(REPO_SLUG)
DESTINO_PATH = os.path.abspath(DESTINO_BASE)
os.makedirs(DESTINO_PATH, exist_ok=True)

def copiar_archivo(archivo):
    origen = os.path.join(REPO_PATH, archivo)
    destino = os.path.join(DESTINO_PATH, os.path.basename(archivo))
    if os.path.exists(origen):
        contador = 1
        while os.path.exists(destino):
            nombre, extension = os.path.splitext(os.path.basename(archivo))
            destino = os.path.join(DESTINO_PATH, f"{nombre}_{contador}{extension}")
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
print("\n📌 Archivos Eliminados:")
for archivo in archivos_eliminados:
    print(f"❌ Eliminado: {archivo}")

print(f"\n📁 Estructura Kiuwan creada en '{KIUWAN_BASE}'.")
print(f"🌳 Rama asociada: {RAMA}")