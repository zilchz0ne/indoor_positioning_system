#include <WiFi.h>
#include <WiFiUdp.h>
#include <BLEDevice.h>
#include <BLEScan.h>
#include <math.h>

const char* ssid = "YOUR_WIFI";
const char* password = "YOUR_PASS";

WiFiUDP udp;
const int UDP_PORT = 4210;
IPAddress broadcastIP(255, 255, 255, 255);

BLEScan* pBLEScan;

const String MAC_A = "68:fe:71:8b:45:b6";
const String MAC_B = "68:fe:71:8a:f4:d2";
const String MAC_C = "68:fe:71:8b:4c:6e";

int rssi_A = -100;
int rssi_B = -100;
int rssi_C = -100;

const float TX_A = -68;
const float TX_B = -70;
const float TX_C = -73;

const float N_A = 2.5;
const float N_B = 2.5;
const float N_C = 2.5;

float Ax = -0.5, Ay = 0.0;
float Bx =  0.0, By = 1.0;
float Cx =  0.5, Cy = 0.0;

float clampDist(float d)
{
    if (d < 0.2) return 0.2;
    if (d > 5.0) return 5.0;
    return d;
}

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

float distToB(float x, float y)
{
    float dx = x - Bx;
    float dy = y - By;
    return sqrt(dx*dx + dy*dy);
}

void trilaterate(float &x, float &y,
                 float x1, float y1, float r1,
                 float x2, float y2, float r2,
                 float x3, float y3, float r3)
{
    float A = 2*(x2 - x1);
    float B = 2*(y2 - y1);
    float C = r1*r1 - r2*r2 - x1*x1 + x2*x2 - y1*y1 + y2*y2;

    float D = 2*(x3 - x2);
    float E = 2*(y3 - y2);
    float F = r2*r2 - r3*r3 - x2*x2 + x3*x3 - y2*y2 + y3*y3;

    float denom = (A*E - B*D);

    if (abs(denom) < 0.0001)
    {
        x = 0;
        y = 0;
        return;
    }

    x = (C*E - B*F) / denom;
    y = (A*F - C*D) / denom;
}

void sendUDP(float dA, float dB, float dC,
             float x1, float y1,
             float x2, float y2,
             float fx, float fy,
             float tx, float ty)
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
    json += "},";

    json += "\"tri\":{";
    json += "\"x\":" + String(tx, 3) + ",";
    json += "\"y\":" + String(ty, 3);
    json += "}";

    json += "}";

    udp.beginPacket(broadcastIP, UDP_PORT);
    udp.print(json);
    udp.endPacket();
}

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

    Serial.println("System ready (full comparison)");
}

void loop()
{
    updateRSSI();

    float dA = clampDist(distA(rssi_A));
    float dB = clampDist(distB(rssi_B));
    float dC = clampDist(distC(rssi_C));

    float avg = (dA + dC) / 2.0;
    dA = (dA + avg) / 2.0;
    dC = (dC + avg) / 2.0;

    float L = 1.0;

    float x1, y1, x2, y2;
    solve2Circles(dA, dC, L, x1, y1, x2, y2);

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

    float tx, ty;
    trilaterate(tx, ty,
                Ax, Ay, dA,
                Bx, By, dB,
                Cx, Cy, dC);

    sendUDP(dA, dB, dC, x1, y1, x2, y2, fx, fy, tx, ty);
} 
