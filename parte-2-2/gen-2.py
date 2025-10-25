#!/usr/bin/env python3
import sys
import subprocess
import re

if len(sys.argv) != 3:
    print("Uso: ./gen-2.py <fichero-entrada> <fichero-salida>")
    sys.exit(1)

infile = sys.argv[1]
outfile = sys.argv[2]


# Leer y validar el fichero de entrada
try:
    with open(infile, "r") as f:
        lines = [l.strip() for l in f if l.strip()]

    if len(lines) < 3:
        print(f"Error: el fichero '{infile}' está incompleto.")
        sys.exit(1)

    # Primera línea: n, m, u
    n, m, u = map(int, lines[0].split())

    # Matriz c (m x m)
    C = []
    idx = 1
    for i in range(m):
        fila = list(map(float, lines[idx].split()))
        if len(fila) != m:
            print(f"Error: la fila {i+1} de C no tiene {m} columnas.")
            sys.exit(1)
        C.append(fila)
        idx += 1

    # Matriz o (u x n)
    O = []
    for i in range(u):
        fila = list(map(int, lines[idx].split()))
        if len(fila) != n:
            print(f"Error: la fila {i+1} de O no tiene {n} columnas.")
            sys.exit(1)
        if any(v not in (0, 1) for v in fila):
            print("Error: la matriz O debe ser binaria (0/1).")
            sys.exit(1)
        O.append(fila)
        idx += 1

    # Validar simetría de C
    for i in range(m):
        for j in range(m):
            if C[i][j] != C[j][i]:
                print(f"Error: C no es simétrica en posición ({i+1},{j+1}).")
                sys.exit(1)

except FileNotFoundError:
    print(f"Error: el fichero '{infile}' no existe.")
    sys.exit(1)


# Generar el fichero .dat
try:
    with open(outfile, "w") as f:
        f.write("# --- Conjuntos ---\n")
        f.write(f"set AUTOBUSES := {' '.join([f'A{i+1}' for i in range(m)])};\n")
        f.write(f"set TALLERES := {' '.join([f'T{i+1}' for i in range(u)])};\n")
        f.write(f"set FRANJAS := {' '.join([f'S{i+1}' for i in range(n)])};\n\n")

        # Parámetro c
        f.write("# --- Parámetro de coincidencia de pasajeros (c[i,j]) ---\n")
        f.write("param c:\n")
        # Cabecera
        f.write("     " + "  ".join([f"A{i+1}" for i in range(m)]) + " :=\n")
        for i in range(m):
            fila = "  ".join(str(int(C[i][j])) if C[i][j].is_integer() else str(C[i][j]) for j in range(m))
            f.write(f"A{i+1}  {fila}\n")
        f.write(";\n\n")

        # Parámetro o
        f.write("# --- Disponibilidad de franjas por taller (o[s,t]) ---\n")
        f.write("param o:\n")
        f.write("      " + "  ".join([f"T{i+1}" for i in range(u)]) + " :=\n")
        for s in range(n):
            fila = "  ".join(str(O[t][s]) for t in range(u))
            f.write(f"S{s+1}   {fila}\n")
        f.write(";\n")

    print(f"Fichero de datos '{outfile}' generado correctamente.")
except IOError as e:
    print(f"Error al escribir '{outfile}': {e}")
    sys.exit(1)


# Ejecutar GLPK
print("Ejecutando glpsol...")

try:
    result = subprocess.run(
        ["glpsol", "--model", "parte-2-2.mod", "--data", outfile, "-o", "output2.out"],
        capture_output=True,
        text=True,
        check=True,
    )
except subprocess.CalledProcessError as e:
    print("Error: GLPK terminó con error.")
    print(e.stdout)
    sys.exit(1)
except FileNotFoundError:
    print("Error: 'glpsol' no se encontró. Instala GLPK o añade su ruta al PATH.")
    sys.exit(1)


# Leer resultados (corrigiendo detección de asignaciones)

objective_value = None
rows = cols = None
assignments = {}

with open("output2.out", "r") as f:
    out = f.read()

# Valor del objetivo
mobj = re.search(r"Objective:\s+\w+\s+=\s+([0-9eE.+-]+)", out)
if mobj:
    objective_value = float(mobj.group(1))

mrows = re.search(r"Rows:\s+(\d+)", out)
mcols = re.search(r"Columns:\s+(\d+)", out)
if mrows:
    rows = int(mrows.group(1))
if mcols:
    cols = int(mcols.group(1))

# Patrón robusto: solo valores estrictamente 1 (no 0)
patron = re.compile(r"[xX]\[(A\d+),(S\d+),(T\d+)\].*?([0-9\.\-Ee]+)")
for m in patron.finditer(out):
    a, s, t, val = m.groups()
    try:
        v = float(val)
        if abs(v - 1.0) < 1e-6:
            assignments[a] = (s, t)
    except ValueError:
        continue


# Imprimir resultados

print("\n===== RESULTADOS =====")
print(f"Objetivo óptimo: {objective_value}, Variables: {cols}, Restricciones: {rows}\n")

if assignments:
    for a in sorted(assignments.keys()):
        s, t = assignments[a]
        print(f"Autobús {a} → Franja {s} en Taller {t}")
else:
    print("No se encontraron asignaciones X=1 en la solución.")

print("=======================")

