"""
========================================================
Sample Data Generator
========================================================
Generates a realistic 200-reading sample dataset for
demonstration purposes without running the full simulation.
This CSV is committed to GitHub to show project outputs.

Run: python data/generate_sample_data.py
========================================================
"""

import sys
import os
import csv
import random
from datetime import datetime, timedelta

# ── Path setup ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from python_simulation.sensor_simulator import SensorSimulator
from python_simulation.alert_engine     import AlertEngine
from python_simulation.pump_controller  import PumpController


def generate_sample_data(num_readings: int = 200, output_filename: str = "sample_sensor_data.csv"):
    """Generate and save sample sensor data."""

    simulator  = SensorSimulator(seed=42)
    alert_eng  = AlertEngine()
    pump_ctrl  = PumpController()

    output_path = os.path.join(os.path.dirname(__file__), output_filename)

    columns = [
        "reading_id", "timestamp", "scenario",
        "soil_moisture", "temperature", "humidity",
        "light_intensity", "water_level",
        "pump_status", "alert_count", "alerts",
        "system_status",
    ]

    start_time = datetime(2025, 6, 1, 6, 0, 0)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()

        for i in range(num_readings):
            # Simulate realistic time progression
            current_time = start_time + timedelta(minutes=i * 5)
            hour = current_time.hour

            # Pick scenario based on time of day
            if 6 <= hour < 10:
                scenario = random.choices(
                    ["normal", "dry_soil"], weights=[60, 40])[0]
            elif 10 <= hour < 15:
                scenario = random.choices(
                    ["dry_soil", "high_temp", "normal"], weights=[40, 35, 25])[0]
            elif 15 <= hour < 19:
                scenario = random.choices(
                    ["normal", "high_temp"], weights=[70, 30])[0]
            elif 19 <= hour < 22:
                scenario = random.choices(
                    ["normal", "low_water"], weights=[70, 30])[0]
            else:
                scenario = "night"

            reading = simulator.get_reading(scenario=scenario)
            reading["timestamp"] = current_time.strftime("%Y-%m-%d %H:%M:%S")

            alerts = alert_eng.check(reading)
            pump_on = pump_ctrl.decide(reading)
            system_status = alert_eng.get_system_status(reading)

            row = {
                "reading_id":      reading["reading_id"],
                "timestamp":       reading["timestamp"],
                "scenario":        reading["scenario"],
                "soil_moisture":   reading["soil_moisture"],
                "temperature":     reading["temperature"],
                "humidity":        reading["humidity"],
                "light_intensity": reading["light_intensity"],
                "water_level":     reading["water_level"],
                "pump_status":     "ON" if pump_on else "OFF",
                "alert_count":     len(alerts),
                "alerts":          " | ".join(alerts) if alerts else "None",
                "system_status":   system_status,
            }
            writer.writerow(row)

    print(f"✓ Generated {num_readings} readings → {output_path}")
    return output_path


if __name__ == "__main__":
    path = generate_sample_data(200)
    print(f"\nSample data saved to: {path}")
    print("You can commit this file to GitHub as a project output!")
