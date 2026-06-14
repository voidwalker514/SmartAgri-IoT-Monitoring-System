"""
========================================================
Data Logger Module
========================================================
Logs sensor readings, alerts, and pump status to CSV files
and provides summary statistics for reporting.

Output files:
  - data/sensor_log_YYYYMMDD_HHMMSS.csv : Raw sensor data
  - outputs/alert_report_YYYYMMDD.txt   : Human-readable alert report
========================================================
"""

import csv
import os
from datetime import datetime
from typing import Dict, List


# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR   = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")


class DataLogger:
    """
    Logs sensor readings and alerts to CSV and text files.
    
    Usage:
        logger = DataLogger()
        logger.log(reading, alerts, pump_status)
        path = logger.save()
    """

    CSV_COLUMNS = [
        "reading_id",
        "timestamp",
        "scenario",
        "soil_moisture",
        "temperature",
        "humidity",
        "light_intensity",
        "water_level",
        "pump_status",
        "alert_count",
        "alerts",
    ]

    def __init__(self, session_name: str = None):
        """
        Initialize logger with a session name.
        
        Args:
            session_name: Optional name prefix for output files.
        """
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_name = session_name or f"session_{ts}"
        self.csv_path = os.path.join(DATA_DIR, f"sensor_log_{ts}.csv")
        self.alert_report_path = os.path.join(OUTPUT_DIR, f"alert_report_{ts}.txt")

        self._rows: List[Dict] = []
        self._alerts_log: List[str] = []
        self._total_readings = 0
        self._total_alerts = 0

    def log(
        self,
        reading: Dict,
        alerts: List[str] = None,
        pump_status: bool = False,
    ) -> None:
        """
        Log a single sensor reading with alerts and pump status.
        
        Args:
            reading    : Dictionary from SensorSimulator.get_reading()
            alerts     : List of alert strings from AlertEngine.check()
            pump_status: Boolean pump state from PumpController.decide()
        """
        alerts = alerts or []
        self._total_readings += 1
        self._total_alerts += len(alerts)

        row = {
            "reading_id":      reading.get("reading_id", self._total_readings),
            "timestamp":       reading.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "scenario":        reading.get("scenario", "unknown"),
            "soil_moisture":   reading.get("soil_moisture", 0.0),
            "temperature":     reading.get("temperature", 0.0),
            "humidity":        reading.get("humidity", 0.0),
            "light_intensity": reading.get("light_intensity", 0.0),
            "water_level":     reading.get("water_level", 0.0),
            "pump_status":     "ON" if pump_status else "OFF",
            "alert_count":     len(alerts),
            "alerts":          " | ".join(alerts) if alerts else "None",
        }

        self._rows.append(row)

        # Also track alerts for the report
        for alert in alerts:
            self._alerts_log.append(
                f"[{row['timestamp']}] Reading #{row['reading_id']}: {alert}"
            )

    def save(self) -> str:
        """
        Save all logged data to CSV and generate an alert report.
        
        Returns:
            Path to the saved CSV file.
        """
        # Write CSV
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(self._rows)

        # Write alert report
        self._write_alert_report()

        return self.csv_path

    def _write_alert_report(self) -> None:
        """Write a human-readable alert report text file."""
        stats = self.get_stats()
        with open(self.alert_report_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("  IoT Smart Agriculture Monitoring System\n")
            f.write("  Alert Report\n")
            f.write("=" * 60 + "\n")
            f.write(f"  Session    : {self.session_name}\n")
            f.write(f"  Generated  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")

            f.write("[SUMMARY]\n")
            f.write(f"  Total Readings : {stats['total_readings']}\n")
            f.write(f"  Total Alerts   : {stats['total_alerts']}\n")
            f.write(f"  Alert Rate     : {stats['alert_rate']:.1f}%\n")
            f.write(f"  Pump ON Events : {stats['pump_on_events']}\n")
            f.write(f"  Pump OFF Events: {stats['pump_off_events']}\n\n")

            f.write("[SENSOR AVERAGES]\n")
            for key, val in stats["averages"].items():
                f.write(f"  {key:<20}: {val:.2f}\n")

            f.write("\n[ALERT LOG]\n")
            if self._alerts_log:
                for alert in self._alerts_log:
                    f.write(f"  {alert}\n")
            else:
                f.write("  No alerts generated during this session.\n")

    def get_stats(self) -> Dict:
        """Compute and return session statistics."""
        if not self._rows:
            return {}

        def avg(key):
            vals = [r[key] for r in self._rows if isinstance(r[key], (int, float))]
            return sum(vals) / len(vals) if vals else 0.0

        pump_on  = sum(1 for r in self._rows if r["pump_status"] == "ON")
        pump_off = sum(1 for r in self._rows if r["pump_status"] == "OFF")

        return {
            "total_readings": self._total_readings,
            "total_alerts":   self._total_alerts,
            "alert_rate":     (self._total_alerts / self._total_readings * 100) if self._total_readings else 0,
            "pump_on_events": pump_on,
            "pump_off_events": pump_off,
            "averages": {
                "soil_moisture":   avg("soil_moisture"),
                "temperature":     avg("temperature"),
                "humidity":        avg("humidity"),
                "light_intensity": avg("light_intensity"),
                "water_level":     avg("water_level"),
            },
        }

    def get_dataframe(self):
        """Return logged data as a pandas DataFrame (if available)."""
        try:
            import pandas as pd
            return pd.DataFrame(self._rows)
        except ImportError:
            raise ImportError("pandas is required for get_dataframe(). Install it with: pip install pandas")

    @property
    def csv_file_path(self) -> str:
        return self.csv_path

    @property
    def report_file_path(self) -> str:
        return self.alert_report_path


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger = DataLogger(session_name="test_session")

    # Simulate 5 readings
    sample_readings = [
        {"reading_id": 1, "timestamp": "2025-01-01 08:00:00", "scenario": "dry_soil",
         "soil_moisture": 12.0, "temperature": 33.0, "humidity": 28.0,
         "light_intensity": 45000, "water_level": 70.0},
        {"reading_id": 2, "timestamp": "2025-01-01 08:05:00", "scenario": "normal",
         "soil_moisture": 55.0, "temperature": 26.0, "humidity": 62.0,
         "light_intensity": 38000, "water_level": 68.0},
        {"reading_id": 3, "timestamp": "2025-01-01 08:10:00", "scenario": "high_temp",
         "soil_moisture": 28.0, "temperature": 46.0, "humidity": 22.0,
         "light_intensity": 80000, "water_level": 65.0},
    ]

    sample_alerts = [
        ["🟡 WARNING: Soil moisture 12.0% — soil drying. Start irrigation soon."],
        [],
        ["🔴 CRITICAL: Temperature 46.0°C — CROP DEATH RISK! Emergency cooling needed."],
    ]

    sample_pump = [True, True, False]

    for r, a, p in zip(sample_readings, sample_alerts, sample_pump):
        logger.log(r, a, p)

    saved_path = logger.save()
    print(f"✓ CSV saved: {saved_path}")
    print(f"✓ Report saved: {logger.report_file_path}")
    print(f"\nStats: {logger.get_stats()}")
