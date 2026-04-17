#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEAdvertising.h>

void setup()
{
    BLEDevice::init("Anchor_A");
    BLEDevice::createServer();
    BLEDevice::getAdvertising()->start();
}

void loop() {}
