
int ANALOG_PIN_OFFSET = 100;
int analog_pins[] = { A1, A2, A3, A4, A5, A6, A7, A8, A9, A10, A11, A12, A13, A14, A15 };
void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600); // Arduino
  Serial1.begin(9600); // XBee
}

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial1.available()) {    
    byte input[3];
    Serial1.readBytes(input, 2);
    char command = char(input[0]);
    int pin = int(input[1]);
    if((pin - ANALOG_PIN_OFFSET) >= 0) {
      pin = analog_pins[pin - ANALOG_PIN_OFFSET];
    }
    Serial.print("pin: ");
    Serial.println(pin);
    if (command == 'H') {
      pinMode(pin, OUTPUT);
      digitalWrite(pin, HIGH);
      Serial.print("high: ");
      Serial.println(pin);
      delay(200);
      digitalWrite(pin, LOW);
	    Serial1.write('A');
    } else if (input[0] == 'L') {
      Serial.print("low: ");
      Serial.println(pin);
      digitalWrite(pin, LOW); 
    } else if (input[0] == 'K') {
      Serial.print("Keepalive received...");
      Serial1.write('A');
      Serial.println("sent response.");
    } else {
      Serial.print("else: ");
      Serial.println(input[0]);
    }
  }
}
