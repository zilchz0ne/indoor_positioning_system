/*
 * IPS Target Node - 1-Foot RSSI Calibration Tool
 * -----------------------------------------------
 * Calibrates the TxPower (reference RSSI at 1.0 ft) for each anchor node one by one.
 * 
 * Hardware setup:
 * 1. Keep Anchor firmware unchanged (standard BLE advertiser).
 * 2. Place the target node and the selected anchor exactly 1 foot (12 inches) apart.
 * 3. Keep other anchors turned off or at least 10+ feet away to avoid signal confusion.
 * 4. Open Serial Monitor at 115200 baud.
 * 5. Type '1', '2', '3', or '4' in Serial to select which anchor you are testing.
 * 6. Collects 50 samples and outputs the exact calibrated 'tx' value and ready-to-paste CSV.
 */

#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include <math.h>

struct Anchor {
  const char* name;
  const char* mac;
  float x;
  float y;
  int sampleCount;
  long rssiSum;
  long rssiSqSum;
  int minRssi;
  int maxRssi;
  float calibratedTx;
  bool isCalibrated;
};

// Anchors matching server/anchor_config.csv
#define NUM_ANCHORS 4
Anchor anchors[NUM_ANCHORS] = {
  {"Anchor_A", "68:fe:71:8b:45:b6", 0.0, 0.0, 0, 0, 0, 999, -999, -59.0, false},
  {"Anchor_B", "68:fe:71:8b:4c:6e", 0.0, 4.0, 0, 0, 0, 999, -999, -59.0, false},
  {"Anchor_C", "00:4b:12:9a:f9:3e", 4.0, 0.0, 0, 0, 0, 999, -999, -59.0, false},
  {"Anchor_D", "20:e7:c8:69:2a:5a", 4.0, 4.0, 0, 0, 0, 999, -999, -59.0, false}
};

const int TARGET_SAMPLES = 50;

// -1 means listen to whichever anchor is active / all; 0..3 targets specific anchor
int selectedAnchorIdx = 0; 

BLEScan* scanner = nullptr;

void resetAnchorStats(int idx) {
  if (idx < 0 || idx >= NUM_ANCHORS) return;
  anchors[idx].sampleCount = 0;
  anchors[idx].rssiSum = 0;
  anchors[idx].rssiSqSum = 0;
  anchors[idx].minRssi = 999;
  anchors[idx].maxRssi = -999;
  anchors[idx].isCalibrated = false;
  Serial.printf("\n[RESET] Cleared data for %s (%s). Place at 1 ft and begin.\n", 
                anchors[idx].name, anchors[idx].mac);
}

void printMenu() {
  Serial.println("\n=======================================================");
  Serial.println("         IPS TARGET - 1-FOOT RSSI CALIBRATION          ");
  Serial.println("=======================================================");
  Serial.println("Commands:");
  Serial.println("  1 -> Calibrate Anchor_A (0.0, 0.0)");
  Serial.println("  2 -> Calibrate Anchor_B (0.0, 4.0)");
  Serial.println("  3 -> Calibrate Anchor_C (4.0, 0.0)");
  Serial.println("  4 -> Calibrate Anchor_D (4.0, 4.0)");
  Serial.println("  0 -> Listen to ALL registered anchors");
  Serial.println("  r -> Reset samples for current anchor");
  Serial.println("  p -> Print current anchor_config.csv output");
  Serial.printf("Currently Selected: %s (%s)\n", 
                (selectedAnchorIdx >= 0) ? anchors[selectedAnchorIdx].name : "ALL ANCHORS",
                (selectedAnchorIdx >= 0) ? anchors[selectedAnchorIdx].mac : "*");
  Serial.println("=======================================================\n");
}

void printCsvSummary() {
  Serial.println("\n-------------------------------------------------------");
  Serial.println("COPY-PASTE READY: server/anchor_config.csv");
  Serial.println("-------------------------------------------------------");
  Serial.println("mac,name,x,y,tx,n");
  for (int i = 0; i < NUM_ANCHORS; i++) {
    float txVal = anchors[i].isCalibrated ? anchors[i].calibratedTx : -59.0;
    Serial.printf("%s,%s,%.1f,%.1f,%.1f,2.0\n", 
                  anchors[i].mac, anchors[i].name, anchors[i].x, anchors[i].y, txVal);
  }
  Serial.println("-------------------------------------------------------\n");
}

int findAnchorIndex(const String& mac) {
  for (int i = 0; i < NUM_ANCHORS; i++) {
    if (mac.equalsIgnoreCase(anchors[i].mac)) {
      return i;
    }
  }
  return -1;
}

void processSample(int idx, int rssi) {
  Anchor& a = anchors[idx];
  
  if (a.sampleCount >= TARGET_SAMPLES) {
    return; // Already reached target count
  }

  a.sampleCount++;
  a.rssiSum += rssi;
  a.rssiSqSum += (long)rssi * rssi;
  if (rssi < a.minRssi) a.minRssi = rssi;
  if (rssi > a.maxRssi) a.maxRssi = rssi;

  float currentAvg = (float)a.rssiSum / a.sampleCount;

  Serial.printf("  [%s] Sample %2d/%2d -> Instant: %3d dBm | Avg so far: %5.1f dBm\n",
                a.name, a.sampleCount, TARGET_SAMPLES, rssi, currentAvg);

  if (a.sampleCount == TARGET_SAMPLES) {
    float mean = currentAvg;
    float variance = ((float)a.rssiSqSum / a.sampleCount) - (mean * mean);
    float stdDev = (variance > 0) ? sqrt(variance) : 0.0;

    a.calibratedTx = round(mean * 10.0) / 10.0;
    a.isCalibrated = true;

    Serial.println("\n*******************************************************");
    Serial.printf(" [SUCCESS] Calibration Complete for %s (%s)\n", a.name, a.mac);
    Serial.printf(" Measured at Distance : 1.0 ft\n");
    Serial.printf(" Calibrated Tx Power  : %.1f dBm  <-- Use as 'tx' in config\n", a.calibratedTx);
    Serial.printf(" Signal Stability     : StdDev ± %.2f dBm (Min: %d, Max: %d)\n", stdDev, a.minRssi, a.maxRssi);
    Serial.println("*******************************************************\n");
    
    // Auto advance to next uncalibrated anchor if in sequential mode
    if (selectedAnchorIdx >= 0 && selectedAnchorIdx < NUM_ANCHORS - 1) {
      Serial.printf("Tip: Now turn off/move %s, place %s at 1 ft, and type '%d'\n\n",
                    a.name, anchors[selectedAnchorIdx + 1].name, selectedAnchorIdx + 2);
    } else {
      printCsvSummary();
    }
  }
}

void handleSerialInput() {
  if (!Serial.available()) return;
  char cmd = Serial.read();

  if (cmd == '1') {
    selectedAnchorIdx = 0;
    resetAnchorStats(0);
  } else if (cmd == '2') {
    selectedAnchorIdx = 1;
    resetAnchorStats(1);
  } else if (cmd == '3') {
    selectedAnchorIdx = 2;
    resetAnchorStats(2);
  } else if (cmd == '4') {
    selectedAnchorIdx = 3;
    resetAnchorStats(3);
  } else if (cmd == '0') {
    selectedAnchorIdx = -1;
    Serial.println("\n[MODE] Listening to ALL anchors simultaneously.");
  } else if (cmd == 'r' || cmd == 'R') {
    if (selectedAnchorIdx >= 0) {
      resetAnchorStats(selectedAnchorIdx);
    } else {
      for (int i = 0; i < NUM_ANCHORS; i++) resetAnchorStats(i);
    }
  } else if (cmd == 'p' || cmd == 'P') {
    printCsvSummary();
  } else if (cmd == 'm' || cmd == 'M' || cmd == '?') {
    printMenu();
  }
}

void setup() {
  Serial.begin(115200);
  delay(1500);

  // Note: Wi-Fi is purposely NOT started here.
  // Running BLE alone prevents 2.4 GHz RF co-channel interference from Wi-Fi!
  BLEDevice::init("");
  scanner = BLEDevice::getScan();
  scanner->setActiveScan(true);
  scanner->setInterval(100);
  scanner->setWindow(99);

  printMenu();
}

void loop() {
  handleSerialInput();

  // Scan BLE for 1 second burst
  BLEScanResults* results = scanner->start(1, false);

  if (results != nullptr) {
    for (int i = 0; i < results->getCount(); i++) {
      BLEAdvertisedDevice device = results->getDevice(i);
      String mac = device.getAddress().toString().c_str();
      int rssi = device.getRSSI();

      int anchorIdx = findAnchorIndex(mac);
      if (anchorIdx >= 0) {
        // If we are filtering for a specific anchor, only accept that anchor's packets
        if (selectedAnchorIdx == -1 || selectedAnchorIdx == anchorIdx) {
          processSample(anchorIdx, rssi);
        }
      }
    }
    scanner->clearResults();
  }

  delay(50);
}
