#!/usr/bin/env python3
import random
import argparse
import subprocess
import time
import re
import csv
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

parser = argparse.ArgumentParser(description="Generate several random input files and collect statistics for model 2.2.")
parser.add_argument("num_cases", type=int, nargs="?", default=10, help="Number of random cases to generate.")
parser.add_argument("output_csv", type=str, nargs="?", default="stats2.csv", help="CSV file to store statistics.")
parser.add_argument("--seed", type=int, default=None, help="Seed for the random number generator.")
parser.add_argument("--keep-files", action="store_true", help="Do not delete temporary files generated.")
args = parser.parse_args()

if args.seed is not None:
    random.seed(args.seed)

csv_path = Path(args.output_csv)
# Ensure the old stats file is removed before starting
if csv_path.exists():
    os.remove(csv_path)

if not csv_path.exists():
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["case_file", "n_slots", "m_buses", "u_workshops", "time_s", "variables", "constraints"])

for case_idx in range(1, args.num_cases + 1):
    # Generate random case
    n = random.randint(1, 10)  # Number of time slots
    m = random.randint(1, 10)  # Number of buses
    u = random.randint(1, 10)  # Number of workshops

    # Generate binary O matrix (n x u)
    O = [[random.randint(0, 1) for _ in range(u)] for _ in range(n)]

    # Ensure the problem is solvable: number of buses must not exceed total available slots.
    total_available_slots = sum(sum(row) for row in O)
    if total_available_slots == 0: # Avoid unsolvable cases where no slots are available
        O[random.randint(0, n-1)][random.randint(0, u-1)] = 1
        total_available_slots = 1
    if m > total_available_slots:
        m = total_available_slots # Adjust number of buses to be solvable

    # Generate symmetric C matrix (m x m) for the (possibly adjusted) number of buses
    C = [[0.0] * m for _ in range(m)]
    for i in range(m):
        for j in range(i, m):
            if i == j:
                C[i][j] = 0
            else:
                val = round(random.uniform(1.0, 100.0), 2)
                C[i][j] = val
                C[j][i] = val

    case_file = f"random_case_{case_idx}.in"
    output_dat = f"random_output_{case_idx}.dat"

    with open(case_file, 'w') as f:
        f.write(f"{n} {m} {u}\n")
        for row in C:
            f.write(" ".join(map(str, row)) + "\n")
        for row in O:
            f.write(" ".join(map(str, row)) + "\n")

    print(f"[{case_idx}] File '{case_file}' generated with n={n} slots, m={m} buses, u={u} workshops.")

    # Measure execution time
    start_time = time.perf_counter()
    try:
        result = subprocess.run(
            ["python3", "gen-2.py", case_file, output_dat],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error executing gen-2.py on case {case_idx}")
        print(e.stderr)
        # Delete files on error
        if not args.keep_files:
            for f_ in (case_file, output_dat):
                try: os.remove(f_)
                except FileNotFoundError: pass
        continue
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    # Parse variables and constraints
    stdout = result.stdout
    vars_match = re.search(r"Variables:\s*(\d+)", stdout, re.IGNORECASE)
    rows_match = re.search(r"Restricciones:\s*(\d+)", stdout, re.IGNORECASE)
    num_vars = int(vars_match.group(1)) if vars_match else None
    num_constraints = int(rows_match.group(1)) if rows_match else None

    print(f"[{case_idx}] Time: {elapsed_time:.4f}s, Variables: {num_vars}, Constraints: {num_constraints}")

    # Save statistics
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([case_file, n, m, u, elapsed_time, num_vars, num_constraints])

    # 🧹 Clean up temporary files if not requested to keep them
    if not args.keep_files:
        for f_ in (case_file, output_dat):
            try:
                os.remove(f_)
            except FileNotFoundError:
                pass
# --- Create plots ---

# Read CSV
df = pd.read_csv(csv_path)

# --- Plot 1: Variables vs Time ---
df_sorted_vars = df.sort_values(by='variables')
plt.figure(figsize=(8,6))
plt.plot(df_sorted_vars['variables'], df_sorted_vars['time_s'],
         marker='o', color='blue', linestyle='-')
plt.xlabel("Number of variables")
plt.ylabel("Execution Time (s)")
plt.title("Execution Time vs. Number of Variables")
plt.grid(True, linestyle='--', alpha=0.7)
plt.savefig("variables_vs_time_p2.png", dpi=300, bbox_inches='tight')
plt.show()

# --- Plot 2: Constraints vs Time ---
df_sorted_constraints = df.sort_values(by='constraints')
plt.figure(figsize=(8,6))
plt.plot(df_sorted_constraints['constraints'], df_sorted_constraints['time_s'],
         marker='o', color='orange', linestyle='-')
plt.xlabel("Number of constraints")
plt.ylabel("Execution Time (s)")
plt.title("Execution Time vs. Number of Constraints")
plt.grid(True, linestyle='--', alpha=0.7)
plt.savefig("constraints_vs_time_p2.png", dpi=300, bbox_inches='tight')
plt.show()

# Plot 3: Variables vs Constraints
plt.figure(figsize=(8,6))
plt.scatter(df['variables'], df['constraints'], c='green', s=80, alpha=0.7)
plt.xlabel("Number of variables")
plt.ylabel("Number of constraints")
plt.title("Relationship between Variables and Constraints per Case")
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig("variables_vs_constraints_p2.png", dpi=300, bbox_inches='tight')

# Clean up the statistics file
if not args.keep_files:
    os.remove(csv_path)
