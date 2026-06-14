/*
 * ============================================================
 * IoT Smart Agriculture Monitoring System
 * Arduino UNO / ESP32 — Sensor Reading Code
 * ============================================================
 * Sensors:
 *   - DHT22   : Temperature & Humidity  → Pin D2
 *   - Soil Moisture (Capacitive)        → Pin A0
 *   - LDR (Light Dependent Resistor)    → Pin A1
 *   - Water Level Sensor (Analog)       → Pin A2
 *   - Relay (Water Pump Control)        → Pin D7
 *   - LED Indicators                    → Pins D8, D9, D10
 *
 * Libraries needed:
 *   - DHT sensor library by Adafruit (v1.4.6+)
 *   - Adafruit Unified Sensor (v1.1.14+)
 *
 * How to install: Arduino IDE → Tools → Manage Libraries
 *   Search: "DHT sensor library" → Install
 *   Search: "Adafruit Unified Sensor" → Install
 *
 * Serial Monitor: 115200 baud
 * ============================================================
 */

#include <DHT.h>

// ── Pin Definitions ──────────────────────────────────────────
#define DHT_PIN         2       // DHT22 data pin
#define DHT_TYPE        DHT22   // DHT22 (AM2302)
#define SOIL_MOISTURE_PIN A0    // Soil moisture sensor (analog)
#define LDR_PIN         A1      // Light dependent resistor (analog)
#define WATER_LEVEL_PIN A2      // Water level sensor (analog)
#define RELAY_PIN       7       // Relay module (pump control)
#define LED_GREEN       8       // Green LED: normal
#define LED_YELLOW      9       // Yellow LED: warning
#define LED_RED         10      // Red LED: critical alert

// ── Threshold Constants ──────────────────────────────────────
#define SOIL_MOISTURE_LOW    30    // % — start irrigation
#define SOIL_MOISTURE_HIGH   65    // % — stop irrigation
#define TEMP_CRITICAL_HIGH   42.0  // °C — critical heat
#define TEMP_WARNING_HIGH    35.0  // °C — heat warning
#define HUMIDITY_LOW         25.0  // % — low humidity warning
#define WATER_LEVEL_LOW      20    // % — refill tank warning
#define WATER_LEVEL_CRITICAL 5     // % — stop pump (safety)
#define LIGHT_LOW_THRESHOLD  100   // lux — low light

// ── Calibration values (tune for your specific sensor) ───────
#define SOIL_DRY_VALUE   860   // Raw ADC value in dry air
#define SOIL_WET_VALUE   380   // Raw ADC value in water
#define WATER_EMPTY      100   // Raw ADC when tank empty
#define WATER_FULL       900   // Raw ADC when tank full
#define LDR_DARK         950   // Raw ADC in total darkness
#define LDR_BRIGHT       10    // Raw ADC in bright sunlight

// ── Global Objects ───────────────────────────────────────────
DHT dht(DHT_PIN, DHT_TYPE);

// ── State variables ──────────────────────────────────────────
bool  pumpOn      = false;
int   readingNum  = 0;

// ── Timing ───────────────────────────────────────────────────
unsigned long lastReadTime    = 0;
unsigned long lastPrintTime   = 0;
const long    READ_INTERVAL   = 2000;   // ms between readings
const long    PRINT_INTERVAL  = 2000;   // ms between prints

// ════════════════════════════════════════════════════════════
void setup() {
    Serial.begin(115200);
    delay(1000);  // Stabilize serial

    // Pin modes
    pinMode(RELAY_PIN,  OUTPUT);
    pinMode(LED_GREEN,  OUTPUT);
    pinMode(LED_YELLOW, OUTPUT);
    pinMode(LED_RED,    OUTPUT);

    // Initial state: pump OFF, green LED
    digitalWrite(RELAY_PIN,  LOW);
    digitalWrite(LED_GREEN,  HIGH);
    digitalWrite(LED_YELLOW, LOW);
    digitalWrite(LED_RED,    LOW);

    dht.begin();

    Serial.println("============================================");
    Serial.println("  IoT Smart Agriculture Monitoring System");
    Serial.println("  Arduino/ESP32 Sensor Node v1.0");
    Serial.println("============================================");
    Serial.println("Format: ID,Timestamp,Moisture%,Temp°C,Humidity%,Light lux,Water%,Pump");
    Serial.println("--------------------------------------------");
}

// ════════════════════════════════════════════════════════════
void loop() {
    unsigned long currentTime = millis();

    if (currentTime - lastReadTime >= READ_INTERVAL) {
        lastReadTime = currentTime;
        readingNum++;

        // ── 1. Read all sensors ──────────────────────────────
        float temperature = readTemperature();
        float humidity    = readHumidity();
        int   soilPct     = readSoilMoisture();
        float lightLux    = readLightLux();
        int   waterPct    = readWaterLevel();

        // ── 2. Pump control logic (hysteresis) ───────────────
        pumpOn = decidePump(soilPct, waterPct);
        digitalWrite(RELAY_PIN, pumpOn ? HIGH : LOW);

        // ── 3. LED indicator logic ────────────────────────────
        updateLEDs(soilPct, temperature, waterPct);

        // ── 4. Serial output (CSV format for logging) ────────
        printCSVReading(readingNum, soilPct, temperature,
                        humidity, lightLux, waterPct);

        // ── 5. Check thresholds and print alerts ──────────────
        checkThresholds(soilPct, temperature, humidity,
                        lightLux, waterPct);
    }
}

// ════════════════════════════════════════════════════════════
// Sensor Reading Functions
// ════════════════════════════════════════════════════════════

float readTemperature() {
    float t = dht.readTemperature();
    if (isnan(t)) {
        Serial.println("[ERROR] DHT22 Temperature read failed!");
        return -999.0;
    }
    return t;
}

float readHumidity() {
    float h = dht.readHumidity();
    if (isnan(h)) {
        Serial.println("[ERROR] DHT22 Humidity read failed!");
        return -999.0;
    }
    return h;
}

int readSoilMoisture() {
    // Average 5 readings to reduce noise
    long sum = 0;
    for (int i = 0; i < 5; i++) {
        sum += analogRead(SOIL_MOISTURE_PIN);
        delay(10);
    }
    int rawValue = sum / 5;

    // Map raw ADC to percentage (0% = dry, 100% = wet)
    int pct = map(rawValue, SOIL_DRY_VALUE, SOIL_WET_VALUE, 0, 100);
    return constrain(pct, 0, 100);
}

float readLightLux() {
    int rawLDR = analogRead(LDR_PIN);
    // Convert to approximate lux using inverse mapping
    // Higher ADC value → less resistance → more light
    // This is a simplified linear approximation
    float voltage = rawLDR * (5.0 / 1023.0);
    // Approximate lux: lux = 500 / (voltage + 0.01)
    // Calibrate this formula for your specific LDR
    if (voltage < 0.01) voltage = 0.01;
    float lux = 500.0 / voltage;
    return constrain(lux, 0.0, 100000.0);
}

int readWaterLevel() {
    int rawValue = analogRead(WATER_LEVEL_PIN);
    int pct = map(rawValue, WATER_EMPTY, WATER_FULL, 0, 100);
    return constrain(pct, 0, 100);
}

// ════════════════════════════════════════════════════════════
// Pump Control Logic (Hysteresis)
// ════════════════════════════════════════════════════════════

bool decidePump(int soilPct, int waterPct) {
    // Safety: stop pump if water tank is too low
    if (waterPct <= WATER_LEVEL_CRITICAL) {
        return false;
    }

    // Turn pump ON if soil is too dry
    if (soilPct <= SOIL_MOISTURE_LOW) {
        return true;
    }

    // Turn pump OFF if soil is sufficiently moist
    if (soilPct >= SOIL_MOISTURE_HIGH) {
        return false;
    }

    // Hysteresis zone: keep current state
    return pumpOn;
}

// ════════════════════════════════════════════════════════════
// LED Indicator Logic
// ════════════════════════════════════════════════════════════

void updateLEDs(int soilPct, float temp, int waterPct) {
    // RED: any critical condition
    bool critical = (soilPct < 10 || temp > TEMP_CRITICAL_HIGH ||
                     waterPct < WATER_LEVEL_CRITICAL);
    // YELLOW: warning condition
    bool warning = (soilPct < SOIL_MOISTURE_LOW || temp > TEMP_WARNING_HIGH ||
                    waterPct < WATER_LEVEL_LOW);

    if (critical) {
        digitalWrite(LED_RED,    HIGH);
        digitalWrite(LED_YELLOW, LOW);
        digitalWrite(LED_GREEN,  LOW);
    } else if (warning) {
        digitalWrite(LED_RED,    LOW);
        digitalWrite(LED_YELLOW, HIGH);
        digitalWrite(LED_GREEN,  LOW);
    } else {
        digitalWrite(LED_RED,    LOW);
        digitalWrite(LED_YELLOW, LOW);
        digitalWrite(LED_GREEN,  HIGH);
    }
}

// ════════════════════════════════════════════════════════════
// Serial Output — CSV Format for Data Logging
// ════════════════════════════════════════════════════════════

void printCSVReading(int id, int soil, float temp,
                     float humidity, float light, int water) {
    Serial.print(id);
    Serial.print(",");
    Serial.print(millis() / 1000);  // Seconds since boot
    Serial.print(",");
    Serial.print(soil);
    Serial.print(",");
    Serial.print(temp, 1);
    Serial.print(",");
    Serial.print(humidity, 1);
    Serial.print(",");
    Serial.print(light, 0);
    Serial.print(",");
    Serial.print(water);
    Serial.print(",");
    Serial.println(pumpOn ? "ON" : "OFF");
}

// ════════════════════════════════════════════════════════════
// Threshold Checking and Alert Generation
// ════════════════════════════════════════════════════════════

void checkThresholds(int soil, float temp, float humidity,
                     float light, int water) {
    // ── Soil Moisture ─────────────────────────────────────
    if (soil <= 10) {
        Serial.println("[CRITICAL] Soil moisture critically low! Crops wilting!");
    } else if (soil <= SOIL_MOISTURE_LOW) {
        Serial.println("[WARNING] Soil moisture low. Starting irrigation.");
    } else if (soil >= 95) {
        Serial.println("[CRITICAL] Soil moisture too high! Root rot risk!");
    } else if (soil >= 85) {
        Serial.println("[WARNING] Soil moisture high. Waterlogging risk.");
    }

    // ── Temperature ───────────────────────────────────────
    if (temp > 0 && temp <= TEMP_CRITICAL_HIGH && temp > TEMP_WARNING_HIGH) {
        Serial.print("[WARNING] High temperature: ");
        Serial.print(temp);
        Serial.println("°C — heat stress detected.");
    } else if (temp > TEMP_CRITICAL_HIGH) {
        Serial.print("[CRITICAL] Temperature ");
        Serial.print(temp);
        Serial.println("°C — crop damage risk!");
    }

    // ── Humidity ──────────────────────────────────────────
    if (humidity > 0 && humidity < HUMIDITY_LOW) {
        Serial.print("[WARNING] Low humidity: ");
        Serial.print(humidity);
        Serial.println("% — drought stress.");
    } else if (humidity > 95.0) {
        Serial.println("[WARNING] Very high humidity — fungal disease risk.");
    }

    // ── Water Level ───────────────────────────────────────
    if (water <= WATER_LEVEL_CRITICAL) {
        Serial.println("[CRITICAL] Water tank nearly empty! Pump stopped.");
    } else if (water <= WATER_LEVEL_LOW) {
        Serial.print("[WARNING] Water level low: ");
        Serial.print(water);
        Serial.println("% — refill tank soon.");
    }

    // ── Pump Status ───────────────────────────────────────
    Serial.print("[INFO] Pump: ");
    Serial.println(pumpOn ? "ON (Irrigating)" : "OFF (Standby)");
    Serial.println("--------------------------------------------");
}
