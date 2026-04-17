#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>

BLEScan* pBLEScan;

void setup()
{
    Serial.begin(115200);

    BLEDevice::init("");
    pBLEScan = BLEDevice::getScan();
    pBLEScan->setActiveScan(true);
}

void loop()
{
    BLEScanResults* results = pBLEScan->start(2, false);

    for (int i = 0; i < results->getCount(); i++)
    {
        BLEAdvertisedDevice device = results->getDevice(i);

        String name = device.getName();
        int rssi = device.getRSSI();

        if (name == "Anchor_A" || name == "Anchor_B" || name == "Anchor_C")
        {
            Serial.print("Found: ");
            Serial.print(name);
            Serial.print(" | RSSI: ");
            Serial.println(rssi);
        }
    }

    Serial.println("----");
}
