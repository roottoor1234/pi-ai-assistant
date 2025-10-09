#include <Servo.h>

Servo servo1;
Servo servo2;

const int SERVO1_PIN = 7;
const int SERVO2_PIN = 6;

void setup() {
  Serial.begin(115200);

  servo1.attach(SERVO1_PIN);
  servo2.attach(SERVO2_PIN);

  servo1.write(90);
  servo2.write(90);

  Serial.println("Ready. Send: [servo_number] [angle]");
  Serial.println("Example: 1 120 or 2 45");
}

void loop() {
  if (Serial.available()) {
    int servoNum = Serial.parseInt(); // Πρώτος αριθμός: ποιο servo
    int angle = Serial.parseInt();    // Δεύτερος αριθμός: γωνία

    if (servoNum == 1 && angle >= -90 && angle <= 90) {
      int realAngle = angle + 90; // δεξί servo κανονικά
      servo1.write(realAngle);
    } 
    else if (servoNum == 2 && angle >= -90 && angle <= 90) {
      int realAngle = 90 - angle; // αριστερό servo αντιστραμμένο
      servo2.write(realAngle);
    }


    // Καθαρίζει το buffer για επόμενη είσοδο
    while (Serial.available()) Serial.read();
  }
}
