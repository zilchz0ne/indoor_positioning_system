#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>

BLEScan* pBLEScan;

String targetMAC = "50:55:54:fc:9d:cb";

void setup() {
  Serial.begin(115200);
  delay(1000);

  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan();
  pBLEScan->setActiveScan(true);
}

void loop() {
  BLEScanResults* results = pBLEScan->start(2);

  for (int i = 0; i < results->getCount(); i++) {
    BLEAdvertisedDevice adv = results->getDevice(i);

    String mac = String(adv.getAddress().toString().c_str());

    if (mac == targetMAC || mac == "47:d1:fa:c9:e9:91") {
      Serial.print("TARGET RSSI: ");
      Serial.println(adv.getRSSI());
    }
  }

  Serial.println("----");

  pBLEScan->clearResults();
  delay(500);
}
