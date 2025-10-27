#!/usr/bin/env python3
import sys
import subprocess
import re

# Check argc
if len(sys.argv) != 3:
    print("Uso: ./gen-2.py <fichero-entrada> <fichero-salida>")
    sys.exit(1)

infile = sys.argv[1]
outfile = sys.argv[2]


# Read and validate infile
try:
    with open(infile, "r") as f:
        print(f"Leyendo {infile}...")
        lines = [l.strip() for l in f if l.strip()]

    if len(lines) < 3:
        print(f"Error: el fichero '{infile}' está incompleto.")
        sys.exit(1)

    # First line:
    # n: Buses
    # m: Time slots
    # u: Workshops
    try:
        n, m, u = map(int, lines[0].split())
    
    # Case: not int
    except ValueError:
        print("Error: Los parámetros de la primera línea deben ser números enteros.")
        sys.exit(1)

    # Additional validations
    if n < 0:
        print("Error: El número de autobuses no puede ser negativo.")
        sys.exit(1)
    if m < 0:
        print("Error: El número de franjas no puede ser negativo.")
        sys.exit(1)
    if u < 0:
        print("Error: El número de talleres no puede ser negativo.")
        sys.exit(1)

    # C matrix (m x m)
    C = []
    # Check C dimensions
    idx = 1
    for i in range(m):
        try:
            row = list(map(float, lines[idx].split()))
        except ValueError: # Case: non-numeric values
            print(f"Error: La fila {i+1} de C contiene elementos no numéricos.")
            sys.exit(1)
        for j in range(len(row)): # Case: negative parameter
            if row[j] < 0:
                print(f"Error: La posición [{i+1}, {j+1}] de C contiene un elemento negativo.")
                sys.exit(1)
       
        if len(row) != m: # Case: bad dimensions
            print(f"Error: la fila {i+1} de C no tiene {m} columnas.")
            sys.exit(1)
        C.append(row)
        idx += 1

    # Validate the symetry of C
    for i in range(m):
        for j in range(m):
            if C[i][j] != C[j][i]:
                print(f"Error: C no es simétrica en posición ({i+1},{j+1}).")
                sys.exit(1)



    # O matrix (u x n)
    O = []
    
    # Check O dimensions
    for i in range(u):
        try:
            row = list(map(int, lines[idx].split()))
        except ValueError:
            print(f"Error: la fila {i+1} de O contiene elementos no numéricos.")
            sys.exit(1)
        if len(row) != n:
            print(f"Error: la fila {i+1} de O no tiene {n} columnas.")
            sys.exit(1)

        # Make sure it's binary
        if any(v not in (0, 1) for v in row):
            print("Error: la matriz O debe ser binaria (0/1).")
            sys.exit(1)
        O.append(row)
        idx += 1

# Case: infile not found
except FileNotFoundError:
    print(f"Error: el fichero '{infile}' no existe.")
    sys.exit(1)


# Generate .dat file
try:
    with open(outfile, "w") as f:
        # Sets
        f.write("# --- Conjuntos ---\n")
        f.write(f"set AUTOBUSES := {' '.join([f'A{i+1}' for i in range(m)])};\n")
        f.write(f"set TALLERES := {' '.join([f'T{i+1}' for i in range(u)])};\n")
        f.write(f"set FRANJAS := {' '.join([f'S{i+1}' for i in range(n)])};\n\n")

        # Parameter c
        f.write("# --- Parámetro de coincidencia de pasajeros (c[i,j]) ---\n")
        f.write("param c:\n")
        # Header
        f.write("     " + "  ".join([f"A{i+1}" for i in range(m)]) + " :=\n")
        for i in range(m):
            row = "  ".join(str(int(C[i][j])) if C[i][j].is_integer() else str(C[i][j]) for j in range(m))
            f.write(f"A{i+1}  {row}\n")
        f.write(";\n\n")

        # Parameter o
        f.write("# --- Disponibilidad de franjas por taller (o[s,t]) ---\n")
        f.write("param o:\n")
        f.write("      " + "  ".join([f"T{i+1}" for i in range(u)]) + " :=\n")
        for s in range(n):
            row = "  ".join(str(O[t][s]) for t in range(u))
            f.write(f"S{s+1}   {row}\n")
        f.write(";\n")

    print(f"Fichero de datos '{outfile}' generado correctamente.")

# Case: writing error
except IOError as e:
    print(f"Error al escribir '{outfile}': {e}")
    sys.exit(1)


# Run GLPK
try:
    print("Ejecutando glpsol...")
    result = subprocess.run(
        ["glpsol", "--model", "parte-2-2.mod", "--data", outfile, "-o", "output2.out"],
        capture_output=True,
        text=True,
        check=True,
    )
# Case: .mod not found
except subprocess.CalledProcessError as e:
    print(f"\nError: 'glpsol' terminó con un código de error ({e.returncode}).")
    print("Revisa que el fichero del modelo 'parte-2-1.mod' existe y es correcto.")
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

with open("output2.out", "r") as f:
    out = f.read()

# Objective value (min z)
mobj = re.search(r"Objective:\s+\w+\s+=\s+([0-9eE.+-]+)", out)
if mobj:
    objective_value = float(mobj.group(1))

# Rows, cols
mrows = re.search(r"Rows:\s+(\d+)", out)
mcols = re.search(r"Columns:\s+(\d+)", out)
if mrows:
    rows = int(mrows.group(1))
if mcols:
    cols = int(mcols.group(1))

# Robust pattern: only strictly 1's (no 0's)
pattern = re.compile(r"[xX]\[(A\d+),(S\d+),(T\d+)\].*?([0-9\.\-Ee]+)")
for m in pattern.finditer(out):
    a, s, t, val = m.groups()
    try:
        v = float(val)
        if abs(v - 1.0) < 1e-6:
            assignments[a] = (s, t)
    except ValueError:
        continue


# Print results
print("="*25, "RESULTADOS", "="*25)
print(f"Objetivo óptimo: {objective_value}, Variables: {cols}, Restricciones: {rows}\n")

if assignments:
    for a in sorted(assignments.keys()):
        s, t = assignments[a]
        print(f"Autobús {a} → Franja {s} en Taller {t}")

# Case: no assignations
else:
    print("No se encontraron asignaciones X=1 en la solución.")

print("="*62)
# More detailed info
print("Para más detalles, consulta el fichero output.out")

