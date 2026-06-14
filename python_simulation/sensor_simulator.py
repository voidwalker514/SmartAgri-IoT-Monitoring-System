"""
========================================================
Sensor Simulator Module
========================================================
Simulates realistic IoT sensor readings for:
  - Soil Moisture Sensor  (capacitive / resistive)
  - DHT22 Temperature & Humidity Sensor
  - LDR (Light Dependent Resistor)
  - Water Level Sensor (ultrasonic / float)

Scenarios supported:
  - 'normal'       : Healthy farm conditions
  - 'dry_soil'     : Drought / irrigation needed
  - 'high_temp'    : Heat stress conditions
  - 'low_water'    : Water tank near empty
  - 'night'        : Night time low-light conditions
  - 'rainy'        : Wet conditions
  - 'random'       : Randomly picks from all scenarios
========================================================
"""

import random
import math
import time
from datetime import datetime
from typing import Dict


class SensorSimulator:
    """
    Simulates multi-sensor readings for a smart farm.
    
    All values mimic real-world sensor behavior with:
      - Gaussian noise (natural sensor drift)
      - Gradual trends (temperature rises slowly)
      - Scenario-based presets (dry, wet, night, etc.)
    """

    # ── Sensor Value Ranges ─────────────────────────────────────────
    RANGES = {
        "soil_moisture":   (0.0,   100.0),   # % (0=completely dry, 100=saturated)
        "temperature":     (10.0,  55.0),    # °C
        "humidity":        (10.0,  100.0),   # %
        "light_intensity": (0.0,   100000.0),# lux
        "water_level":     (0.0,   100.0),   # % (0=empty tank, 100=full)
    }

    # ── Scenario Presets ────────────────────────────────────────────
    SCENARIOS = {
        "normal": {
            "soil_moisture":   (45.0, 65.0),
            "temperature":     (22.0, 28.0),
            "humidity":        (55.0, 75.0),
            "light_intensity": (20000.0, 60000.0),
            "water_level":     (60.0, 90.0),
        },
        "dry_soil": {
            "soil_moisture":   (5.0,  20.0),   # Very dry — needs irrigation
            "temperature":     (30.0, 40.0),   # Hot and dry
            "humidity":        (20.0, 40.0),   # Low humidity
            "light_intensity": (40000.0, 90000.0),
            "water_level":     (50.0, 80.0),
        },
        "high_temp": {
            "soil_moisture":   (20.0, 40.0),
            "temperature":     (42.0, 52.0),   # Extreme heat stress
            "humidity":        (15.0, 35.0),
            "light_intensity": (60000.0, 95000.0),
            "water_level":     (30.0, 60.0),
        },
        "low_water": {
            "soil_moisture":   (10.0, 30.0),
            "temperature":     (25.0, 35.0),
            "humidity":        (30.0, 50.0),
            "light_intensity": (15000.0, 50000.0),
            "water_level":     (2.0,  15.0),   # Tank almost empty
        },
        "night": {
            "soil_moisture":   (40.0, 60.0),
            "temperature":     (12.0, 20.0),   # Cool at night
            "humidity":        (70.0, 95.0),   # High humidity at night
            "light_intensity": (0.0,  500.0),  # Near darkness
            "water_level":     (50.0, 80.0),
        },
        "rainy": {
            "soil_moisture":   (80.0, 99.0),   # Over-saturated
            "temperature":     (18.0, 26.0),
            "humidity":        (85.0, 100.0),  # Very high humidity
            "light_intensity": (1000.0, 15000.0),
            "water_level":     (85.0, 100.0),  # Tank overflowing
        },
    }

    SCENARIO_NAMES = list(SCENARIOS.keys())

    def __init__(self, noise_level: float = 0.03, seed: int = None):
        """
        Initialize simulator.
        
        Args:
            noise_level: Fraction of range to use as Gaussian noise (0.03 = 3%)
            seed: Random seed for reproducibility (None = truly random)
        """
        self.noise_level = noise_level
        self._reading_count = 0
        self._last_reading = None
        self._trend_offset = 0.0  # Simulates gradual temperature drift
        
        if seed is not None:
            random.seed(seed)

    def _add_noise(self, value: float, sensor_name: str) -> float:
        """Add realistic Gaussian noise to a sensor value."""
        range_size = self.RANGES[sensor_name][1] - self.RANGES[sensor_name][0]
        noise = random.gauss(0, self.noise_level * range_size)
        result = value + noise
        # Clamp to valid range
        lo, hi = self.RANGES[sensor_name]
        return round(max(lo, min(hi, result)), 2)

    def _interpolate(self, lo: float, hi: float) -> float:
        """Generate a value uniformly between lo and hi."""
        return round(random.uniform(lo, hi), 2)

    def get_reading(self, scenario: str = "random") -> Dict:
        """
        Generate a single sensor reading dictionary.
        
        Args:
            scenario: One of the SCENARIOS keys, or 'random'
            
        Returns:
            Dict with all sensor values plus metadata
        """
        self._reading_count += 1

        # Pick scenario
        if scenario == "random":
            # Weight toward normal (50%), others share 50%
            weights = [50, 15, 10, 10, 8, 7]
            chosen = random.choices(self.SCENARIO_NAMES, weights=weights, k=1)[0]
        elif scenario in self.SCENARIOS:
            chosen = scenario
        else:
            raise ValueError(f"Unknown scenario '{scenario}'. Valid: {self.SCENARIO_NAMES + ['random']}")

        preset = self.SCENARIOS[chosen]

        # Generate base values from preset ranges
        soil_moisture   = self._add_noise(self._interpolate(*preset["soil_moisture"]), "soil_moisture")
        temperature     = self._add_noise(self._interpolate(*preset["temperature"]), "temperature")
        humidity        = self._add_noise(self._interpolate(*preset["humidity"]), "humidity")
        light_intensity = self._add_noise(self._interpolate(*preset["light_intensity"]), "light_intensity")
        water_level     = self._add_noise(self._interpolate(*preset["water_level"]), "water_level")

        # Simulate gradual temperature trend
        self._trend_offset += random.uniform(-0.05, 0.05)
        self._trend_offset = max(-2.0, min(2.0, self._trend_offset))
        temperature = round(temperature + self._trend_offset, 2)
        temperature = max(self.RANGES["temperature"][0], min(self.RANGES["temperature"][1], temperature))

        reading = {
            "reading_id":      self._reading_count,
            "timestamp":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scenario":        chosen,
            "soil_moisture":   soil_moisture,
            "temperature":     temperature,
            "humidity":        humidity,
            "light_intensity": light_intensity,
            "water_level":     water_level,
        }
        self._last_reading = reading
        return reading

    def get_batch(self, count: int = 100, scenario: str = "random") -> list:
        """
        Generate a batch of sensor readings.
        
        Args:
            count: Number of readings to generate
            scenario: Scenario to use for all readings
            
        Returns:
            List of reading dictionaries
        """
        return [self.get_reading(scenario=scenario) for _ in range(count)]

    def simulate_day_cycle(self, hours: int = 24, readings_per_hour: int = 4) -> list:
        """
        Simulate a full day/night cycle with realistic patterns.
        
        Morning (6-12):  Rising temperature, increasing light
        Afternoon (12-18): Peak temperature, high light
        Evening (18-22): Falling temperature
        Night (22-6):    Low light, low temperature, high humidity
        """
        readings = []
        for hour in range(hours):
            for _ in range(readings_per_hour):
                # Determine time-of-day scenario
                if 6 <= hour < 12:
                    scenario = random.choice(["normal", "dry_soil"])
                elif 12 <= hour < 18:
                    scenario = random.choice(["high_temp", "dry_soil", "normal"])
                elif 18 <= hour < 22:
                    scenario = "normal"
                else:
                    scenario = "night"

                reading = self.get_reading(scenario=scenario)
                # Override timestamp to simulate the hour
                reading["timestamp"] = f"2025-01-01 {hour:02d}:{random.randint(0,59):02d}:00"
                readings.append(reading)

        return readings


# ── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sim = SensorSimulator(seed=42)
    print("=== Sample Sensor Readings ===\n")
    
    for scenario in SensorSimulator.SCENARIO_NAMES:
        reading = sim.get_reading(scenario=scenario)
        print(f"Scenario: {scenario:12s} | "
              f"Moisture: {reading['soil_moisture']:6.1f}% | "
              f"Temp: {reading['temperature']:5.1f}°C | "
              f"Humidity: {reading['humidity']:5.1f}% | "
              f"Light: {reading['light_intensity']:8.1f} lux | "
              f"Water: {reading['water_level']:5.1f}%")
