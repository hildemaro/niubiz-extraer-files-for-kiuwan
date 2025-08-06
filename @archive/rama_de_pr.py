import requests
import json
import tkinter as tk
from tkinter import simpledialog

# --- Configuración (Reemplaza estos valores) ---
USERNAME = "ntt_jcardenas"
APP_PASSWORD = "ATBBXsHerSFmvmbKsCgesefdYnK90D438512"


# Función para extraer la información de la URL del PR
def obtener_datos_de_url(url):
    partes = url.split('/')
    # La estructura de la URL de Bitbucket es /propietario/repositorio/pull-requests/id
    project_key = partes[-4]
    repository_slug = partes[-3]
    pr_id = partes[-1]

    return project_key, repository_slug, pr_id


# Función principal para realizar la consulta a la API
def consultar_pr():
    # Crea la ventana principal de Tkinter, pero la oculta
    root = tk.Tk()
    root.withdraw()

    # Muestra un cuadro de diálogo para pedir la URL del PR
    pr_url = simpledialog.askstring("Entrada", "Ingresa la URL del Pull Request de Bitbucket:")

    if not pr_url:
        print("🚫 Proceso cancelado por el usuario.")
        return

    try:
        # Extrae los componentes de la URL
        project_key, repository_slug, pr_id = obtener_datos_de_url(pr_url)

        # Construye la URL de la API
        api_url = f"https://api.bitbucket.org/2.0/repositories/{project_key}/{repository_slug}/pullrequests/{pr_id}"

        print(f"🔗 URL de la API a consultar: {api_url}")

        # Realiza la petición GET con autenticación básica
        response = requests.get(api_url, auth=(USERNAME, APP_PASSWORD))
        response.raise_for_status()

        # Parsea la respuesta JSON
        pr_data = response.json()

        # Extrae el nombre de las ramas
        source_branch = pr_data['source']['branch']['name']
        destination_branch = pr_data['destination']['branch']['name']

        print(f"✅ Extracción de ramas exitosa para el PR #{pr_id}:")
        print(f"  - Rama Origen (Source): {source_branch}")
        print(f"  - Rama Destino (Destination): {destination_branch}")

    except (requests.exceptions.RequestException, KeyError) as e:
        print(f"🚫 Ocurrió un error: {e}")
        print("Asegúrate de que la URL sea válida y de tener los permisos correctos.")


# Llama a la función principal
if __name__ == "__main__":
    consultar_pr()