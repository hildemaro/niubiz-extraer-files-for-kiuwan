# Archivo: main_script.py
import requests
from config import USERNAME, APP_PASSWORD
import tkinter as tk
from tkinter import simpledialog


def get_last_branch_from_commit(workspace, repo_slug, commit_hash, username, app_password):
    """
    Obtiene la última rama que contiene un commit específico.

    Args:
        workspace (str): El workspace de Bitbucket (dueño del repo).
        repo_slug (str): El nombre del repositorio.
        commit_hash (str): El hash del commit a buscar.
        username (str): El nombre de usuario para la autenticación.
        app_password (str): La App password de Bitbucket.

    Returns:
        str: El nombre de la última rama encontrada o None si no se encuentra.
    """

    branches_url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/refs/branches"
    auth = (username, app_password)

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
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        return None


if __name__ == "__main__":

    # Credenciales del archivo config.py
    mi_username = USERNAME
    mi_app_password = APP_PASSWORD

    # Crea la ventana de Tkinter y la oculta
    root = tk.Tk()
    root.withdraw()

    # Muestra un cuadro de diálogo para pedir la URL del commit
    commit_url = simpledialog.askstring("Input", "Ingresa la URL completa del commit:")

    if commit_url:
        try:
            # Extrae los datos de la URL
            parts = commit_url.split('/')
            mi_workspace = parts[-4]
            mi_repo_slug = parts[-3]
            mi_commit_hash = parts[-1]

            print(f"Buscando el commit: {mi_commit_hash} en el repositorio: {mi_repo_slug}...")

            ultima_rama = get_last_branch_from_commit(mi_workspace, mi_repo_slug, mi_commit_hash, mi_username,
                                                      mi_app_password)

            if ultima_rama:
                print(f"La última rama del commit {mi_commit_hash} es: {ultima_rama}")
            else:
                print(f"No se encontraron ramas asociadas al commit {mi_commit_hash} o hubo un error.")

        except IndexError:
            print("Formato de URL inválido. Por favor, asegúrate de que sea la URL completa del commit.")
    else:
        print("Búsqueda cancelada por el usuario.")