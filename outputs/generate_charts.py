"""
========================================================
Generate All Charts Script
========================================================
Generates all visualization charts from sample data.
Run this AFTER generating sample data.

Usage:
  python outputs/generate_charts.py
========================================================
"""

import sys
import os
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from python_simulation.visualizer import generate_all_charts

DATA_DIR = os.path.join(BASE_DIR, "data")

def main():
    # Prioritize sample_sensor_data.csv if it exists
    sample_csv = os.path.join(DATA_DIR, "sample_sensor_data.csv")
    if os.path.exists(sample_csv):
        latest = sample_csv
    else:
        # Find the most recent CSV
        pattern = os.path.join(DATA_DIR, "*.csv")
        files = sorted(glob.glob(pattern))
        if not files:
            print("No CSV data files found!")
            print("Run first: python data/generate_sample_data.py")
            sys.exit(1)
        latest = files[-1]
    
    print(f"Using: {latest}\n")
    charts = generate_all_charts(latest)

    print("\n=== Chart Generation Complete ===")
    print("Upload these images to GitHub → outputs/charts/")
    for name, path in charts.items():
        if path:
            size_kb = os.path.getsize(path) / 1024
            print(f"  {name:<25} → {os.path.basename(path)} ({size_kb:.0f} KB)")

if __name__ == "__main__":
    main()
