#include <BLEDevice.h>
#include <BLEScan.h>
#include <math.h>

BLEScan* pBLEScan;

// ---------------- GLOBAL RSSI ----------------
int rssi_A = -100;
int rssi_B = -100;
int rssi_C = -100;

// ---------------- MAC ADDRESSES ----------------
const String MAC_A = "68:fe:71:8b:45:b6";
const String MAC_B = "b0:cb:d8:ce:24:aa";
const String MAC_C = "68:fe:71:8b:4c:6e";

// ---------------- CONFIG ----------------
const float TX_POWER = -59.0;
const float PATH_LOSS = 2.5;

// ---------------- RSSI → DISTANCE ----------------
float rssiToDistance(int rssi)
{
    return pow(10.0, (TX_POWER - rssi) / (10.0 * PATH_LOSS));
}

// ---------------- UPDATE RSSI (5 sec avg) ----------------
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

            String mac = device.getAddress().toString();
            int rssi = device.getRSSI();

            if (mac == MAC_A)
            {
                sumA += rssi;
                countA++;
            }
            else if (mac == MAC_B)
            {
                sumB += rssi;
                countB++;
            }
            else if (mac == MAC_C)
            {
                sumC += rssi;
                countC++;
            }
        }

        pBLEScan->clearResults();
    }

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

    Serial.println("MAC-based RSSI Scanner Started");
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
