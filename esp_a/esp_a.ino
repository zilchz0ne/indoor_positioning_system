#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

BLEScan* pBLEScan;

void setup() {
  Serial.begin(115200);
  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan(); // create BLE scanner
  pBLEScan->setActiveScan(true); // active scan for RSSI
}

void loop() {
  BLEScanResults results = pBLEScan->start(2); // scan 2 seconds
  for (int i = 0; i < results.getCount(); i++) {
    BLEAdvertisedDevice adv = results.getDevice(i);
    if (adv.getName() == "TargetESP") {
      Serial.print("RSSI: ");
      Serial.println(adv.getRSSI());
    }
  }
  pBLEScan->clearResults(); // clear for next loop
  delay(500);
}
