#include <BLEDevice.h>
#include <BLEScan.h>
#include <math.h>

BLEScan* pBLEScan;

// ---------------- MAC ADDRESSES ----------------
const String MAC_A = "68:fe:71:8b:45:b6";
const String MAC_C = "68:fe:71:8b:4c:6e";

// ---------------- GLOBAL RSSI ----------------
int rssi_A = -100;
int rssi_C = -100;

// ---------------- CALIBRATION (your measured 1m RSSI) ----------------
const float TX_A = -68;
const float TX_C = -73;

const float N_A = 2.5;
const float N_C = 2.5;

// ---------------- DISTANCE LIMITS ----------------
float clampDist(float d)
{
    if (d < 0.2) return 0.2;
    if (d > 5.0) return 5.0;
    return d;
}

// ---------------- RSSI → DISTANCE ----------------
float distA(int rssi)
{
    return pow(10.0, (TX_A - rssi) / (10.0 * N_A));
}

float distC(int rssi)
{
    return pow(10.0, (TX_C - rssi) / (10.0 * N_C));
}

// ---------------- RSSI UPDATE (5s AVG) ----------------
void updateRSSI()
{
    unsigned long start = millis();

    float sumA = 0, sumC = 0;
    int countA = 0, countC = 0;

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
            else if (mac == MAC_C)
            {
                sumC += rssi;
                countC++;
            }
        }

        pBLEScan->clearResults();
    }

    if (countA > 0) rssi_A = sumA / countA;
    if (countC > 0) rssi_C = sumC / countC;
}

// ---------------- 2-CIRCLE SOLVER (MIDPOINT ORIGIN) ----------------
// A = (-L/2,0), C = (L/2,0)

void solve2Circles(float dA, float dC, float L,
                   float &x1, float &y1, float &x2, float &y2)
{
    float x = (dA*dA - dC*dC) / (2.0 * L);

    float dxA = x + (L / 2.0);

    float temp = dA*dA - dxA*dxA;
    if (temp < 0) temp = 0;

    float y = sqrt(temp);

    x1 = x;
    y1 = y;

    x2 = x;
    y2 = -y;
}

// ---------------- SETUP ----------------
void setup()
{
    Serial.begin(115200);

    BLEDevice::init("");
    pBLEScan = BLEDevice::getScan();
    pBLEScan->setActiveScan(true);

    Serial.println("2-anchor midpoint system started");
}

// ---------------- LOOP ----------------
void loop()
{
    updateRSSI();

    float dA = clampDist(distA(rssi_A));
    float dC = clampDist(distC(rssi_C));

    // light smoothing (helps noise)
    float avg = (dA + dC) / 2.0;
    dA = (dA + avg) / 2.0;
    dC = (dC + avg) / 2.0;

    float L = 1.0; // set real A-C distance in meters

    float x1, y1, x2, y2;
    solve2Circles(dA, dC, L, x1, y1, x2, y2);

    Serial.println("---- DISTANCES ----");
    Serial.print("A: "); Serial.println(dA);
    Serial.print("C: "); Serial.println(dC);

    Serial.println("---- POSSIBLE POSITIONS ----");
    Serial.print("P1: ("); Serial.print(x1); Serial.print(", "); Serial.print(y1); Serial.println(")");
    Serial.print("P2: ("); Serial.print(x2); Serial.print(", "); Serial.print(y2); Serial.println(")");

    Serial.println("----------------------");
}
