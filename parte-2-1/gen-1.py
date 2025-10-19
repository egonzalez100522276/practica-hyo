#!/usr/bin/python3
import sys
import os
import subprocess

if len(sys.argv) != 3:
    print("Use: ./gen-1.py <fichero-entrada> <fichero-salida>")
    sys.exit(1)

infile = sys.argv[1]
outfile = sys.argv[2]

# Leer datos del fichero de entrada
with open(infile, 'r') as f:
    lines = [line.strip() for line in f if line.strip()]

n, m = map(int, lines[0].split())
kd, kp = map(float, lines[1].split())
d = list(map(float, lines[2].split(",")))
p = list(map(float, lines[3].split(",")))

# Generar el .dat
with open(outfile, 'w') as f:
    # add sets
    f.write(f"set AUTOBUSES := {' '.join([f'a{i+1}' for i in range(m)])};\n")
    f.write(f"set FRANJAS := {' '.join([f'f{j+1}' for j in range(n)])};\n\n")
    
    # add kd and kp constants
    f.write(f"param kd := {kd};\n")
    f.write(f"param kp := {kp};\n\n")

    # add d[i]
    f.write("param d :=\n")
    for i in range(m):
        f.write(f" a{i+1} {d[i]}\n")
    
    # add p[i]
    f.write(";\n\nparam p :=\n")
    for i in range(m):
        f.write(f" a{i+1} {p[i]}\n")
    f.write(";\n")

# Solve with GLPK
result = subprocess.run(
    ["glpsol", "--model", "parte-2-1.mod", "--data", outfile, "-o", "output.out"],
    capture_output=True, text=True
)

# Procesar la salida para mostrar solo información relevante
output_lines = result.stdout.split('\n')
solution_found = False
variables_count = 0
constraints_count = 0
objective_value = 0.0

print("=" * 60)
print("OPTIMAL SOLUTION FOUND")
print("=" * 60)

for i, line in enumerate(output_lines):
    line = line.strip()
    
    # Buscar información clave
    if "INTEGER OPTIMAL" in line:
        solution_found = True
        print(f"Status: {line}")
    
    elif "Objective:" in line and "OverallCost" in line:
        # Extraer valor de la función objetivo
        parts = line.split()
        for part in parts:
            if part.replace('.', '').isdigit():
                objective_value = float(part)
                break
    
    elif "Rows:" in line:
        parts = line.split()
        constraints_count = int(parts[1])
    
    elif "Columns:" in line:
        parts = line.split()
        variables_count = int(parts[1])
    
    elif "=== OPTIMAL SOLUTION ===" in line:
        # Mostrar desde aquí hasta el final de la solución
        print("\n" + "=" * 40)
        for j in range(i, min(i + 20, len(output_lines))):
            sol_line = output_lines[j].strip()
            if sol_line and not sol_line.startswith("Model has been successfully processed"):
                print(sol_line)
        break

# Si no encontramos el formato esperado, mostrar información básica
if solution_found:
    print(f"\nSummary:")
    print(f"Objective value: {objective_value}")
    print(f"Variables: {variables_count}")
    print(f"Constraints: {constraints_count}")
else:
    # Mostrar salida completa si no se pudo parsear
    print("Full output:")
    print(result.stdout)

if result.stderr:
    print("\nErrors:")
    print(result.stderr)

print("=" * 60)