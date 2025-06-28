import os
import re
import shutil
import requests
import tkinter as tk
from tkinter import simpledialog
from tqdm import tqdm  # Barra de progreso
import config  # Importar credenciales desde config.py

# Crear ventana oculta para el cuadro de diálogo
root = tk.Tk()
root.withdraw()

# 🔹 Menú de selección
opcion = simpledialog.askstring(
    "Selección de Extracción",
    "Seleccione el tipo de extracción:\n1. Commit\n2. Pull Request\n3. Repositorio Remoto (Clonar)",
    parent=root
)

if opcion not in ["1", "2", "3"]:
    print("❌ Opción inválida. Saliendo...")
    exit(1)

# 🔹 Variables comunes
WORKSPACE, REPO_SLUG, IDENTIFICADOR = None, None, None
archivos_modificados, archivos_agregados, archivos_eliminados = [], [], []
GIT_CLONE_URL = None  # Variable para almacenar la URL de clonación

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
    IDENTIFICADOR = COMMIT_ID[:7]  # Usar hash corto del commit
    # Construir URL de clonación para el repositorio del commit
    GIT_CLONE_URL = f"https://{config.USERNAME}@bitbucket.org/{WORKSPACE}/{REPO_SLUG}.git"

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
    # Construir URL de clonación para el repositorio del PR
    GIT_CLONE_URL = f"https://{config.USERNAME}@bitbucket.org/{WORKSPACE}/{REPO_SLUG}.git"

elif opcion == "3":  # Repositorio Remoto (Clonar)
    # Para la opción 3, solo preguntamos el REPO_SLUG
    REPO_SLUG = simpledialog.askstring(
        "Bitbucket - Clonar Repositorio",
        "Ingrese el nombre del REPOSITORIO (ej: aws.api.qr.manager):",
        parent=root
    )
    if not REPO_SLUG:
        print("❌ No ingresaste el nombre del repositorio. Saliendo...")
        exit(1)

    # Usamos la URL de clonación fija que especificaste, asumiendo que el WORKSPACE es 'VisaNet_TI'
    # y el usuario de clonación es 'ntt_jcardenas'
    WORKSPACE = "VisaNet_TI"  # Asumiendo un WORKSPACE fijo para esta URL de clonación
    GIT_CLONE_URL = f"https://ntt_jcardenas@bitbucket.org/{WORKSPACE}/{REPO_SLUG}.git"
    IDENTIFICADOR = "repo"  # Identificador para la carpeta de destino

# 🔹 Preguntar por la rama y proceder con la clonación (para todas las opciones)
# Esta sección ya aplica a todas las opciones, incluyendo la 3.
branch_para_clonar = simpledialog.askstring(
    "Clonación de Repositorio",
    "Ingrese el nombre de la rama para clonar (ej: develop, master):",
    parent=root
)
if not branch_para_clonar:
    print("❌ No se especificó una rama para clonar. La clonación se omitirá.")
    exit(1)  # Salir si no hay rama para clonar

# Directorio donde se clonará el repositorio
# Usamos el REPO_SLUG extraído para el nombre de la carpeta de destino de la clonación
clone_target_dir = os.path.join(os.getcwd(), REPO_SLUG)

if os.path.exists(clone_target_dir):
    print(f"⚠️ La carpeta '{REPO_SLUG}' ya existe en '{os.getcwd()}'. No se clonará para evitar sobrescribir.")
    print(f"Se usará la carpeta existente '{clone_target_dir}' para el análisis.")
else:
    print(f"\n🌀 Clonando repositorio '{REPO_SLUG}' en la rama '{branch_para_clonar}'...")
    clone_command = f"git clone -b {branch_para_clonar} {GIT_CLONE_URL}"
    try:
        os.system(clone_command)
        print("✅ Repositorio clonado exitosamente.")
    except Exception as e:
        print(f"❌ Error al clonar el repositorio: {e}")
        print("Por favor, asegúrate de que Git está instalado y configurado correctamente.")
        exit(1)

# Aseguramos que REPO_SLUG_CLONED_PATH apunte a la carpeta clonada para el resto del script
REPO_SLUG_CLONED_PATH = clone_target_dir

# 🔹 Definir rutas de salida con nomenclatura Kiuwan
# DESTINO_BASE ahora usa el nombre de la carpeta clonada
DESTINO_BASE = f"{os.path.basename(REPO_SLUG_CLONED_PATH)}_{IDENTIFICADOR}"
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
shutil.copy2("Inventario de vulnerabilidades.xlsx",
             os.path.join(KIUWAN_BASE, f"Analisis_Kiuwan-{DESTINO_BASE}", "Inventario de vulnerabilidades.xlsx"))
shutil.copy2("Plantilla de reportesKiuwan.xlsx", os.path.join(KIUWAN_BASE, "Plantilla de reportesKiuwan.xlsx"))

# 🔹 Obtener archivos modificados según la opción seleccionada
if opcion == "1":  # Commit
    API_URL = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{REPO_SLUG}/diffstat/{COMMIT_ID}"
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

elif opcion == "3":  # Repositorio Remoto (Clonado)
    # Después de clonar, todos los archivos del repositorio clonado son los "modificados" para esta opción
    for root_dir, _, files in os.walk(REPO_SLUG_CLONED_PATH):
        for file in files:
            archivos_modificados.append(os.path.relpath(os.path.join(root_dir, file), REPO_SLUG_CLONED_PATH))

# 🔹 Copiar archivos extraídos a la carpeta de destino
# REPO_PATH ahora es la carpeta donde se clonó el repositorio
REPO_PATH = os.path.abspath(REPO_SLUG_CLONED_PATH)
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