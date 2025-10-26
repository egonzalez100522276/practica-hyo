#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
import subprocess

if len(sys.argv) != 3:
    print("Uso: ./gen-basico.py <fichero-entrada.in> <fichero-salida.dat>")
    sys.exit(1)

infile = sys.argv[1]
outfile = sys.argv[2]

# ---------- 1. Leer fichero de entrada ----------
with open(infile, "r", encoding="utf-8") as f:
    lines = [l.strip() for l in f if l.strip()]

n_t, n_a = map(int, lines[0].split())
COST = []
for i in range(1, 1 + n_t):
    fila = list(map(float, lines[i].split()))
    if len(fila) != n_a:
        print(f"Error: la fila {i} no tiene {n_a} valores.")
        sys.exit(1)
    COST.append(fila)

# ---------- 2. Generar fichero .dat ----------
with open(outfile, "w", encoding="utf-8") as f:
    f.write("# --- Conjuntos ---\n")
    f.write("set TALLER := " + " ".join(f"T{i+1}" for i in range(n_t)) + ";\n")
    f.write("set AUTOBUS := " + " ".join(f"A{j+1}" for j in range(n_a)) + ";\n\n")
    f.write("# --- Parámetro de costes ---\n")
    f.write("param COST : " + " ".join(f"A{j+1}" for j in range(n_a)) + " :=\n")
    for i in range(n_t):
        f.write(f"T{i+1}  " + "  ".join(str(COST[i][j]) for j in range(n_a)) + "\n")
    f.write(";\n")

print(f"Fichero de datos '{outfile}' generado correctamente.")
print("Ejecutando glpsol...")

# ---------- 3. Ejecutar GLPK ----------
proc = subprocess.run(
    ["glpsol", "--model", "p1_hyo.mod", "--data", outfile, "-o", "salida.out"],
    capture_output=True, text=True
)
log = (proc.stdout or "") + "\n" + (proc.stderr or "")

# ---------- 4. Comprobar si hay solución óptima ----------
with open("salida.out", "r", encoding="utf-8", errors="ignore") as f:
    sol = f.read()

if not re.search(r"OPTIMAL", log, re.IGNORECASE) and not re.search(r"OPTIMAL", sol, re.IGNORECASE):
    print("\n===== RESULTADOS =====")
    print("No existe solución óptima (modelo no factible o no alcanzada).")
    print("=======================")
    sys.exit(0)

# ---------- 5. Extraer información ----------
objective = None
rows = None
cols = None

# Buscar en ambos: salida.out y stdout
search_text = sol + "\n" + log

mobj = re.search(r"Objective:\s*\w*\s*=\s*([-+0-9.eE]+)", search_text)
if mobj:
    objective = float(mobj.group(1))

mrows = re.search(r"(Rows|Number of rows):\s*(\d+)", search_text)
mcols = re.search(r"(Columns|Number of columns):\s*(\d+)", search_text)
if mrows:
    rows = int(mrows.group(2))
if mcols:
    cols = int(mcols.group(2))

# ---------- 6. Extraer asignaciones ----------
assignments = []
for m in re.finditer(r"[xX]\[(T\d+),(A\d+)\].*?([\-+0-9.]+)", sol):
    t, a, val = m.groups()
    try:
        if abs(float(val) - 1.0) < 1e-8:
            assignments.append((t, a))
    except:
        continue

# ---------- 7. Mostrar resultados ----------
print("\n===== RESULTADOS =====")
print(f"Objetivo óptimo: {objective}, Variables: {cols}, Restricciones: {rows}\n")

if assignments:
    for t, a in sorted(assignments):
        print(f"Taller {t} ← Autobús {a}")
else:
    print("No se encontraron asignaciones (x=1).")

print("=======================")
