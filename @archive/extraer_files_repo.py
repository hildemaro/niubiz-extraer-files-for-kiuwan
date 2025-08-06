import os
import shutil
import tkinter as tk
from tkinter import simpledialog
from tqdm import tqdm  # Barra de progreso

# 🔹 Crear ventana oculta para el cuadro de diálogo
root = tk.Tk()
root.withdraw()  # Oculta la ventana principal

# 🔹 Preguntar por la carpeta de origen
carpeta_origen = simpledialog.askstring(
    "Seleccionar Carpeta",
    "Ingrese el nombre de la carpeta a copiar:",
    parent=root
)

if not carpeta_origen:
    print("❌ No ingresaste ninguna carpeta. Saliendo...")
    exit(1)

# 🔹 Verificar si la carpeta de origen existe
if not os.path.exists(carpeta_origen):
    print(f"❌ Error: No se encontró la carpeta '{carpeta_origen}'.")
    exit(1)

# 🔹 Definir la carpeta de destino con nomenclatura (NOMBRE_ORIGEN)_kiuwan
destino_path = f"{carpeta_origen}_kiuwan"

# 🔹 Crear la carpeta de destino si no existe
os.makedirs(destino_path, exist_ok=True)

# 🔹 Archivo de log dentro de la carpeta de destino
log_path = os.path.join(destino_path, "cambios.log")

# 🔹 Obtener lista de todos los archivos dentro de la carpeta y subcarpetas
archivos_a_copiar = []
for root_dir, _, files in os.walk(carpeta_origen):
    for file in files:
        archivos_a_copiar.append(os.path.join(root_dir, file))  # Ruta completa de cada archivo

if not archivos_a_copiar:
    print("📌 No hay archivos en la carpeta de origen para copiar.")
    exit(0)

# 🔹 Copiar archivos y registrar en log
with open(log_path, "w", encoding="utf-8") as log_file:

    def copiar_archivo(archivo):
        base_nombre = os.path.basename(archivo)
        destino = os.path.join(destino_path, base_nombre)

        # Si el archivo ya existe, agregar un número incremental
        contador = 1
        while os.path.exists(destino):
            nombre, extension = os.path.splitext(base_nombre)
            destino = os.path.join(destino_path, f"{nombre}_{contador}{extension}")
            contador += 1

        shutil.copy2(archivo, destino)
        log_file.write(f"✅ Copiado: {archivo} → {os.path.basename(destino)}\n")
        return f"✅ {archivo} → {os.path.basename(destino)}"

    # 🔹 Mostrar barra de progreso
    print("\n📌 Copiando archivos:")
    for archivo in tqdm(archivos_a_copiar, desc="Progreso"):
        print(copiar_archivo(archivo))

print(f"\n📁 Todos los archivos han sido copiados en '{destino_path}' sin estructura de carpetas.")
print(f"📜 Se ha guardado un registro en '{log_path}'.")
