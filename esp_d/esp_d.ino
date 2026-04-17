#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include <map>
#include <vector>
#include <math.h>

BLEScan* pBLEScan;

// ---------------- CONFIG ----------------
const float L = 1.0;
const float TX_POWER = -59.0;
const float PATH_LOSS = 2.5;

const int GRID_RES = 20;

// ---------------- DATA ----------------
std::map<String, std::vector<int>> history;

// last known distances (IMPORTANT FIX)
float dA = -1, dB = -1, dC = -1;

// ---------------- RSSI ----------------
void addRSSI(String name, int rssi)
{
    auto &v = history[name];
    v.push_back(rssi);
    if (v.size() > 10) v.erase(v.begin());
}

float smooth(String name)
{
    auto &v = history[name];
    if (v.empty()) return -100;

    int sum = 0;
    for (int x : v) sum += x;

    return (float)sum / v.size();
}

float toDistance(float rssi)
{
    return pow(10.0, (TX_POWER - rssi) / (10.0 * PATH_LOSS));
}

// ---------------- GRID SEARCH ----------------
void computePosition()
{
    float bestX = 0, bestY = 0;
    float bestErr = 1e9;

    float step = L / GRID_RES;

    for (float x = 0; x <= L; x += step)
    {
        for (float y = 0; y <= L; y += step)
        {
            float pA = sqrt(x*x + y*y);
            float pB = sqrt((x-L)*(x-L) + y*y);
            float pC = sqrt(x*x + (y-L)*(y-L));

            float e =
                fabs(pA - dA) +
                fabs(pB - dB) +
                fabs(pC - dC);

            if (e < bestErr)
            {
                bestErr = e;
                bestX = x;
                bestY = y;
            }
        }
    }

    Serial.print("POSITION → x: ");
    Serial.print(bestX);
    Serial.print(" y: ");
    Serial.print(bestY);
    Serial.print(" error: ");
    Serial.println(bestErr);
}

// ---------------- SETUP ----------------
void setup()
{
    Serial.begin(115200);

    BLEDevice::init("");
    pBLEScan = BLEDevice::getScan();
    pBLEScan->setActiveScan(true);

    Serial.println("V1 FIXED Positioning System");
}

// ---------------- LOOP ----------------
void loop()
{
    float localA = -1;
    float localB = -1;
    float localC = -1;

    BLEScanResults* results = pBLEScan->start(2, false);

    for (int i = 0; i < results->getCount(); i++)
    {
        BLEAdvertisedDevice device = results->getDevice(i);

        String name = device.getName();
        int rssi = device.getRSSI();

        if (name == "Anchor_A" || name == "Anchor_B" || name == "Anchor_C")
        {
            addRSSI(name, rssi);

            float r = smooth(name);
            float d = toDistance(r);

            if (name == "Anchor_A") localA = d;
            if (name == "Anchor_B") localB = d;
            if (name == "Anchor_C") localC = d;
        }
    }

    pBLEScan->clearResults();

    // ONLY compute if ALL 3 found in SAME scan cycle
    if (localA > 0 && localB > 0 && localC > 0)
    {
        dA = localA;
        dB = localB;
        dC = localC;

        computePosition();
    }

    Serial.println("----");
}
