void setup() {
  init_dip_switch();
  Serial.begin(9600);
  Serial.println("LOL");
}

void loop() {
  Serial.print("Motion Class: ");
  Serial.print(read_motion_class());
  Serial.print(", Logger Location: ");
  Serial.print(read_logger_location());
  Serial.print(", SD Active: ");
  Serial.println(read_sd_active()); 
}

void init_dip_switch() {
  pinMode(2, INPUT);
  pinMode(3, INPUT);
  pinMode(4, INPUT);
  pinMode(5, INPUT);
  pinMode(6, INPUT);
  pinMode(7, INPUT);
  pinMode(8, INPUT);
}

int read_motion_class() {
  int out = 0x0000;
  for (int i = 5; i >= 2; i--) {
    out = (out << 1) | digitalRead(i);
  }
  return out;
}

bool read_sd_active() {
  return (bool) digitalRead(8);
}

int read_logger_location() {
  int out = 0x00;
  for (int i = 7; i >= 6; i--) {
    out = (out << 1) | digitalRead(i);
  }
  return out;
}

