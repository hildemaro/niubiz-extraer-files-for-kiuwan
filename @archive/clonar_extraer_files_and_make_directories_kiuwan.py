import os
import re
import shutil
import requests
import tkinter as tk
from tkinter import simpledialog
from tqdm import tqdm
import config
import platform

# --- CONFIGURACIÓN DE KIUWAN ---
KIUWAN_APP_NAME = "Aplicaciones_Vendemas"
# --- FIN CONFIGURACIÓN ---

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
GIT_CLONE_URL = None

if opcion == "1":
    COMMIT_URL = simpledialog.askstring("Bitbucket - Ingresar URL", "Ingrese la URL del commit:", parent=root)
    if not COMMIT_URL: exit(print("❌ No ingresaste ninguna URL. Saliendo..."))
    match = re.search(r"https://bitbucket.org/([^/]+)/([^/]+)/commits/([a-f0-9]+)", COMMIT_URL)
    if not match: exit(print("❌ Error: La URL del commit no es válida."))
    WORKSPACE, REPO_SLUG, COMMIT_ID = match.groups()
    IDENTIFICADOR = COMMIT_ID[:7]
    GIT_CLONE_URL = f"https://{config.USERNAME}@bitbucket.org/{WORKSPACE}/{REPO_SLUG}.git"

elif opcion == "2":
    PR_URL = simpledialog.askstring("Bitbucket - Ingresar URL", "Ingrese la URL del Pull Request:", parent=root)
    if not PR_URL: exit(print("❌ No ingresaste ninguna URL. Saliendo..."))
    match = re.search(r"bitbucket\.org/([^/]+)/([^/]+)/pull-requests/(\d+)", PR_URL)
    if not match: exit(print("❌ URL no válida. Saliendo..."))
    WORKSPACE, REPO_SLUG, IDENTIFICADOR = match.groups()
    GIT_CLONE_URL = f"https://{config.USERNAME}@bitbucket.org/{WORKSPACE}/{REPO_SLUG}.git"

elif opcion == "3":
    REPO_SLUG = simpledialog.askstring("Bitbucket - Clonar Repositorio",
                                       "Ingrese el nombre del REPOSITORIO (ej: aws.api.qr.manager):", parent=root)
    if not REPO_SLUG: exit(print("❌ No ingresaste el nombre del repositorio. Saliendo..."))
    WORKSPACE = "VisaNet_TI"
    GIT_CLONE_URL = f"https://ntt_jcardenas@bitbucket.org/{WORKSPACE}/{REPO_SLUG}.git"
    IDENTIFICADOR = "repo"

# 🔹 Clonación
branch_para_clonar = simpledialog.askstring("Clonación de Repositorio",
                                            "Ingrese el nombre de la rama para clonar (ej: develop, master):",
                                            parent=root)
if not branch_para_clonar: exit(print("❌ No se especificó una rama para clonar. Saliendo..."))

clone_target_dir = os.path.join(os.getcwd(), REPO_SLUG)

if os.path.exists(clone_target_dir):
    print(f"⚠️  La carpeta '{REPO_SLUG}' ya existe. Se usará la carpeta existente para el análisis.")
else:
    print(f"\n🌀 Clonando repositorio '{REPO_SLUG}' en la rama '{branch_para_clonar}'...")
    os.system(f"git clone -b {branch_para_clonar} {GIT_CLONE_URL}")
    print("✅ Repositorio clonado exitosamente.")

REPO_SLUG_CLONED_PATH = clone_target_dir

# 🔹 Preparación de carpetas y archivos
DESTINO_BASE = f"{os.path.basename(REPO_SLUG_CLONED_PATH)}_{IDENTIFICADOR}"
DESTINO_PATH = os.path.abspath(DESTINO_BASE)
os.makedirs(DESTINO_PATH, exist_ok=True)

# Lógica de obtención y copia de archivos
if opcion in ["1", "2"]:
    API_URL = ""
    if opcion == "1":
        API_URL = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{REPO_SLUG}/diffstat/{COMMIT_ID}"
    else:
        API_URL = f"https://api.bitbucket.org/2.0/repositories/{WORKSPACE}/{REPO_SLUG}/pullrequests/{IDENTIFICADOR}/diffstat"

    response = requests.get(API_URL, auth=(config.USERNAME, config.APP_PASSWORD))
    if response.status_code != 200: exit(print(f"❌ Error {response.status_code}: {response.text}"))

    data = response.json()
    for item in data.get("values", []):
        status = item.get("status")
        new_path = (item.get("new") or {}).get("path")
        old_path = (item.get("old") or {}).get("path")
        if status == "modified":
            archivos_modificados.append(new_path)
        elif status == "added":
            archivos_agregados.append(new_path)
        elif status == "removed":
            archivos_eliminados.append(old_path)

elif opcion == "3":
    for root_dir, _, files in os.walk(REPO_SLUG_CLONED_PATH):
        for file in files:
            archivos_modificados.append(os.path.relpath(os.path.join(root_dir, file), REPO_SLUG_CLONED_PATH))

REPO_PATH = os.path.abspath(REPO_SLUG_CLONED_PATH)


def copiar_archivo(archivo):
    origen = os.path.join(REPO_PATH, archivo)
    destino_final = os.path.join(DESTINO_PATH, archivo)
    if os.path.exists(origen):
        os.makedirs(os.path.dirname(destino_final), exist_ok=True)
        shutil.copy2(origen, destino_final)
        return f"✅ Copiado: {archivo}"
    else:
        return f"⚠️  Archivo no encontrado: {archivo}"


print("\n📌 Archivos Modificados:")
for archivo in tqdm(archivos_modificados, desc="Copiando archivos modificados"): print(copiar_archivo(archivo))
print("\n📌 Archivos Agregados:")
for archivo in tqdm(archivos_agregados, desc="Copiando archivos agregados"): print(copiar_archivo(archivo))
print("\n📌 Archivos Eliminados:")
for archivo in archivos_eliminados: print(f"❌ Eliminado: {archivo}")

print(f"\n📁 Archivos para análisis preparados en: '{DESTINO_PATH}'")

# ==============================================================================
# 🔹 Creación de Estructura de Carpetas Kiuwan para Reportes (LÓGICA REINTEGRADA)
# ==============================================================================
print("\n🌀 Creando estructura de carpetas para reportes Kiuwan...")
try:
    KIUWAN_BASE = os.path.abspath(f"kiuwan_{DESTINO_BASE}")
    os.makedirs(KIUWAN_BASE, exist_ok=True)

    estructura_kiuwan = [
        f"Analisis_Kiuwan-{DESTINO_BASE}",
        f"Analisis_Kiuwan-{DESTINO_BASE}/Analisis de Codigo/Defectos",
        f"Analisis_Kiuwan-{DESTINO_BASE}/Analisis de Codigo/Resumen",
        f"Analisis_Kiuwan-{DESTINO_BASE}/Seguridad de Codigo/Resumen",
        f"Analisis_Kiuwan-{DESTINO_BASE}/Seguridad de Codigo/Vulnerabilidades"
    ]
    for subdir in estructura_kiuwan:
        os.makedirs(os.path.join(KIUWAN_BASE, subdir), exist_ok=True)

    # Copiar archivos XLSX
    shutil.copy2("Inventario de vulnerabilidades.xlsx",
                 os.path.join(KIUWAN_BASE, f"Analisis_Kiuwan-{DESTINO_BASE}", "Inventario de vulnerabilidades.xlsx"))
    shutil.copy2("Plantilla de reportesKiuwan.xlsx", os.path.join(KIUWAN_BASE, "Plantilla de reportesKiuwan.xlsx"))
    print(f"✅ Estructura de reportes creada exitosamente en '{KIUWAN_BASE}'")

except FileNotFoundError as e:
    print(
        f"\n⚠️  ADVERTENCIA: No se pudo copiar el archivo de reporte '{e.filename}'. Asegúrate que exista en el mismo directorio que el script.")
except Exception as e:
    print(f"\n⚠️  ADVERTENCIA: Ocurrió un error creando la estructura de carpetas para reportes: {e}")

# ==============================================================================
# 🔹 Ejecución del Análisis Kiuwan
# ==============================================================================
print("\n" + "=" * 50)
print("🚀 INICIANDO ESCANEO KIUWAN")
print("=" * 50)

try:
    # 1. Determinar la ruta base de forma dinámica
    script_dir = os.path.dirname(os.path.abspath(__file__))
    kiuwan_bin_path = os.path.join(script_dir, "KiuwanLocalAnalyzer", "bin")

    if not os.path.isdir(kiuwan_bin_path):
        raise FileNotFoundError(f"No se pudo encontrar el directorio de Kiuwan en '{kiuwan_bin_path}'.")

    # 2. Determinar el ejecutable correcto
    agent_filename = "agent.cmd" if platform.system() == "Windows" else "agent.sh"
    kiuwan_executable = os.path.join(kiuwan_bin_path, agent_filename)

    if not os.path.exists(kiuwan_executable):
        raise FileNotFoundError(f"El ejecutable '{agent_filename}' no se encuentra en '{kiuwan_bin_path}'")

    # 3. Pedir la etiqueta para el escaneo
    scan_label = simpledialog.askstring("Etiqueta del Escaneo Kiuwan",
                                        "Ingrese un nombre (etiqueta) para este escaneo:", parent=root)
    if not scan_label:
        exit("❌ No se ingresó etiqueta para el escaneo. Abortando.")

    # 4. La carpeta a escanear es DESTINO_PATH
    source_path_to_scan = DESTINO_PATH

    # 5. Construir el comando Kiuwan
    kiuwan_command = f'"{kiuwan_executable}" -s "{source_path_to_scan}" -n "{KIUWAN_APP_NAME}" -l "{scan_label}"'

    print(f"\n▶️  Ejecutando el siguiente comando Kiuwan:\n")
    print(kiuwan_command)
    print("\n" + "-" * 50)

    # 6. Ejecutar el comando
    os.system(kiuwan_command)
    print("\n" + "-" * 50)
    print("✅ Escaneo Kiuwan iniciado.")

except FileNotFoundError as e:
    print(f"\n❌ ERROR DE CONFIGURACIÓN: {e}")
except Exception as e:
    print(f"\n❌ Error inesperado durante el escaneo de Kiuwan: {e}")