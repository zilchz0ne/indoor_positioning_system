/*
 * IPS Target Node
 * ---------------
 * 1. Connect to WiFi
 * 2. Scan for BLE anchors every few seconds
 * 3. Send raw readings to the network:  TARGET_ID,ANCHOR_MAC,RSSI
 * 4. UDP broadcast on port 4210 (server listens; no target config needed)
 *
 * All positioning math happens on the Python server, not here.
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

// --- Anchor MACs (must match server.py ANCHOR_MAP) ---
const char* ANCHOR_MACS[] = {
  "68:fe:71:8b:45:b6",   // Anchor A
  "68:fe:71:8b:4c:6e",   // Anchor B
  "b0:cb:d8:cd:33:16",   // Anchor C
};
const int NUM_ANCHORS = 3;

BLEScan* scanner = nullptr;

// Returns anchor index 0..2, or -1 if MAC is not one of our anchors
int findAnchorIndex(const String& mac) {
  String m = mac;
  m.toLowerCase();
  for (int i = 0; i < NUM_ANCHORS; i++) {
    if (m.equals(ANCHOR_MACS[i])) return i;
  }
  return -1;
}

// Broadcast one reading:  T1,68:fe:71:8b:45:b6,-65
void sendReading(const char* anchorMac, int rssi) {
  char packet[64];
  snprintf(packet, sizeof(packet), "%s,%s,%d", TARGET_ID, anchorMac, rssi);

  udp.beginPacket(IPAddress(255, 255, 255, 255), UDP_PORT);
  udp.write((uint8_t*)packet, strlen(packet));
  udp.endPacket();

  Serial.printf("UDP -> %s\n", packet);
}

bool connectWifi() {
  Serial.printf("WiFi: connecting to '%s'...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  for (int i = 0; i < 40; i++) {  // 20 second timeout
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
  delay(1500);  // let USB serial settle (avoids garbage on monitor open)
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

  Serial.println("BLE scan ready. Starting loop...");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi lost — reconnecting...");
    connectWifi();
  }

  // Blocking scan: simple, safe (WiFi + UDP only run in main loop)
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
    int idx = findAnchorIndex(device.getAddress().toString());
    if (idx >= 0) {
      sendReading(ANCHOR_MACS[idx], device.getRSSI());
      sent++;
    }
  }

  scanner->clearResults();
  Serial.printf("Scan done: %d devices seen, %d anchor packets sent\n\n", results->getCount(), sent);

  delay(200);
}
