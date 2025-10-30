#!/usr/bin/env python3
import sys
import re
import subprocess
import argparse

parser = argparse.ArgumentParser(description="Genera un fichero .dat para el problema 2.2.1. y lo resuelve con GLPK.")
parser.add_argument("infile", help="Fichero de entrada con los datos del problema.")
parser.add_argument("outfile", help="Fichero .dat de salida que se generará.")
parser.add_argument("--debug", action="store_true", help="Activa el modo de depuración para mostrar más información.")
args = parser.parse_args()

infile = args.infile
outfile = args.outfile

def debug_print(*message):
    if args.debug:
        print(*message)
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
        d = list(map(float, re.findall(r"[0-9.]+", lines[2])))
        p = list(map(float, re.findall(r"[0-9.]+", lines[3])))

        # --- Additional data validations ---
        if n < 0:
            print(f"Error: El número de franjas ({n}) no puede ser negativo.")
            sys.exit(1)
        if m < 0:
            print(f"Error: El número de autobuses ({m}) no puede ser negativo.")
            sys.exit(1)
        
        if kd < 0:
            print(f"Error: La constante kd ({kd}) no puede ser negativa.")
            sys.exit(1)
        if kp < 0:
            print(f"Error: La constante kp ({kp}) no puede ser negativa.")
            sys.exit(1)

        if len(d) != m:
            print(f"Error: El número de valores 'd' ({len(d)}) no coincide con el número de autobuses ({m}).")
            sys.exit(1)

        if len(p) != m:
            print(f"Error: El número de valores 'p' ({len(p)}) no coincide con el número de autobuses ({m}).")
            sys.exit(1)
        
        for i, val in enumerate(d):
            if val < 0:
                print(f"Error: El valor d en la posición {i} ({val}) no puede ser negativo.")
                sys.exit(1)
            if val != int(val):
                print(f"Error: El valor d en la posición {i} ({val}) debe ser un número entero.")
                sys.exit(1)

        for i, val in enumerate(p):
            if val < 0:
                print(f"Error: El valor p en la posición {i} ({val}) no puede ser negativo.")
                sys.exit(1)
            if val != int(val):
                print(f"Error: El valor p en la posición {i} ({val}) debe ser un número entero.")
                sys.exit(1)

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
    # Generate .dat
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

debug_print(f"Fichero de datos '{outfile}' generado correctamente.")
debug_print("Ejecutando glpsol...")

# Solve with GLPK, capturing output to hide it from the terminal
try:
    result = subprocess.run(
        ["glpsol", "--model", "parte-2-1.mod", "--data", outfile, "--output", "output.out"],
        capture_output=True,
        text=True,
        check=False  # We will check the output manually
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

# Check if an optimal solution was found by reading the stdout
debug_print(result.stdout)
if "OPTIMAL LP SOLUTION FOUND" not in result.stdout:
    print("\nError: No se encontró una solución óptima.", file=sys.stderr)
    if "HAS NO PRIMAL FEASIBLE SOLUTION" in result.stdout:
        print("Razón: El problema no tiene una solución factible (es infactible).", file=sys.stderr)
    elif "HAS NO DUAL FEASIBLE SOLUTION" in result.stdout:
        print("Razón: El problema es no acotado.", file=sys.stderr)
    # Exit with an error code so that random-cases-1.py can catch it
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

debug_print("Ejecución de glpsol finalizada.\n")

# Print the results
debug_print("="*25, "RESULTADOS", "="*25, "\n")

print(f"Coste total: {objective_value}, Variables: {variables_count}, Restricciones: {constraints_count}")

# Bus assignments calculations
all_buses = {f'a{i+1}' for i in range(m)}
assigned_buses = set(assignments.keys())
unassigned_buses = all_buses - assigned_buses


for bus, franja in sorted(assignments.items()):
    print(f"Autobús {bus} asignado a franja {franja}")

for bus in sorted(list(unassigned_buses)):
    print(f"Autobús {bus} sin asignar")

debug_print("="*62)
# More detailed info
debug_print("Para más detalles, consulta el fichero output.out")
