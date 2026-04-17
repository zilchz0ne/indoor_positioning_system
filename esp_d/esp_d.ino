#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <map>
#include <vector>
#include <string>
#include <math.h>

BLEScan* pBLEScan;

// ---------------- CONFIG ----------------
const float TX_POWER = -59.0;   // calibration at 1m
const float PATH_LOSS = 2.5;    // indoor environment

// ---------------- DATA STORAGE ----------------
std::map<String, std::vector<int>> rssiHistory;

// ---------------- UTIL: ADD RSSI ----------------
void addRSSI(String name, int rssi)
{
    std::vector<int>& v = rssiHistory[name];

    v.push_back(rssi);

    // keep last 10 values only
    if (v.size() > 10)
    {
        v.erase(v.begin());
    }
}

// ---------------- UTIL: SMOOTH RSSI ----------------
float getSmoothedRSSI(String name)
{
    std::vector<int>& v = rssiHistory[name];

    if (v.size() == 0)
        return -100;

    int sum = 0;
    for (int x : v)
    {
        sum += x;
    }

    return (float)sum / v.size();
}

// ---------------- UTIL: RSSI → DISTANCE ----------------
float rssiToDistance(float rssi)
{
    return pow(10.0, (TX_POWER - rssi) / (10.0 * PATH_LOSS));
}

// ---------------- SETUP ----------------
void setup()
{
    Serial.begin(115200);

    BLEDevice::init("");
    pBLEScan = BLEDevice::getScan();
    pBLEScan->setActiveScan(true);

    Serial.println("Scanner started...");
}

// ---------------- LOOP ----------------
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
            addRSSI(name, rssi);

            float smooth = getSmoothedRSSI(name);
            float dist = rssiToDistance(smooth);

            Serial.print(name);
            Serial.print(" | RSSI: ");
            Serial.print(rssi);
            Serial.print(" | Smooth: ");
            Serial.print(smooth);
            Serial.print(" | Dist: ");
            Serial.println(dist);
        }
    }

    Serial.println("----");

    pBLEScan->clearResults();
}
