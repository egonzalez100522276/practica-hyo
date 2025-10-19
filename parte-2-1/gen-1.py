#!/usr/bin/python3
import sys
import os
import re
import subprocess

if len(sys.argv) != 3:
    print("Use: ./gen-1.py <fichero-entrada> <fichero-salida>")
    sys.exit(1)

infile = sys.argv[1]
outfile = sys.argv[2]

try:
    # Read data from infile
    with open(infile, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    # Case: incomplete file
    if len(lines) < 4:
        print(f"Error: El fichero de entrada '{infile}' está incompleto. Se esperan al menos 4 líneas.")
        sys.exit(1)

    # Parse data
    try:
        n, m = map(int, lines[0].split())
        kd, kp = map(float, lines[1].split())
        d = list(map(float, lines[2].split(",")))
        p = list(map(float, lines[3].split(",")))

    # Error handling
    except (ValueError, IndexError):
        print(f"Error: Formato de datos incorrecto en el fichero de entrada '{infile}'.")
        sys.exit(1)

# Case: file not found
except FileNotFoundError:
    print(f"Error: El fichero de entrada '{infile}' no existe.")
    sys.exit(1)
except IOError as e:
    print(f"Error: No se pudo leer el fichero de entrada '{infile}': {e}")
    sys.exit(1)

try:
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
except IOError as e:
    print(f"Error: No se pudo escribir en el fichero de salida '{outfile}': {e}")
    sys.exit(1)

# El resto del script se puede encapsular en una función o continuar aquí.
# Por simplicidad, lo dejamos en el flujo principal.

print(f"Fichero de datos '{outfile}' generado correctamente.")
print("Ejecutando glpsol...")

# Solve with GLPK, capturing output to hide it from the terminal
try:
    result = subprocess.run(
        ["glpsol", "--model", "parte-2-1.mod", "--data", outfile, "-o", "output.out"],
        capture_output=True,
        text=True,
        check=True  # This will raise an exception if glpsol fails
    )
except FileNotFoundError:
    print("\nError: El comando 'glpsol' no se encontró.")
    print("Comprueba que GLPK está instalado y que 'glpsol' está en el PATH del sistema.")
    sys.exit(1)
except subprocess.CalledProcessError as e:
    print(f"\nError: 'glpsol' terminó con un código de error ({e.returncode}).")
    print("Revisa que el fichero del modelo 'parte-2-1.mod' existe y es correcto.")
    print("Salida de error de glpsol:")
    print(e.stderr)
    sys.exit(1)


# Parse result and print it
objective_value = None
variables_count = None
constraints_count = None
assignments = {}
try:
    # Parse the result
    with open("output.out", "r") as f:
        content = f.read()
        
        # Objective value
        obj_match = re.search(r"Objective:\s+\w+\s+=\s+([0-9eE.+-]+)", content)
        if obj_match:
            objective_value = float(obj_match.group(1))
        
        # Number of constraints and variables
        rows_match = re.search(r"Rows:\s+(\d+)", content)
        if rows_match:
            constraints_count = int(rows_match.group(1))
        cols_match = re.search(r"Columns:\s+(\d+)", content)
        if cols_match:
            variables_count = int(cols_match.group(1))
        
        # Variable assignments
        # ej: 1 x[a1,f1] * 1 0 1
        for match in re.finditer(r"x\[(a\d+),(f\d+)\]\s+\*\s+1", content):
            bus, franja = match.groups()
            assignments[bus] = franja
except FileNotFoundError:
    print("Error: El fichero de resultados 'output.out' no fue generado por glpsol.")
    sys.exit(1)

print("Ejecución de glpsol finalizada.\n")


# Print the results
print("="*25, "RESULTADOS", "="*25, "\n")

print(f"Coste total: {objective_value}, Variables: {variables_count}, Restricciones: {constraints_count}")

# Bus assignments calculations
all_buses = {f'a{i+1}' for i in range(m)}
assigned_buses = set(assignments.keys())
unassigned_buses = all_buses - assigned_buses


for bus, franja in sorted(assignments.items()):
    print(f"Autobús {bus} asignado a franja {franja}")

for bus in sorted(list(unassigned_buses)):
    print(f"Autobús {bus} sin asignar")

print("\n" + "="*62)
# More detailed info
print("Para más detalles, consulta el fichero output.out")
