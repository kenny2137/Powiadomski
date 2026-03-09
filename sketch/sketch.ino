#include <Arduino_RouterBridge.h>

// Global Variable For Bufor
String gsmResponse;
String atCommand;

void receiveFromPython(String command) {
  Serial.print(command); 
}

void setup() {
  Monitor.begin();
  while (!Monitor) {}
  Bridge.begin(); 
  Bridge.provide("send_at", receiveFromPython);
  Serial.begin(115200);
  // We reserve 1024 bytes (1KB) in advance in RAM for long responses.
  gsmResponse.reserve(1024);
  atCommand.reserve(256);
  
  Monitor.println("Wait 3 seconds to run SIM7670E...");
  delay(3000); 
  Monitor.println("Send config SMS...");
  Serial.print("AT+CMGF=1\r\n");
  delay(500);
  Serial.print("AT+CNMI=1,1,0,0,0\r\n");
  delay(500);
}

void loop() {
  // --- GSM Response ---
  if (Serial.available()) {
    unsigned long lastCharTime = millis();
    
    while (millis() - lastCharTime < 10) {
      while (Serial.available()) {
        gsmResponse += (char)Serial.read();
        lastCharTime = millis();
      }
    }
    
    Monitor.print(gsmResponse);
    
    Bridge.notify("gsm_rx", gsmResponse.c_str());
    
    gsmResponse = "";
  }

  // --- Transmit AT Commands (from Monitor) ---
  if (Monitor.available()) {
    unsigned long lastCharTime = millis();
    
    while (millis() - lastCharTime < 10) {
      while (Monitor.available()) {
        atCommand += (char)Monitor.read();
        lastCharTime = millis();
      }
    }
    
    Serial.print(atCommand);
    atCommand = "";
  }
}