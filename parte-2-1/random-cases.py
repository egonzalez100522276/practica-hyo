#!/usr/bin/env python3
import random
import argparse
import subprocess

parser = argparse.ArgumentParser(description="Genera un fichero de entrada aleatorio para el problema 2.2.1.")
parser.add_argument("outfile", type = str, nargs="?", default="random_case.in", help="Fichero de salida que se generará con los datos aleatorios.")
parser.add_argument("--seed", type=int, default=None, help="Semilla para el generador aleatorio.")
args = parser.parse_args()

# Generate random seed if not provided
if args.seed is not None:
    random.seed(args.seed)

# Generate random number of slots and buses
n = random.randint(0, 15)  # Slots
m = random.randint(0, 15)  # Buses

# Generate kd and kp constants (positive floats)
kd = round(random.uniform(0.1, 10.0), 2)
kp = round(random.uniform(0.1, 10.0), 2)

# generate d and p lists with random positive values
d = [round(random.uniform(1.0, 50.0), 2) for _ in range(m)]
p = [round(random.uniform(1.0, 50.0), 2) for _ in range(m)]

# Write outfile
with open(args.outfile, 'w') as f:
    f.write(f"{n} {m}\n")
    f.write(f"{kd} {kp}\n")
    f.write(", ".join(map(str, d)) + "\n")
    f.write(", ".join(map(str, p)) + "\n")

print(f"Fichero '{args.outfile}' generado con {n} franjas y {m} autobuses.")

result = subprocess.run(
        ["python3", "gen-1.py", args.outfile, "random-output.dat"],
        capture_output=True,
        text=True,
        check=True  # This will raise an exception if glpsol fails
    )

print(result.stdout)
