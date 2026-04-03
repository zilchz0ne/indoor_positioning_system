#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>

void setup() {
  BLEDevice::init("TargetESP");
  BLEServer *pServer = BLEDevice::createServer();
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->start(); // broadcast BLE
}

void loop() {
  delay(1000); // nothing else needed
}
