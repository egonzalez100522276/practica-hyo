#!/usr/bin/env python3
import sys
import os
import subprocess

if len(sys.argv) != 3:
    print("Uso: ./gen-1.py <fichero-entrada> <fichero-salida>")
    sys.exit(1)

infile = sys.argv[1]
outfile = sys.argv[2]

# Leer datos del fichero de entrada
with open(infile, 'r') as f:
    lines = [line.strip() for line in f if line.strip()]

n, m = map(int, lines[0].split())
kd, kp = map(float, lines[1].split())
d = list(map(float, lines[2].split()))
p = list(map(float, lines[3].split()))

# Generar el .dat
with open(outfile, 'w') as f:
    f.write(f"set AUTOBUSES := {' '.join([f'a{i+1}' for i in range(m)])};\n")
    f.write(f"set FRANJAS := {' '.join([f's{j+1}' for j in range(n)])};\n\n")
    f.write(f"param kd := {kd};\n")
    f.write(f"param kp := {kp};\n\n")
    f.write("param d :=\n")
    for i in range(m):
        f.write(f" a{i+1} {d[i]}\n")
    f.write(";\n\nparam p :=\n")
    for i in range(m):
        f.write(f" a{i+1} {p[i]}\n")
    f.write(";\n")

# Resolver con GLPK
result = subprocess.run(
    ["glpsol", "--model", "parte-2-1.mod", "--data", outfile],
    capture_output=True, text=True
)

print(result.stdout)