#!/usr/bin/python3
import sys
import os
import subprocess
import re

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
    capture_output=True,
    text=True
)

# Parse result and print it
objective_value = None
variables_count = None
constraints_count = None
assignments = {}

# Parse the result
with open("output.out", "r") as f:
    lines = f.readlines()
    in_variable_section = False
    for line in lines:
        line = line.strip()
        if not line:
            in_variable_section = False
            continue

        # Objective value
        if line.startswith("Objective:"):
            objective_value = float(line.split()[3])
        
        # Number of constraints
        elif line.startswith("Rows:"):
            constraints_count = int(line.split()[1])
        
        # Number of variables
        elif line.startswith("Columns:"):
            variables_count = int(line.split()[1])
        
        # "Variable section" is the last part of the .out file where the variables values are shown
        elif "Column name" in line:
            in_variable_section = True
        elif in_variable_section:
            # use regex to parse the variable line
            # ej: 1 x[a1,f1] * 1 0 1
            match = re.match(r"\s*\d+\s+x\[(a\d+),(f\d+)\]\s+\*\s+1", line)
            if match:
                bus, franja = match.groups()
                assignments[bus] = franja

# Print the results
print(f"Coste total: {objective_value}, Variables: {variables_count}, Restricciones: {constraints_count}")

# Bus assignments calculations
all_buses = {f'a{i+1}' for i in range(m)}
assigned_buses = set(assignments.keys())
unassigned_buses = all_buses - assigned_buses


for bus, franja in sorted(assignments.items()):
    print(f"Autobús {bus} asignado a franja {franja}")

for bus in sorted(list(unassigned_buses)):
    print(f"Autobús {bus} sin asignar")

# More detailed info
print("Para más detalles, consulta el fichero output.out")