#include <BLEDevice.h>
#include <BLEScan.h>

BLEScan* pBLEScan;

// ---------------- GLOBAL RSSI ----------------
int rssi_A = -100;
int rssi_B = -100;
int rssi_C = -100;

// ---------------- CONFIG ----------------
const float TX_POWER = -59.0;
const float PATH_LOSS = 2.5;

// ---------------- RSSI → DISTANCE ----------------
float rssiToDistance(int rssi)
{
    return pow(10.0, (TX_POWER - rssi) / (10.0 * PATH_LOSS));
}

// ---------------- UPDATE RSSI ----------------
void updateRSSI()
{
    unsigned long start = millis();

    while (millis() - start < 5000)   // 5 seconds
    {
        BLEScanResults* results = pBLEScan->start(1, false);

        for (int i = 0; i < results->getCount(); i++)
        {
            BLEAdvertisedDevice device = results->getDevice(i);

            String name = device.getName();
            int rssi = device.getRSSI();

            if (name == "Anchor_A")
                rssi_A = rssi;

            else if (name == "Anchor_B")
                rssi_B = rssi;

            else if (name == "Anchor_C")
                rssi_C = rssi;
        }

        pBLEScan->clearResults();
    }
}

// ---------------- SETUP ----------------
void setup()
{
    Serial.begin(115200);

    BLEDevice::init("");
    pBLEScan = BLEDevice::getScan();
    pBLEScan->setActiveScan(true);

    Serial.println("RSSI Collector Started");
}

// ---------------- LOOP ----------------
void loop()
{
    updateRSSI();

    Serial.println("---- RSSI VALUES ----");
    Serial.print("A: "); Serial.println(rssi_A);
    Serial.print("B: "); Serial.println(rssi_B);
    Serial.print("C: "); Serial.println(rssi_C);

    Serial.println("---- DISTANCES ----");
    Serial.print("A: "); Serial.println(rssiToDistance(rssi_A));
    Serial.print("B: "); Serial.println(rssiToDistance(rssi_B));
    Serial.print("C: "); Serial.println(rssiToDistance(rssi_C));

    Serial.println("---------------------");
}
