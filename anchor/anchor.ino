#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEAdvertising.h>

void setup() {
  // Initialize BLE without a public name to keep packets small and fast
  BLEDevice::init("");
  
  // Create the server and get the advertising pointer
  BLEServer *pServer = BLEDevice::createServer();
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  
  // Start advertising the empty packet (its unique MAC address is automatically attached)
  pAdvertising->start();
}

void loop() {
  // Intentionally left blank. The hardware handles BLE advertising in the background.
  delay(1000); 
}
