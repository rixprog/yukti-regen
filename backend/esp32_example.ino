/*
 * ESP32 Carbon Footprint Monitor
 * 
 * This example code shows how to send energy consumption data
 * from an ESP32 with ACS712 current sensor and a 9W bulb
 * to the Carbon Footprint Visualizer backend via UDP.
 * 
 * Hardware:
 * - ESP32 Dev Board
 * - ACS712 Current Sensor (30A version)
 * - 9W LED Bulb
 * - Resistors for voltage divider (if needed)
 * 
 * Connections:
 * - ACS712 VCC -> 5V
 * - ACS712 GND -> GND
 * - ACS712 OUT -> GPIO34 (ADC1_CH6)
 * - 9W Bulb connected to relay or directly to power
 */

#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server details
const char* serverIP = "192.168.1.100";  // Change to your server IP
const int serverPort = 8888;

// Hardware pins
const int ACS712_PIN = 34;  // ADC pin for current sensor
const int RELAY_PIN = 2;    // Pin for controlling the bulb

// Calibration values for ACS712-30A
const float ACS712_SENSITIVITY = 0.066;  // 66mV/A for 30A version
const float ACS712_OFFSET = 2.5;         // 2.5V offset
const float VOLTAGE_REF = 3.3;           // ESP32 reference voltage

// Measurement variables
float current = 0.0;
float power = 0.0;
unsigned long startTime;
unsigned long duration;
bool bulbOn = false;

// UDP
WiFiUDP udp;

void setup() {
  Serial.begin(115200);
  
  // Initialize pins
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  
  // Start UDP
  udp.begin(serverPort);
  
  Serial.println("ESP32 Carbon Footprint Monitor Ready!");
  Serial.println("Commands:");
  Serial.println("1. Send 'start' to begin monitoring");
  Serial.println("2. Send 'stop' to stop monitoring");
  Serial.println("3. Send 'status' to check current status");
}

void loop() {
  // Check for serial commands
  if (Serial.available()) {
    String command = Serial.readString();
    command.trim();
    
    if (command == "start") {
      startMonitoring();
    } else if (command == "stop") {
      stopMonitoring();
    } else if (command == "status") {
      sendStatus();
    }
  }
  
  // If monitoring, take measurements
  if (bulbOn) {
    measureCurrent();
    delay(1000);  // Measure every second
  }
  
  delay(100);
}

void startMonitoring() {
  if (!bulbOn) {
    digitalWrite(RELAY_PIN, HIGH);  // Turn on bulb
    bulbOn = true;
    startTime = millis();
    Serial.println("Monitoring started - Bulb turned ON");
  } else {
    Serial.println("Already monitoring!");
  }
}

void stopMonitoring() {
  if (bulbOn) {
    digitalWrite(RELAY_PIN, LOW);   // Turn off bulb
    bulbOn = false;
    duration = millis() - startTime;
    
    // Calculate total energy consumption
    float totalEnergy = (power * duration) / (1000.0 * 3600.0);  // Convert to kWh
    float durationHours = duration / 3600000.0;  // Convert to hours
    
    // Send data to server
    sendEnergyData(power, durationHours, totalEnergy);
    
    Serial.println("Monitoring stopped - Bulb turned OFF");
    Serial.printf("Duration: %.2f hours\n", durationHours);
    Serial.printf("Power: %.2f W\n", power);
    Serial.printf("Energy: %.4f kWh\n", totalEnergy);
  } else {
    Serial.println("Not currently monitoring!");
  }
}

void measureCurrent() {
  // Read analog value from ACS712
  int rawValue = analogRead(ACS712_PIN);
  float voltage = (rawValue * VOLTAGE_REF) / 4095.0;  // Convert to voltage
  
  // Calculate current (A)
  current = (voltage - ACS712_OFFSET) / ACS712_SENSITIVITY;
  
  // Calculate power (W) - assuming 220V for the bulb
  // For a 9W bulb, this should read approximately 0.041A
  power = current * 220.0;  // P = I * V
  
  // Update running average for more stable readings
  static float powerSum = 0;
  static int sampleCount = 0;
  
  powerSum += power;
  sampleCount++;
  
  if (sampleCount >= 10) {  // Average over 10 samples
    power = powerSum / sampleCount;
    powerSum = 0;
    sampleCount = 0;
  }
  
  // Print current measurement
  Serial.printf("Current: %.3f A, Power: %.2f W\n", current, power);
}

void sendEnergyData(float powerWatts, float durationHours, float energyKwh) {
  // Create JSON payload
  DynamicJsonDocument doc(1024);
  doc["type"] = "energy";
  doc["device_id"] = "esp32_001";
  doc["power_watts"] = powerWatts;
  doc["duration_hours"] = durationHours;
  doc["energy_kwh"] = energyKwh;
  doc["timestamp"] = getCurrentTimestamp();
  
  // Convert to string
  String jsonString;
  serializeJson(doc, jsonString);
  
  // Send via UDP
  udp.beginPacket(serverIP, serverPort);
  udp.write((uint8_t*)jsonString.c_str(), jsonString.length());
  udp.endPacket();
  
  Serial.println("Energy data sent to server:");
  Serial.println(jsonString);
}

void sendStatus() {
  DynamicJsonDocument doc(512);
  doc["type"] = "status";
  doc["device_id"] = "esp32_001";
  doc["bulb_on"] = bulbOn;
  doc["current_power"] = power;
  doc["uptime"] = millis();
  doc["timestamp"] = getCurrentTimestamp();
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  udp.beginPacket(serverIP, serverPort);
  udp.write((uint8_t*)jsonString.c_str(), jsonString.length());
  udp.endPacket();
  
  Serial.println("Status sent to server:");
  Serial.println(jsonString);
}

String getCurrentTimestamp() {
  // Get current time (you might want to use NTP for accurate time)
  unsigned long currentTime = millis();
  unsigned long seconds = currentTime / 1000;
  unsigned long minutes = seconds / 60;
  unsigned long hours = minutes / 60;
  
  // Simple timestamp format (you should use proper date/time)
  return String(hours) + ":" + String(minutes % 60) + ":" + String(seconds % 60);
}

/*
 * Example JSON messages sent to server:
 * 
 * Energy data:
 * {
 *   "type": "energy",
 *   "device_id": "esp32_001",
 *   "power_watts": 9.2,
 *   "duration_hours": 2.5,
 *   "energy_kwh": 0.023,
 *   "timestamp": "2024-01-15T14:30:00"
 * }
 * 
 * Status:
 * {
 *   "type": "status",
 *   "device_id": "esp32_001",
 *   "bulb_on": true,
 *   "current_power": 9.2,
 *   "uptime": 3600000,
 *   "timestamp": "2024-01-15T14:30:00"
 * }
 */
