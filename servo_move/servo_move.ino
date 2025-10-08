#include <Servo.h>

Servo servo;
const int SERVO_PIN = 7;

void setup() {
  servo.attach(SERVO_PIN);
  Serial.begin(115200);
  servo.write(90);
}

void loop() {
  if (Serial.available()) {
    int angle = Serial.parseInt();   // διαβάζει αριθμό
    if (angle >= 0 && angle <= 180) {
      servo.write(angle);
      Serial.print("Moved to: ");
      Serial.println(angle);
    }
  }
}
