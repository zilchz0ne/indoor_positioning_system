#include <WiFi.h>
#include <WiFiUdp.h>
#include <BLEDevice.h>
#include <BLEScan.h>
#include <math.h>

// ---------------- WIFI ----------------
const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASS";

// ---------------- UDP ----------------
WiFiUDP udp;
const int UDP_PORT = 4210;
IPAddress broadcastIP(255, 255, 255, 255);

// ---------------- BLE ----------------
BLEScan* pBLEScan;

// ---------------- MAC ADDRESSES ----------------
const String MAC_A = "68:fe:71:8b:45:b6";
const String MAC_B = "68:fe:71:8a:f4:d2";
const String MAC_C = "68:fe:71:8b:4c:6e";

// ---------------- RSSI ----------------
int rssi_A = -100;
int rssi_B = -100;
int rssi_C = -100;

// ---------------- CALIBRATION ----------------
const float TX_A = -68;
const float TX_B = -70;
const float TX_C = -73;

const float N_A = 2.5;
const float N_B = 2.5;
const float N_C = 2.5;

// ---------------- ANCHOR POSITIONS ----------------
// A = (-0.5, 0)
// C = ( 0.5, 0)
// B = ( 0.0, 1.0)
float Ax = -0.5, Ay = 0.0;
float Bx =  0.0, By = 1.0;
float Cx =  0.5, Cy = 0.0;

// ---------------- DISTANCE LIMIT ----------------
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

float distB(int rssi)
{
    return pow(10.0, (TX_B - rssi) / (10.0 * N_B));
}

float distC(int rssi)
{
    return pow(10.0, (TX_C - rssi) / (10.0 * N_C));
}

// ---------------- RSSI UPDATE ----------------
void updateRSSI()
{
    unsigned long start = millis();

    float sumA = 0, sumB = 0, sumC = 0;
    int countA = 0, countB = 0, countC = 0;

    while (millis() - start < 2000)
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

// ---------------- 2-CIRCLE SOLVER ----------------
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

// ---------------- DISTANCE TO B ----------------
float distToB(float x, float y)
{
    float dx = x - Bx;
    float dy = y - By;
    return sqrt(dx*dx + dy*dy);
}

// ---------------- SEND UDP JSON ----------------
void sendUDP(float dA, float dB, float dC,
             float x1, float y1,
             float x2, float y2,
             float fx, float fy)
{
    String json = "{";

    json += "\"A\":" + String(dA, 3) + ",";
    json += "\"B\":" + String(dB, 3) + ",";
    json += "\"C\":" + String(dC, 3) + ",";

    json += "\"points\":[";
    json += "{\"x\":" + String(x1, 3) + ",\"y\":" + String(y1, 3) + "},";
    json += "{\"x\":" + String(x2, 3) + ",\"y\":" + String(y2, 3) + "}";
    json += "],";

    json += "\"final\":{";
    json += "\"x\":" + String(fx, 3) + ",";
    json += "\"y\":" + String(fy, 3);
    json += "}";

    json += "}";

    udp.beginPacket(broadcastIP, UDP_PORT);
    udp.print(json);
    udp.endPacket();
}

// ---------------- SETUP ----------------
void setup()
{
    Serial.begin(115200);

    BLEDevice::init("");
    pBLEScan = BLEDevice::getScan();
    pBLEScan->setActiveScan(true);

    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED)
    {
        delay(300);
    }

    udp.begin(UDP_PORT);

    Serial.println("System ready (3-anchor)");
}

// ---------------- LOOP ----------------
void loop()
{
    updateRSSI();

    float dA = clampDist(distA(rssi_A));
    float dB = clampDist(distB(rssi_B));
    float dC = clampDist(distC(rssi_C));

    // smoothing
    float avg = (dA + dC) / 2.0;
    dA = (dA + avg) / 2.0;
    dC = (dC + avg) / 2.0;

    float L = 1.0;

    float x1, y1, x2, y2;
    solve2Circles(dA, dC, L, x1, y1, x2, y2);

    // choose correct point using B
    float d1 = distToB(x1, y1);
    float d2 = distToB(x2, y2);

    float err1 = abs(d1 - dB);
    float err2 = abs(d2 - dB);

    float fx, fy;

    if (err1 < err2)
    {
        fx = x1;
        fy = y1;
    }
    else
    {
        fx = x2;
        fy = y2;
    }

    sendUDP(dA, dB, dC, x1, y1, x2, y2, fx, fy);
}
