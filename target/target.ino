/*
 * IPS Target Node
 * ---------------
 * 1. Connect to WiFi
 * 2. Scan for BLE devices every few seconds
 * 3. Forward every reading:  TARGET_ID,MAC,RSSI
 * 4. UDP broadcast on port 4210
 *
 * Anchor MACs are NOT configured here — the Python server decides which
 * MACs are anchors. Add new anchors in server.py only; no target re-flash.
 */

#include <WiFi.h>
#include <WiFiUdp.h>
#include <BLEDevice.h>
#include <BLEScan.h>

// --- WiFi (edit before upload) ---
const char* WIFI_SSID     = "YOUR_WIFI";
const char* WIFI_PASSWORD = "YOUR_PASS";

// --- Target label sent in every packet ---
const char* TARGET_ID = "T1";

// --- UDP ---
const int UDP_PORT = 4210;
WiFiUDP udp;

// Ignore very weak BLE signals (phones far away, etc.) — no MAC list needed
const int RSSI_MIN = -85;

BLEScan* scanner = nullptr;

// Broadcast one reading:  T1,68:fe:71:8b:45:b6,-65
void sendReading(const char* mac, int rssi) {
  char packet[64];
  snprintf(packet, sizeof(packet), "%s,%s,%d", TARGET_ID, mac, rssi);

  udp.beginPacket(IPAddress(255, 255, 255, 255), UDP_PORT);
  udp.write((uint8_t*)packet, strlen(packet));
  udp.endPacket();

  Serial.printf("UDP -> %s\n", packet);
}

bool connectWifi() {
  Serial.printf("WiFi: connecting to '%s'...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  for (int i = 0; i < 40; i++) {
    if (WiFi.status() == WL_CONNECTED) {
      Serial.printf("WiFi: connected, IP=%s\n", WiFi.localIP().toString().c_str());
      return true;
    }
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi: FAILED (check SSID/password)");
  return false;
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println();
  Serial.println("=== IPS Target ===");

  if (!connectWifi()) {
    Serial.println("Halting. Fix WiFi and reset.");
    while (true) delay(1000);
  }

  udp.begin(UDP_PORT);

  BLEDevice::init("");
  scanner = BLEDevice::getScan();
  scanner->setActiveScan(true);

  Serial.println("BLE scan ready (server filters anchor MACs).");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi lost — reconnecting...");
    connectWifi();
  }

  Serial.println("BLE scan...");
  BLEScanResults* results = scanner->start(3, false);

  if (results == nullptr) {
    Serial.println("BLE scan failed — retrying...");
    delay(1000);
    return;
  }

  int sent = 0;
  for (int i = 0; i < results->getCount(); i++) {
    BLEAdvertisedDevice device = results->getDevice(i);
    int rssi = device.getRSSI();
    if (rssi >= RSSI_MIN) {
      sendReading(device.getAddress().toString().c_str(), rssi);
      sent++;
    }
  }

  scanner->clearResults();
  Serial.printf("Scan done: %d devices seen, %d packets sent\n\n", results->getCount(), sent);

  delay(200);
}
