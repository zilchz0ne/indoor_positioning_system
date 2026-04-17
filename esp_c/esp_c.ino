#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEBeacon.h>
#include <BLEAdvertising.h>

#define UUID "12345678-1234-1234-1234-1234567890ab"

void setup()
{
    Serial.begin(115200);

    BLEDevice::init("Anchor_C"); // change name per anchor

    BLEBeacon beacon;
    beacon.setManufacturerId(0x4C00); // Apple format (works well)
    beacon.setProximityUUID(BLEUUID(UUID));
    beacon.setMajor(1);  // change per anchor
    beacon.setMinor(3);  // change per anchor
    beacon.setSignalPower(-59); // TX power at 1m (calibration)

    BLEAdvertisementData advData;
    advData.setFlags(0x04);
    advData.setManufacturerData(beacon.getData());

    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->setAdvertisementData(advData);
    pAdvertising->start();

    Serial.println("Anchor started...");
}

void loop()
{
    delay(1000);
}
