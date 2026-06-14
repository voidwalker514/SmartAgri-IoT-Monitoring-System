<div align="center">

# 🌱 IoT-Enabled Smart Agriculture Monitoring System

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square&logo=python)](https://www.python.org)
[![Arduino](https://img.shields.io/badge/Arduino-UNO%2FESP32-teal?style=flat-square&logo=arduino)](https://www.arduino.cc)
[![Dash](https://img.shields.io/badge/Dashboard-Plotly%20Dash-purple?style=flat-square&logo=plotly)](https://dash.plotly.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)]()

> **Real-time IoT farm monitoring system** with sensor simulation, automated irrigation control, threshold-based alerting, and an interactive web dashboard. Built as an industry-grade IoT portfolio project demonstrating embedded systems, data engineering, and smart automation concepts.

[📖 Documentation](docs/PROJECT_DOCUMENTATION.md) • [🔌 Circuit Diagram](circuit_diagram/README.md) • [🎤 Interview Q&A](docs/INTERVIEW_QA.md) • [▶ Quick Start](#quick-start)

</div>

---

## 📋 Table of Contents

- [Problem Statement](#problem-statement)
- [What This System Does](#what-this-system-does)
- [IoT Concepts Demonstrated](#iot-concepts-demonstrated)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Sensors & Hardware](#sensors--hardware)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [How to Run](#how-to-run)
- [Simulation Scenarios](#simulation-scenarios)
- [Dashboard Features](#dashboard-features)
- [Sample Output](#sample-output)
- [Learning Outcomes](#learning-outcomes)
- [Virtual Simulation Guide](#virtual-simulation-guide)

---

## 🚨 Problem Statement

Traditional agriculture relies on **manual field inspection** — a farmer must physically check soil, weather, and irrigation systems multiple times per day. This leads to:

| Problem | Impact |
|---------|--------|
| Delayed irrigation response | Crop wilting and yield loss |
| Over-irrigation | Water waste + root rot |
| Undetected temperature spikes | Crop death from heat stress |
| Empty water tank + running pump | Pump motor damage |
| No remote visibility | Farmer must be physically present |

**This IoT system solves all of these** through 24/7 automated monitoring, real-time alerts, and intelligent pump control.

---

## ✅ What This System Does

- 📡 **Monitors 5 parameters** continuously: soil moisture, temperature, humidity, light intensity, water level
- 🚨 **Generates alerts** at WARNING and CRITICAL levels with specific action guidance
- 💧 **Controls irrigation pump** automatically using hysteresis logic (prevents rapid switching)
- 🛡️ **Protects the pump** from dry-running when water tank is critically low
- 📊 **Logs all data** to timestamped CSV files for analysis
- 🌐 **Shows real-time dashboard** at `http://localhost:8050` with live gauges, trend charts, and alert panel
- 📈 **Generates 5 visualization charts** from historical data

---

## 🔌 IoT Concepts Demonstrated

| Concept | Implementation |
|---------|---------------|
| **Sensor Integration** | DHT22, soil moisture, LDR, water level sensors |
| **ADC Conversion** | Raw analog voltage → calibrated percentage values |
| **Edge Computing** | Threshold decisions made on microcontroller |
| **Actuator Control** | Relay-controlled water pump |
| **MQTT Protocol** | Publish-subscribe messaging (optional, configured) |
| **Time-Series Data** | Timestamped CSV logging |
| **Real-Time Dashboard** | Live updating web UI with callbacks |
| **Alert Systems** | Multi-level (INFO/WARNING/CRITICAL) alert engine |
| **Hysteresis Control** | Prevents pump chattering / rapid cycling |
| **Data Visualization** | 5 chart types: timeline, heatmap, correlation, etc. |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|----------|
| **Microcontroller** | Arduino UNO / ESP32 |
| **Simulation** | Python 3.9+ (no hardware required) |
| **Circuit Simulation** | Wokwi.com (browser-based) |
| **Dashboard** | Plotly Dash + Dash Bootstrap Components |
| **Charts** | Matplotlib + Seaborn |
| **Data Storage** | CSV (pandas DataFrames) |
| **Protocol (optional)** | MQTT (paho-mqtt) |
| **Cloud (optional)** | ThingSpeak API |
| **Environment** | python-dotenv (API key management) |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SENSOR LAYER                                 │
│  [Soil Moisture]  [DHT22 Temp/Humid]  [LDR Light]  [Water]    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Analog/Digital Signals
┌──────────────────────────▼──────────────────────────────────────┐
│               PROCESSING LAYER (Edge Computing)                  │
│          Arduino UNO / ESP32  OR  Python Simulator              │
│                                                                  │
│   ┌──────────────┐    ┌──────────────────┐   ┌──────────────┐  │
│   │  ADC Reading │    │ Threshold Engine  │   │ Pump Logic   │  │
│   │  + Noise     │───▶│ soil < 30% → ON  │───▶│ Hysteresis   │  │
│   │  Filtering   │    │ temp > 42°C → 🚨  │   │ Safety Check │  │
│   └──────────────┘    └──────────────────┘   └──────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
        ┌──────────────────┼────────────────────┐
        │                  │                    │
┌───────▼────┐    ┌─────────▼────────┐   ┌──────▼──────┐
│   RELAY    │    │   DATA LOGGER    │   │ ALERT ENGINE │
│  💧 Pump   │    │  CSV + Reports   │   │ CRITICAL/WARN│
│  ON / OFF  │    └────────┬─────────┘   └──────┬───────┘
└────────────┘             │                    │
                  ┌─────────▼────────────────────▼──┐
                  │       WEB DASHBOARD              │
                  │  Gauges | Charts | Alerts | Table │
                  │  http://localhost:8050            │
                  └──────────────────────────────────┘
```

---

## 📟 Sensors & Hardware

| Sensor | Parameter | Pin | Range |
|--------|-----------|-----|-------|
| **DHT22** | Temperature + Humidity | D2 | -40 to 80°C / 0-100% |
| **Capacitive Soil Moisture** | Soil moisture | A0 | 0-100% |
| **LDR** | Light intensity | A1 | 0-100,000 lux |
| **Water Level Sensor** | Tank water level | A2 | 0-100% |
| **5V Relay Module** | Pump ON/OFF | D7 | Digital |
| **Green LED** | Status OK | D8 | Digital |
| **Yellow LED** | Warning | D9 | Digital |
| **Red LED** | Critical Alert | D10 | Digital |

---

## 📁 Project Structure

```
IoT-Smart-Agriculture-Monitoring-System/
│
├── 📄 main.py                        # Entry point (CLI + simulation runner)
├── 📄 requirements.txt               # Python dependencies
├── 📄 .env.example                   # API key template (never commit .env!)
├── 📄 .gitignore                     # Git ignore rules
├── 📄 README.md                      # This file
│
├── 🔌 arduino_code/
│   └── smart_agriculture.ino         # Full Arduino C++ sensor code
│
├── 🐍 python_simulation/
│   ├── sensor_simulator.py           # 6-scenario sensor data generator
│   ├── alert_engine.py               # Threshold checking + alert generation
│   ├── pump_controller.py            # Hysteresis pump control logic
│   ├── data_logger.py                # CSV logging + report generation
│   └── visualizer.py                 # 5 chart types (matplotlib/seaborn)
│
├── 🌐 dashboard/
│   └── app.py                        # Plotly Dash real-time web dashboard
│
├── 📊 data/
│   ├── generate_sample_data.py       # Generates 200-reading sample CSV
│   └── sample_sensor_data.csv        # ← Pre-generated dataset for GitHub
│
├── 📈 outputs/
│   ├── generate_charts.py            # Regenerate charts from CSV
│   └── charts/                       # Generated PNG visualization files
│       ├── sensor_timeline.png
│       ├── threshold_analysis.png
│       ├── pump_timeline.png
│       ├── correlation_matrix.png
│       └── scenario_distribution.png
│
├── 🔌 circuit_diagram/
│   ├── wokwi_diagram.json            # Wokwi simulation file (paste at wokwi.com)
│   └── README.md                     # Pin connections + wiring guide
│
├── 🖼️ images/                        # Screenshots for README
│
└── 📚 docs/
    ├── PROJECT_DOCUMENTATION.md      # Complete 13-section project guide
    └── INTERVIEW_QA.md               # IoT interview preparation Q&A
```

---

## ⚡ Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/iot-smart-agriculture-monitoring-system.git
cd iot-smart-agriculture-monitoring-system

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run quick demo (10 readings)
python main.py --demo

# 5. Launch live dashboard
python main.py --dashboard
# → Open: http://127.0.0.1:8050
```

---

## 🚀 How to Run

### Option 1: Quick Demo (No setup required after install)
```bash
python main.py --demo
```

### Option 2: Full Simulation (Customizable)
```bash
python main.py --readings 100 --interval 1.0
```

### Option 3: Real-Time Dashboard
```bash
python main.py --dashboard
# Navigate to http://127.0.0.1:8050
```

### Option 4: Generate Sample Data + Charts
```bash
python data/generate_sample_data.py    # Creates sample_sensor_data.csv
python outputs/generate_charts.py     # Creates 5 PNG charts
```

### Option 5: Wokwi Circuit Simulation
1. Go to [wokwi.com](https://wokwi.com)
2. Create new Arduino UNO project
3. Paste `circuit_diagram/wokwi_diagram.json` as diagram
4. Paste `arduino_code/smart_agriculture.ino` as code
5. Click ▶ Start → adjust potentiometers

---

## 🎭 Simulation Scenarios

| Scenario | Soil | Temp | Humidity | Light | Water | Expected |
|----------|------|------|----------|-------|-------|---------|
| `normal` | 45-65% | 22-28°C | 55-75% | 20K-60K | 60-90% | All OK ✅ |
| `dry_soil` | 5-20% | 30-40°C | 20-40% | 40K-90K | 50-80% | Pump ON + Warning |
| `high_temp` | 20-40% | 42-52°C | 15-35% | 60K-95K | 30-60% | CRITICAL Alert 🔴 |
| `low_water` | 10-30% | 25-35°C | 30-50% | 15K-50K | 2-15% | Pump OFF + Warning |
| `night` | 40-60% | 12-20°C | 70-95% | 0-500 | 50-80% | Low light info |
| `rainy` | 80-99% | 18-26°C | 85-100% | 1K-15K | 85-100% | Waterlogging Warning |

---

## 🌐 Dashboard Features

| Feature | Description |
|---------|-------------|
| **5 Live Gauges** | Real-time color-coded gauge charts for all sensors |
| **6 Trend Charts** | Scrolling time-series for each sensor + light/water |
| **Alert Panel** | Live alert log with CRITICAL (red) / WARNING (yellow) colors |
| **Pump Status Badge** | Real-time pump ON/OFF indicator |
| **System Status** | Overall OK/WARNING/CRITICAL badge |
| **Scenario Selector** | Dropdown to simulate different farm conditions |
| **Data Table** | Latest reading values with status for all sensors |
| **Auto-refresh** | Updates every 2 seconds automatically |

---

## 📊 Sample Output

### Console Output
```
#001 Moisture: 14.3% Temp: 33.8°C Humidity: 24.1% Light: 45231 lux Water: 72.1% Pump: ON
  ⚠  🟡 WARNING: Soil moisture 14.3% — soil drying. Start irrigation soon.
#002 Moisture: 47.2% Temp: 46.1°C Humidity: 19.8% Light: 83120 lux Water: 68.5% Pump: ON
  ⚠  🔴 CRITICAL: Temperature 46.1°C — CROP DEATH RISK! Emergency cooling needed.
#003 Moisture: 68.5% Temp: 27.0°C Humidity: 62.3% Light: 38000 lux Water: 75.0% Pump: OFF
```

### Alert Types
| Alert Level | Trigger Conditions |
|-------------|-------------------|
| 🔴 CRITICAL | Soil < 10%, Temp > 45°C, Water < 5%, Humidity < 15% |
| 🟡 WARNING | Soil < 30%, Temp > 38°C, Water < 20%, Humidity < 30% |
| ✅ OK | All sensors within safe operational range |

### Pump Decision Logic
```
Soil Moisture:
  < 30%  → PUMP ON  (Soil too dry — irrigate)
  30-65% → Keep current state (hysteresis zone)
  > 65%  → PUMP OFF (Soil sufficiently moist)

Safety Override:
  Water Level < 10% → PUMP OFF (protect from dry-running)
```

---

## 🎓 Learning Outcomes

After completing this project, you will understand:

- ✅ IoT system design (sensor → processing → actuator → dashboard)
- ✅ Sensor types, ADC conversion, and calibration
- ✅ Threshold-based control logic and hysteresis
- ✅ MQTT protocol and publish-subscribe architecture
- ✅ Python modular programming with classes
- ✅ Real-time web dashboard development (Plotly Dash)
- ✅ Time-series data logging and CSV analysis
- ✅ Data visualization for IoT analytics
- ✅ Git/GitHub project management
- ✅ Professional project documentation

---

## 🎯 Career Applications

This project demonstrates skills relevant for:

| Role | Relevant Skills |
|------|----------------|
| **IoT Engineer** | Sensor integration, MQTT, embedded logic |
| **Embedded Systems Developer** | Arduino C++, ADC, actuator control |
| **Data Analyst** | CSV logging, pandas, matplotlib, seaborn |
| **Smart Farming Specialist** | Precision agriculture, irrigation automation |
| **Automation Engineer** | Threshold logic, relay control, alerts |
| **Full-Stack Developer** | Python web dashboard, REST API, data pipeline |

---

## 📚 References & Tools

- [Arduino Official Documentation](https://www.arduino.cc/reference/en/)
- [DHT22 Datasheet](https://www.sparkfun.com/datasheets/Sensors/Temperature/DHT22.pdf)
- [Wokwi Circuit Simulator](https://wokwi.com)
- [Plotly Dash Documentation](https://dash.plotly.com)
- [ThingSpeak IoT Platform](https://thingspeak.com)
- [HiveMQ MQTT Broker](https://www.hivemq.com)
- [MQTT Protocol Specification](https://mqtt.org)

---

## 📜 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with 💚 for IoT Education | Proof of Work for Smart Agriculture Engineering**

⭐ If this project helped you, please give it a star on GitHub!

</div>
