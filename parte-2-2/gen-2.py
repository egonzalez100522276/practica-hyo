#!/usr/bin/env python3
import sys
import subprocess
import re
import argparse

parser = argparse.ArgumentParser(description="Genera un fichero .dat para el problema 2.2.2. y lo resuelve con GLPK.")
parser.add_argument("infile", help="Fichero de entrada con los datos del problema.")
parser.add_argument("outfile", help="Fichero .dat de salida que se generará.")
parser.add_argument("--debug", action="store_true", help="Activa el modo de depuración para mostrar más información.")
args = parser.parse_args()

infile = args.infile
outfile = args.outfile

def debug_print(*message):
    if args.debug:
        print(*message)


# Read and validate infile
try:
    with open(infile, "r", encoding="utf-8") as f:
        debug_print(f"Leyendo {infile}...")
        lines = [l.strip() for l in f if l.strip()]

    if len(lines) < 3:
        print(f"Error: el fichero '{infile}' está incompleto.")
        sys.exit(1)

    # First line: n: Buses, m: Time slots, u: Workshops
    try:
        n, m, u = map(int, lines[0].split())
    except ValueError:
        print("Error: Los parámetros de la primera línea deben ser números enteros.")
        sys.exit(1)

    if n < 0 or m < 0 or u < 0:
        print("Error: Los parámetros no pueden ser negativos.")
        sys.exit(1)

    # C matrix (m x m)
    C = []
    idx = 1
    for i in range(m):
        try:
            row = list(map(float, lines[idx].split()))
        except ValueError:
            print(f"Error: La fila {i+1} de C contiene elementos no numéricos.")
            sys.exit(1)
        if len(row) != m:
            print(f"Error: la fila {i+1} de C no tiene {m} columnas.")
            sys.exit(1)
        if any(v < 0 for v in row):
            print(f"Error: La fila {i+1} de C contiene un elemento negativo.")
            sys.exit(1)
        C.append(row)
        idx += 1

    # Validate symmetry of C
    for i in range(m):
        for j in range(m):
            if C[i][j] != C[j][i]:
                print(f"Error: C no es simétrica en posición ({i+1},{j+1}).")
                sys.exit(1)

    # O matrix (n x u)  ← Cambio: ahora filas = n, columnas = u
    O = []
    for i in range(n):
        try:
            row = list(map(int, lines[idx].split()))
        except ValueError:
            print(f"Error: la fila {i+1} de O contiene elementos no numéricos.")
            sys.exit(1)
        if len(row) != u:
            print(f"Error: la fila {i+1} de O no tiene {u} columnas.")
            sys.exit(1)
        if any(v not in (0,1) for v in row):
            print("Error: la matriz O debe ser binaria (0/1).")
            sys.exit(1)
        O.append(row)
        idx += 1

except FileNotFoundError:
    print(f"Error: el fichero '{infile}' no existe.")
    sys.exit(1)


# Generate .dat file
try:
    with open(outfile, "w", encoding="utf-8") as f:
        # Sets
        f.write("# --- Conjuntos ---\n")
        f.write(f"set AUTOBUSES := {' '.join([f'A{i+1}' for i in range(m)])};\n")
        f.write(f"set TALLERES := {' '.join([f'T{i+1}' for i in range(u)])};\n")
        f.write(f"set FRANJAS := {' '.join([f'S{i+1}' for i in range(n)])};\n\n")

        # Parameter c
        f.write("# --- Parámetro de coincidencia de pasajeros (c[i,j]) ---\n")
        f.write("param c:\n")
        f.write("     " + "  ".join([f"A{i+1}" for i in range(m)]) + " :=\n")
        for i in range(m):
            row = "  ".join(str(int(C[i][j])) if C[i][j].is_integer() else str(C[i][j]) for j in range(m))
            f.write(f"A{i+1}  {row}\n")
        f.write(";\n\n")

        # Parameter o (transposed)
        f.write("# --- Disponibilidad de franjas por taller (o[s,t]) ---\n")
        f.write("param o:\n")
        f.write("      " + "  ".join([f"T{i+1}" for i in range(u)]) + " :=\n")
        for s in range(n):
            row = "  ".join(str(O[s][t]) for t in range(u))
            f.write(f"S{s+1}   {row}\n")
        f.write(";\n")

    debug_print(f"Fichero de datos '{outfile}' generado correctamente.")

except IOError as e:
    print(f"Error al escribir '{outfile}': {e}")
    sys.exit(1)


# Run GLPK
try:
    debug_print("Ejecutando glpsol...")
    result = subprocess.run(
        ["glpsol", "--model", "parte-2-2.mod", "--data", outfile, "-o", "output2.out", "--log", "output2.log"],
        capture_output=True,
        text=True,
        check=True,
    )

except subprocess.CalledProcessError as e:
    print(f"\nError: 'glpsol' terminó con un código de error ({e.returncode}).")
    print("Revisa que el fichero del modelo 'parte-2-2.mod' existe y es correcto.")
    print("Salida de error de glpsol:")
    print(e.stderr)
    sys.exit(1)

except FileNotFoundError:
    print("Error: 'glpsol' no se encontró. Instala GLPK o añade su ruta al PATH.")
    sys.exit(1)


# Read result (Checking assignation detection)
objective_value = None
rows = cols = None
assignments = {}

with open("output2.out", "r", encoding="utf-8") as f:
    out = f.read()

# Check if an optimal solution was found
if "OPTIMAL SOLUTION FOUND" not in result.stdout:
    print("Error: No se encontró una solución óptima.", file=sys.stderr)
    if "HAS NO PRIMAL FEASIBLE SOLUTION" in result.stdout:
        print("Razón: El problema no tiene una solución factible (es infactible).", file=sys.stderr)
    elif "HAS NO DUAL FEASIBLE SOLUTION" in result.stdout:
        print("Razón: El problema es no acotado.", file=sys.stderr)
    sys.exit(1)

mobj = re.search(r"Objective:\s+\w+\s+=\s+([0-9eE.+-]+)", out)
if mobj:
    objective_value = float(mobj.group(1))

mrows = re.search(r"Rows:\s+(\d+)", out)
mcols = re.search(r"Columns:\s+(\d+)", out)
if mrows:
    rows = int(mrows.group(1))
if mcols:
    cols = int(mcols.group(1))

pattern = re.compile(r"[xX]\[(A\d+),(S\d+),(T\d+)\].*?([0-9\.\-Ee]+)")
for m in pattern.finditer(out):
    a, s, t, val = m.groups()
    try:
        v = float(val)
        if abs(v - 1.0) < 1e-6:
            assignments[a] = (s, t)
    except ValueError:
        continue

debug_print("="*25, "RESULTADOS", "="*25)
print(f"Coste total óptimo: {objective_value}, Variables: {cols}, Restricciones: {rows}\n")

if assignments:
    for a in sorted(assignments.keys()):
        s, t = assignments[a]
        print(f"Autobús {a} → Franja {s} en Taller {t}")
else:
    print("No se encontraron asignaciones X=1 en la solución.")

debug_print("="*62)
debug_print("Para más detalles, consulta el fichero output.out")
