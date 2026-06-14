"""
========================================================
Pump Controller Module
========================================================
Simulates an irrigation water pump controlled by a relay.

Logic:
  - Turn pump ON  if soil moisture < MOISTURE_LOW_THRESHOLD
  - Turn pump OFF if soil moisture > MOISTURE_HIGH_THRESHOLD
  - Override OFF  if water level < WATER_SAFE_THRESHOLD
                  (protects pump from running dry)
  - Keep current state if between thresholds (hysteresis)

This hysteresis prevents rapid pump ON/OFF cycling.
========================================================
"""

from typing import Dict


class PumpController:
    """
    Simulates a relay-controlled irrigation water pump.
    
    Uses hysteresis control to avoid rapid switching.
    
    Attributes:
        pump_on (bool): Current pump state (True=ON, False=OFF)
        total_on_cycles (int): Number of times pump turned ON
        total_off_cycles (int): Number of times pump turned OFF
    """

    # ── Threshold Constants ──────────────────────────────────────────
    MOISTURE_LOW_THRESHOLD  = 30.0   # % — turn pump ON below this
    MOISTURE_HIGH_THRESHOLD = 65.0   # % — turn pump OFF above this
    WATER_SAFE_THRESHOLD    = 10.0   # % — minimum tank level to run pump

    def __init__(self):
        self.pump_on = False
        self.total_on_cycles  = 0
        self.total_off_cycles = 0
        self._history: list = []

    def decide(self, reading: Dict) -> bool:
        """
        Decide pump ON/OFF based on sensor reading.
        
        Args:
            reading: Dictionary with 'soil_moisture' and 'water_level' keys
            
        Returns:
            bool: True if pump should be ON, False if OFF
        """
        moisture    = reading.get("soil_moisture", 50.0)
        water_level = reading.get("water_level", 80.0)

        previous_state = self.pump_on

        # Safety check: protect pump if water tank is too low
        if water_level <= self.WATER_SAFE_THRESHOLD:
            self.pump_on = False
            reason = f"SAFETY: Water tank critically low ({water_level:.1f}%)"
        
        # Turn pump ON if soil is too dry
        elif moisture <= self.MOISTURE_LOW_THRESHOLD:
            self.pump_on = True
            reason = f"Soil moisture {moisture:.1f}% < {self.MOISTURE_LOW_THRESHOLD}%"
        
        # Turn pump OFF if soil is sufficiently moist
        elif moisture >= self.MOISTURE_HIGH_THRESHOLD:
            self.pump_on = False
            reason = f"Soil moisture {moisture:.1f}% > {self.MOISTURE_HIGH_THRESHOLD}%"
        
        # Hysteresis zone — keep current state
        else:
            reason = f"Hysteresis zone ({self.MOISTURE_LOW_THRESHOLD}%–{self.MOISTURE_HIGH_THRESHOLD}%)"

        # Count state changes
        if self.pump_on and not previous_state:
            self.total_on_cycles += 1
        elif not self.pump_on and previous_state:
            self.total_off_cycles += 1

        # Record history
        self._history.append({
            "reading_id": reading.get("reading_id"),
            "timestamp": reading.get("timestamp"),
            "pump_on": self.pump_on,
            "soil_moisture": moisture,
            "water_level": water_level,
            "reason": reason,
        })

        return self.pump_on

    def get_status_string(self) -> str:
        """Return human-readable pump status."""
        return "💧 PUMP: ON  (Irrigating)" if self.pump_on else "🔴 PUMP: OFF (Standby)"

    def get_stats(self) -> Dict:
        """Return pump operation statistics."""
        return {
            "current_state": "ON" if self.pump_on else "OFF",
            "total_on_cycles": self.total_on_cycles,
            "total_off_cycles": self.total_off_cycles,
            "history_length": len(self._history),
        }

    def get_history(self) -> list:
        """Return full pump decision history."""
        return self._history


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    pump = PumpController()

    test_cases = [
        {"reading_id": 1, "timestamp": "08:00", "soil_moisture": 15.0, "water_level": 75.0},
        {"reading_id": 2, "timestamp": "09:00", "soil_moisture": 40.0, "water_level": 72.0},
        {"reading_id": 3, "timestamp": "10:00", "soil_moisture": 55.0, "water_level": 68.0},
        {"reading_id": 4, "timestamp": "11:00", "soil_moisture": 70.0, "water_level": 65.0},
        {"reading_id": 5, "timestamp": "12:00", "soil_moisture": 20.0, "water_level": 8.0},  # Low water!
        {"reading_id": 6, "timestamp": "13:00", "soil_moisture": 20.0, "water_level": 15.0}, # Tank refilled
    ]

    print("=== Pump Controller Test ===\n")
    for r in test_cases:
        status = pump.decide(r)
        print(f"[{r['timestamp']}] Moisture: {r['soil_moisture']:5.1f}% | "
              f"Water: {r['water_level']:5.1f}% | "
              f"Pump: {'ON ' if status else 'OFF'} | "
              f"Reason: {pump._history[-1]['reason']}")

    print(f"\n{pump.get_status_string()}")
    print(f"Stats: {pump.get_stats()}")
