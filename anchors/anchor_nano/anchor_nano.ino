#include <SoftwareSerial.h>

// Connect Nano Digital Pin 2 to HM-10 TXD
// Connect Nano Digital Pin 3 to HM-10 RXD (use a voltage divider if required)
SoftwareSerial bleSerial(2, 3); 

void setup() {
  // Initialize standard hardware serial for PC debugging logs
  Serial.begin(9600);
  while (!Serial) {
    ; // Wait for serial communication stability
  }
  
  // Initialize software serial connection to the BLE module
  bleSerial.begin(9600); 
  Serial.println("System initialization: Setting up BLE Anchor...");
  delay(1000);

  // Send industrial AT config commands to establish an empty name advertising loop
  bleSerial.print("AT+RENEW");     // Reset factory settings to ensure a clean state
  delay(500);
  bleSerial.print("AT+NAME");      // Set name parameters to empty to minimize packet size
  delay(500);
  bleSerial.print("AT+ROLE1");     // Configure the BLE module to Master / Beacon mode
  delay(500);
  bleSerial.print("AT+RESET");     // Reboot module to save parameters and start advertising
  delay(500);

  Serial.println("Anchor initialization complete. BLE Broadcasting active!");
}

void loop() {
  // Read raw telemetry positioning string feedback if broadcasted by the module
  if (bleSerial.available()) {
    char incomingByte = bleSerial.read();
    Serial.print(incomingByte);
  }
  delay(1000);
}
