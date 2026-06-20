#include <WiFi.h>
#include <WiFiUdp.h>
#include <BLEDevice.h>
#include <BLEScan.h>

// Network Credentials
const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASS";

// Target Identifier (Change this per human-worn target node, e.g., "T1", "T2")
const String TARGET_ID = "T1"; 

// UDP Settings
WiFiUDP udp;
const int UDP_PORT = 4210;
IPAddress broadcastIP(255, 255, 255, 255);

BLEScan* pBLEScan;

// Callback class that fires INSTANTLY whenever a BLE device is spotted
class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks {
    void onResult(BLEAdvertisedDevice advertisedDevice) {
        String mac = advertisedDevice.getAddress().toString();
        int rssi = advertisedDevice.getRSSI();

        // Construct a clean, tiny CSV string: TARGET,MAC,RSSI
        String payload = TARGET_ID + "," + mac + "," + String(rssi);

        // Blast it over UDP Broadcast immediately
        udp.beginPacket(broadcastIP, UDP_PORT);
        udp.print(payload);
        udp.endPacket();
    }
};

void setup() {
    Serial.begin(115200);

    // Connect to Wi-Fi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(200);
    }

    // Initialize UDP
    udp.begin(UDP_PORT);

    // Initialize BLE Scanning as an asynchronous stream
    BLEDevice::init("");
    pBLEScan = BLEDevice::getScan();
    pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
    pBLEScan->setActiveScan(true);
    
    // Start continuous, non-blocking scanning (0 means scan forever)
    pBLEScan->start(0, nullptr, false); 
}

void loop() {
    // The loop stays entirely empty. 
    // The BLE callback handles data capture and Wi-Fi streaming asynchronously.
    delay(1000);
}
