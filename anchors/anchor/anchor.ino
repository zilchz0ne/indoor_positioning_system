#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEAdvertising.h>

void setup() {
  // Empty name keeps BLE packets small
  BLEDevice::init("");
  BLEDevice::createServer();
  BLEDevice::getAdvertising()->start();
}

void loop() {
  delay(1000);
}
