#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

BLEScan* pBLEScan;

void setup() {
  Serial.begin(115200);
  delay(1000); // give time for serial to stabilize
  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan();
  pBLEScan->setActiveScan(true);
}

void loop() {
  BLEScanResults* results = pBLEScan->start(2);

  for (int i = 0; i < results->getCount(); i++) {
    BLEAdvertisedDevice adv = results->getDevice(i);

    Serial.print("MAC: ");
    Serial.print(adv.getAddress().toString().c_str());
    Serial.print(" | RSSI: ");
    Serial.println(adv.getRSSI());
  }

  Serial.println("----");

  pBLEScan->clearResults();
  delay(1000);
}
