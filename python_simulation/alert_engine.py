"""
========================================================
Alert Engine Module
========================================================
Checks sensor readings against configurable thresholds
and generates prioritized alerts.

Alert Levels:
  - CRITICAL : Immediate action required (crop damage risk)
  - WARNING  : Attention needed soon
  - INFO     : Informational / optimal conditions

Thresholds are based on general crop requirements
(can be tuned per crop type via config).
========================================================
"""

from typing import Dict, List


# ── Default Threshold Configuration ─────────────────────────────────────────
THRESHOLDS = {
    "soil_moisture": {
        "critical_low":  10.0,   # Below 10% → crop wilting, pump ON urgently
        "warning_low":   25.0,   # Below 25% → soil drying, pump ON soon
        "warning_high":  85.0,   # Above 85% → waterlogging risk
        "critical_high": 95.0,   # Above 95% → root rot danger
    },
    "temperature": {
        "critical_low":  5.0,    # Frost risk
        "warning_low":   10.0,   # Cold stress
        "warning_high":  38.0,   # Heat stress
        "critical_high": 45.0,   # Crop death risk
    },
    "humidity": {
        "critical_low":  15.0,   # Extreme dry air
        "warning_low":   30.0,   # Low humidity stress
        "warning_high":  90.0,   # Fungal disease risk
        "critical_high": 98.0,   # Very high fungal risk
    },
    "light_intensity": {
        "critical_low":  0.0,    # Complete darkness (sensor fault?)
        "warning_low":   500.0,  # Insufficient light for photosynthesis
        "warning_high":  80000.0,# Potential light saturation
        "critical_high": 95000.0,# Extremely intense sunlight
    },
    "water_level": {
        "critical_low":  5.0,    # Tank nearly empty — stop pump to prevent damage
        "warning_low":   20.0,   # Refill tank soon
        "warning_high":  98.0,   # Tank overflowing
        "critical_high": 100.0,  # Overflow
    },
}

# ── Alert Messages ─────────────────────────────────────────────────────────
ALERT_MESSAGES = {
    "soil_moisture_critical_low":  "🔴 CRITICAL: Soil moisture {val:.1f}% — CROPS AT WILTING RISK! Irrigate immediately.",
    "soil_moisture_warning_low":   "🟡 WARNING: Soil moisture {val:.1f}% — soil drying. Start irrigation soon.",
    "soil_moisture_warning_high":  "🟡 WARNING: Soil moisture {val:.1f}% — waterlogging risk. Stop irrigation.",
    "soil_moisture_critical_high": "🔴 CRITICAL: Soil moisture {val:.1f}% — ROOT ROT DANGER! Stop irrigation now.",
    "temperature_critical_low":    "🔴 CRITICAL: Temperature {val:.1f}°C — FROST RISK! Protect crops immediately.",
    "temperature_warning_low":     "🟡 WARNING: Temperature {val:.1f}°C — cold stress. Monitor crops.",
    "temperature_warning_high":    "🟡 WARNING: Temperature {val:.1f}°C — heat stress. Increase irrigation.",
    "temperature_critical_high":   "🔴 CRITICAL: Temperature {val:.1f}°C — CROP DEATH RISK! Emergency cooling needed.",
    "humidity_critical_low":       "🔴 CRITICAL: Humidity {val:.1f}% — extreme dry air. Crops dehydrating.",
    "humidity_warning_low":        "🟡 WARNING: Humidity {val:.1f}% — low humidity. Monitor transpiration.",
    "humidity_warning_high":       "🟡 WARNING: Humidity {val:.1f}% — fungal disease risk. Improve ventilation.",
    "humidity_critical_high":      "🔴 CRITICAL: Humidity {val:.1f}% — very high fungal risk. Ventilate now.",
    "light_intensity_warning_low": "🟡 WARNING: Light {val:.0f} lux — insufficient for photosynthesis.",
    "light_intensity_critical_high":"🔴 CRITICAL: Light {val:.0f} lux — extreme intensity. Shading needed.",
    "water_level_critical_low":    "🔴 CRITICAL: Water tank {val:.1f}% — TANK NEARLY EMPTY! Pump stopped. Refill now.",
    "water_level_warning_low":     "🟡 WARNING: Water tank {val:.1f}% — refill soon to avoid pump damage.",
    "water_level_warning_high":    "🟡 WARNING: Water tank {val:.1f}% — near overflow.",
}


class AlertEngine:
    """
    Compares sensor readings against thresholds and returns
    a list of alert strings.
    
    Usage:
        engine = AlertEngine()
        alerts = engine.check(reading_dict)
    """

    def __init__(self, custom_thresholds: Dict = None):
        """
        Initialize with optional custom thresholds.
        
        Args:
            custom_thresholds: Override default THRESHOLDS dict.
        """
        self.thresholds = custom_thresholds if custom_thresholds else THRESHOLDS
        self.alert_history: List[Dict] = []   # Keep history for analysis

    def _check_sensor(self, sensor_name: str, value: float) -> List[str]:
        """Check a single sensor value and return alerts."""
        alerts = []
        t = self.thresholds.get(sensor_name, {})

        # Critical checks first (most important)
        if "critical_low" in t and value <= t["critical_low"]:
            key = f"{sensor_name}_critical_low"
            if key in ALERT_MESSAGES:
                alerts.append(("CRITICAL", ALERT_MESSAGES[key].format(val=value)))

        elif "warning_low" in t and value <= t["warning_low"]:
            key = f"{sensor_name}_warning_low"
            if key in ALERT_MESSAGES:
                alerts.append(("WARNING", ALERT_MESSAGES[key].format(val=value)))

        if "critical_high" in t and value >= t["critical_high"]:
            key = f"{sensor_name}_critical_high"
            if key in ALERT_MESSAGES:
                alerts.append(("CRITICAL", ALERT_MESSAGES[key].format(val=value)))

        elif "warning_high" in t and value >= t["warning_high"]:
            key = f"{sensor_name}_warning_high"
            if key in ALERT_MESSAGES:
                alerts.append(("WARNING", ALERT_MESSAGES[key].format(val=value)))

        return alerts

    def check(self, reading: Dict) -> List[str]:
        """
        Check all sensors in a reading and return alert messages.
        
        Args:
            reading: Dictionary from SensorSimulator.get_reading()
            
        Returns:
            List of alert message strings (empty if all OK)
        """
        all_alerts = []

        sensors = [
            "soil_moisture",
            "temperature",
            "humidity",
            "light_intensity",
            "water_level",
        ]

        for sensor in sensors:
            if sensor in reading:
                sensor_alerts = self._check_sensor(sensor, reading[sensor])
                all_alerts.extend(sensor_alerts)

        # Store in history
        if all_alerts:
            self.alert_history.append({
                "reading_id": reading.get("reading_id"),
                "timestamp": reading.get("timestamp"),
                "alerts": all_alerts,
            })

        # Return just the message strings for simplicity
        return [msg for _, msg in all_alerts]

    def check_with_levels(self, reading: Dict) -> List[Dict]:
        """
        Check sensors and return structured alert objects with levels.
        
        Returns:
            List of dicts: {"level": "CRITICAL/WARNING", "message": "..."}
        """
        all_alerts = []
        for sensor in ["soil_moisture", "temperature", "humidity", "light_intensity", "water_level"]:
            if sensor in reading:
                sensor_alerts = self._check_sensor(sensor, reading[sensor])
                for level, msg in sensor_alerts:
                    all_alerts.append({"level": level, "sensor": sensor, "message": msg})
        return all_alerts

    def get_system_status(self, reading: Dict) -> str:
        """
        Returns an overall system status string.
        
        Returns:
            'CRITICAL' | 'WARNING' | 'OK'
        """
        alerts = self.check_with_levels(reading)
        if any(a["level"] == "CRITICAL" for a in alerts):
            return "CRITICAL"
        elif any(a["level"] == "WARNING" for a in alerts):
            return "WARNING"
        return "OK"

    def get_alert_summary(self) -> Dict:
        """Return summary statistics of all alerts generated so far."""
        total = len(self.alert_history)
        critical_count = sum(
            1 for h in self.alert_history
            for level, _ in h["alerts"] if level == "CRITICAL"
        )
        warning_count = sum(
            1 for h in self.alert_history
            for level, _ in h["alerts"] if level == "WARNING"
        )
        return {
            "total_alert_events": total,
            "total_critical": critical_count,
            "total_warnings": warning_count,
        }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    engine = AlertEngine()

    test_readings = [
        # Dry soil scenario
        {"reading_id": 1, "timestamp": "2025-01-01 08:00:00",
         "soil_moisture": 8.5, "temperature": 35.0, "humidity": 25.0,
         "light_intensity": 50000, "water_level": 70.0},
        # High temperature scenario
        {"reading_id": 2, "timestamp": "2025-01-01 14:00:00",
         "soil_moisture": 30.0, "temperature": 47.0, "humidity": 20.0,
         "light_intensity": 85000, "water_level": 60.0},
        # Low water level
        {"reading_id": 3, "timestamp": "2025-01-01 16:00:00",
         "soil_moisture": 20.0, "temperature": 28.0, "humidity": 50.0,
         "light_intensity": 40000, "water_level": 4.0},
        # Normal (no alerts)
        {"reading_id": 4, "timestamp": "2025-01-01 09:00:00",
         "soil_moisture": 55.0, "temperature": 25.0, "humidity": 65.0,
         "light_intensity": 35000, "water_level": 75.0},
    ]

    for r in test_readings:
        alerts = engine.check(r)
        status = engine.get_system_status(r)
        print(f"\nReading #{r['reading_id']} | Status: {status}")
        if alerts:
            for a in alerts:
                print(f"  {a}")
        else:
            print("  ✅ All systems normal")

    print("\n=== Alert Summary ===")
    print(engine.get_alert_summary())
