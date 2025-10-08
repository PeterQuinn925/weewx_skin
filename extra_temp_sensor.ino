/*you must disconnect the white jumper between RST and GPIO to program and reconnect for it to sleep
*/

#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include <Wire.h>
int tmp102Address = 0x48;
// Time to sleep (in seconds):
const int sleepTimeS = 120;

const char* ssid     = "yourWifinamehere";
const char* password = "yourWifiPasswordHere";

const char* streamId   = "tempdata.txt";
char  replyPacket[] = "whohoo!";

WiFiUDP Udp;
unsigned int localPort = 1025;
unsigned int localUDPPort = 1025;

void setup() {
  Serial.begin(115200);
  Wire.begin (5, 4); // setting up the SDA(5) and SCL(4) pins
  delay(10);

  // We start by connecting to a WiFi network

  Serial.println();
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
  Serial.println("Starting UDP");
  Udp.begin(localPort);
  Serial.print("Local port: ");
  Serial.println(Udp.localPort());

  Wire.requestFrom(tmp102Address, 2);
  byte MSB = Wire.read();
  byte LSB = Wire.read();

  //it's a 12bit int, using two's compliment for negative
  int TemperatureSum = ((MSB << 8) | LSB) >> 4;

  float TempC = TemperatureSum * 0.0625;
  if (TempC > 128)
  {
    TempC = TempC - 256; // for negative temperatures
  }
  float TempF = 32 + TempC * 1.8;
  Serial.print("Temp  = ");
  Serial.println(TempF);
  //sprintf(replyPacekt,100, "%f", TempF);
  dtostrf(TempF, 4, 6, replyPacket);

  Serial.print("connecting to ");
  IPAddress ip(10, 0, 0, 20);

  Udp.beginPacket(ip, 1025);
  Udp.write(replyPacket);
  Udp.endPacket();
  delay(100);
  // Sleep
  Serial.println("ESP8266 in sleep mode");
  ESP.deepSleep(sleepTimeS * 1000000, WAKE_RF_DEFAULT);
  delay(100);
}

void loop() {
}
