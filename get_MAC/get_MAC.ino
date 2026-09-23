#include <WiFi.h>

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    // Wi-Fi must be initialized to read the hardware MAC
    WiFi.mode(WIFI_MODE_STA); 
    
    Serial.println("\n----------------------------------");
    Serial.print("ESP32 MAC Address: ");
    Serial.println(WiFi.macAddress());
    Serial.println("----------------------------------");
}

void loop() {
    Serial.println(WiFi.macAddress());
    delay(1000);
}
