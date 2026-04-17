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

    float sumA = 0, sumB = 0, sumC = 0;
    int countA = 0, countB = 0, countC = 0;

    while (millis() - start < 5000)
    {
        BLEScanResults* results = pBLEScan->start(1, false);

        for (int i = 0; i < results->getCount(); i++)
        {
            BLEAdvertisedDevice device = results->getDevice(i);

            String name = device.getName();
            int rssi = device.getRSSI();

            if (name == "Anchor_A")
            {
                sumA += rssi;
                countA++;
            }
            else if (name == "Anchor_B")
            {
                sumB += rssi;
                countB++;
            }
            else if (name == "Anchor_C")
            {
                sumC += rssi;
                countC++;
            }
        }

        pBLEScan->clearResults();
    }

    // update globals (keep previous if nothing found)
    if (countA > 0) rssi_A = sumA / countA;
    if (countB > 0) rssi_B = sumB / countB;
    if (countC > 0) rssi_C = sumC / countC;
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
