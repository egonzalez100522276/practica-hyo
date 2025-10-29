#!/usr/bin/env python3
import random
import argparse
import subprocess
import time
import re
import csv
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

parser = argparse.ArgumentParser(description="Genera varios ficheros de entrada aleatorios y recoge estadísticas.")
parser.add_argument("num_cases", type=int, nargs="?", default=10, help="Número de casos aleatorios")
parser.add_argument("output_csv", type=str, nargs="?", default="stats.csv", help="CSV donde se guardarán las estadísticas")
parser.add_argument("--seed", type=int, default=None, help="Semilla para el generador aleatorio")
parser.add_argument("--keep-files", action="store_true", help="No borrar los ficheros temporales generados")
args = parser.parse_args()

if args.seed is not None:
    random.seed(args.seed)

csv_path = Path(args.output_csv)
if not csv_path.exists():
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["case_file","n","m","time_s","variables","constraints"])

for case_idx in range(1, args.num_cases + 1):
    # Generar caso aleatorio
    n = random.randint(0, 100)
    m = random.randint(1, 100)
    kd = round(random.uniform(0.1, 10.0), 2)
    kp = round(random.uniform(0.1, 10.0), 2)
    d = [round(random.uniform(1.0, 50.0), 2) for _ in range(m)]
    p = [round(random.uniform(1.0, 50.0), 2) for _ in range(m)]

    case_file = f"random_case_{case_idx}.in"
    output_dat = f"random_output_{case_idx}.dat"

    with open(case_file, 'w') as f:
        f.write(f"{n} {m}\n")
        f.write(f"{kd} {kp}\n")
        f.write(", ".join(map(str, d)) + "\n")
        f.write(", ".join(map(str, p)) + "\n")

    print(f"[{case_idx}] Fichero '{case_file}' generado con {n} franjas y {m} autobuses.")

    # Medir tiempo de ejecución
    start_time = time.perf_counter()
    try:
        result = subprocess.run(
            ["python3", "gen-1.py", case_file, output_dat],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar gen-1.py en el caso {case_idx}")
        print(e.stderr)
        # Eliminar archivos si hay error
        if not args.keep_files:
            for f_ in (case_file, output_dat):
                try: os.remove(f_)
                except FileNotFoundError: pass
        continue
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    # Parsear variables y restricciones
    stdout = result.stdout
    vars_match = re.search(r"Variables:\s*(\d+)", stdout)
    rows_match = re.search(r"Restricciones:\s*(\d+)", stdout)
    num_vars = int(vars_match.group(1)) if vars_match else None
    num_constraints = int(rows_match.group(1)) if rows_match else None

    print(f"[{case_idx}] Tiempo: {elapsed_time:.4f}s, Variables: {num_vars}, Restricciones: {num_constraints}")

    # Guardar estadísticas
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([case_file, n, m, elapsed_time, num_vars, num_constraints])

    # 🧹 Borrar archivos temporales si no se pide conservarlos
    if not args.keep_files:
        for f_ in (case_file, output_dat):
            try:
                os.remove(f_)
            except FileNotFoundError:
                pass
# --- Crear gráfica variables vs tiempo con línea ---

# Leer CSV
df = pd.read_csv("stats.csv")

# --- Gráfica 1: Variables vs Tiempo ---
df_sorted_vars = df.sort_values(by='variables')
plt.figure(figsize=(8,6))
plt.plot(df_sorted_vars['variables'], df_sorted_vars['time_s'],
         marker='o', color='blue', linestyle='-')
plt.xlabel("Número de variables")
plt.ylabel("Tiempo de ejecución (s)")
plt.title("Tiempo de ejecución vs Número de variables")
plt.grid(True, linestyle='--', alpha=0.7)
plt.savefig("variables_vs_tiempo.png", dpi=300, bbox_inches='tight')
plt.show()

# --- Gráfica 2: Variables + Restricciones vs Tiempo ---
df['vars_plus_constraints'] = df['variables'] + df['constraints']
df_sorted_total = df.sort_values(by='vars_plus_constraints')
plt.figure(figsize=(8,6))
plt.plot(df_sorted_total['vars_plus_constraints'], df_sorted_total['time_s'],
         marker='o', color='orange', linestyle='-')
plt.xlabel("Número de variables + número de restricciones")
plt.ylabel("Tiempo de ejecución (s)")
plt.title("Tiempo de ejecución vs Variables + Restricciones")
plt.grid(True, linestyle='--', alpha=0.7)
plt.savefig("vars_plus_constraints_vs_tiempo.png", dpi=300, bbox_inches='tight')
plt.show()

# Gráfica Variables vs Restricciones
plt.figure(figsize=(8,6))
plt.scatter(df['variables'], df['constraints'], c='green', s=80, alpha=0.7)
plt.xlabel("Número de variables")
plt.ylabel("Número de restricciones")
plt.title("Relación entre Variables y Restricciones por caso")
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig("variables_vs_restricciones.png", dpi=300, bbox_inches='tight')
# Borrar el archivo de estadísticas
os.remove("stats.csv")


