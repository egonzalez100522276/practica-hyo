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
        writer.writerow(["case_file", "n_slots", "m_buses", "u_workshops", "optimal_cost", "time_s", "variables", "constraints", "availability_pct"])

for case_idx in range(1, args.num_cases + 1):
    # Generate random case
    n = random.randint(1, 10)  # Number of time slots
    m = random.randint(1, 10)  # Number of buses
    u = random.randint(1, 10)  # Number of workshops

    # Generate binary O matrix (n x u) with exactly m+2 ones
    O = [[0] * u for _ in range(n)]  # Initialize all to 0
    
    # Calculate the number of ones to set
    num_ones = min(m + 2, n * u)  # Ensure not exceeding the matrix size
    
    # Randomly set num_ones elements to 1
    positions = random.sample(range(n * u), num_ones)
    for pos in positions:
        row = pos // u
        col = pos % u
        O[row][col] = 1

    # Calculate percentage of available rows (slots)
    available_rows = sum(1 for row in O if sum(row) > 0)
    availability_percentage = (available_rows / n) * 100 if n > 0 else 0

    # O = [random.choices([0, 1], weights=[0.4, 0.6], k=u) for _ in range(n)]



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
                val = random.randint(1, 100) # Generate integer costs for C matrix
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
            check=True, # Will raise CalledProcessError if gen-2.py returns non-zero
            timeout=60  # Timeout of 60 seconds to prevent deadlocks
        )
    except subprocess.TimeoutExpired as e:
        print(f"Timeout expired for case {case_idx}. The process was likely deadlocked or taking too long.")
        print(f"Stdout so far: {e.stdout}")
        print(f"Stderr so far: {e.stderr}")
        continue
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

    # Check if an optimal solution was reported in the output.
    # gen-2.py prints the cost, variables and constraints to stdout.
    cost_match = re.search(r"Coste total óptimo:\s*([0-9eE.+-]+)", stdout, re.IGNORECASE)
    if not cost_match:
        print(f"[{case_idx}] Warning: Optimal solution cost not found in the output of gen-2.py. Skipping case.")
        print(f"Stdout from gen-2.py: {stdout.strip()}")
        continue

    optimal_cost = float(cost_match.group(1))
    vars_match = re.search(r"Variables:\s*(\d+)", stdout, re.IGNORECASE)
    rows_match = re.search(r"Restricciones:\s*(\d+)", stdout, re.IGNORECASE)
    num_vars = int(vars_match.group(1)) if vars_match else None
    num_constraints = int(rows_match.group(1)) if rows_match else None

    print(f"[{case_idx}] Cost: {optimal_cost}, Time: {elapsed_time:.4f}s, Vars: {num_vars}, Constraints: {num_constraints}")

    # Save statistics
    with open(csv_path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([case_file, n, m, u, optimal_cost, elapsed_time, num_vars, num_constraints, availability_percentage])

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

# --- Plot 4: Availability vs Time ---
df_sorted_avail = df.sort_values(by='availability_pct')
plt.figure(figsize=(8,6))
plt.plot(df_sorted_avail['availability_pct'], df_sorted_avail['time_s'],
         marker='o', color='purple', linestyle='-')
plt.xlabel("Percentage of Available Rows (%)")
plt.ylabel("Execution Time (s)")
plt.title("Execution Time vs. Row Availability")
plt.grid(True, linestyle='--', alpha=0.7)
plt.savefig("availability_vs_time_p2.png", dpi=300, bbox_inches='tight')
plt.show()

# Clean up the statistics file
if not args.keep_files:
    if csv_path.exists():
        os.remove(csv_path)
