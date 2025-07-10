// Test_Serial_Stream.ino
// Sends integers 0-255 in a ping-pong pattern over serial at 30 FPS

const int minValue = 0;
const int maxValue = 255;
const int fps = 30;
const unsigned long frameDelay = 1000 / fps;

int value = minValue;
bool ascending = true;
unsigned long lastFrameTime = 0;

void setup() {
  Serial.begin(9600); // Use a fast baud rate for reliability
  while (!Serial) {
    ; // Wait for serial port to connect. Needed for native USB
  }
  pinMode(LED_BUILTIN, OUTPUT); // Initialize the built-in LED
  Serial.println("Tester Connected!");
}

void loop() {
  unsigned long now = millis();
  if (now - lastFrameTime >= frameDelay) {
    Serial.println(value);
    lastFrameTime = now;
    digitalWrite(LED_BUILTIN, HIGH); // Turn LED on
    delay(10); // Briefly flash LED (10ms)
    digitalWrite(LED_BUILTIN, LOW);  // Turn LED off
    if (ascending) {
      value++;
      if (value >= maxValue) {
        value = maxValue;
        ascending = false;
      }
    } else {
      value--;
      if (value <= minValue) {
        value = minValue;
        ascending = true;
      }
    }
  }
} 