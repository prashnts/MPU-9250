
void setup() {
  Wire.begin();
  Serial.begin(38400);

  // Set up the interrupt pin, its set as active high, push-pull
  pinMode(intPin, INPUT);
  digitalWrite(intPin, LOW);
  pinMode(myLed, OUTPUT);
  digitalWrite(myLed, HIGH);
  
  delay(1000);

  byte c = readByte(MPU9250_ADDRESS, WHO_AM_I_MPU9250);
  byte d = readByte(AK8963_ADDRESS, WHO_AM_I_AK8963);
  
  delay(1000);

  if (c == 0x71 && d == 0x48) {
    Serial.println("MPU9250 and AK8963 are online.");
    
    MPU9250SelfTest(SelfTest); // Start by performing self test and reporting values
    Serial.print("x-axis self test: acceleration trim within : "); Serial.print(SelfTest[0],1); Serial.println("% of factory value");
    Serial.print("y-axis self test: acceleration trim within : "); Serial.print(SelfTest[1],1); Serial.println("% of factory value");
    Serial.print("z-axis self test: acceleration trim within : "); Serial.print(SelfTest[2],1); Serial.println("% of factory value");
    Serial.print("x-axis self test: gyration trim within : "); Serial.print(SelfTest[3],1); Serial.println("% of factory value");
    Serial.print("y-axis self test: gyration trim within : "); Serial.print(SelfTest[4],1); Serial.println("% of factory value");
    Serial.print("z-axis self test: gyration trim within : "); Serial.print(SelfTest[5],1); Serial.println("% of factory value");

    // Calibrate gyro and accelerometers, load biases in bias registers
    calibrateMPU9250(gyroBias, accelBias);
    
    delay(1000);
    
    initMPU9250();
    Serial.println("MPU9250 initialized for active data mode");
    initAK8963(magCalibration);

    if(SerialDebug) {
      Serial.print("X-Axis sensitivity adjustment value "); Serial.println(magCalibration[0], 2);
      Serial.print("Y-Axis sensitivity adjustment value "); Serial.println(magCalibration[1], 2);
      Serial.print("Z-Axis sensitivity adjustment value "); Serial.println(magCalibration[2], 2); 
    }
    delay(1000);
  }

  else {
    Serial.print("Could not connect to MPU9250: 0x");
    Serial.println(c, HEX);
    while(1) ; // Loop forever if communication doesn't happen 
  }
}


void loop() {
  
  // If intPin goes high, all data registers have new data
  if (readByte(MPU9250_ADDRESS, INT_STATUS) & 0x01) {
    // On interrupt, check if data ready interrupt
    readAccelData(accelCount); // Read the x/y/z adc values
    getAres();
    
    // Now we'll calculate the accleration value into actual g's
    ax = (float)accelCount[0]*aRes; // - accelBias[0]; // get actual g value, this depends on scale being set
    ay = (float)accelCount[1]*aRes; // - accelBias[1];
    az = (float)accelCount[2]*aRes; // - accelBias[2];
    
    readGyroData(gyroCount); // Read the x/y/z adc values
    getGres();
    
    // Calculate the gyro value into actual degrees per second
    gx = (float)gyroCount[0]*gRes; // get actual gyro value, this depends on scale being set
    gy = (float)gyroCount[1]*gRes;
    gz = (float)gyroCount[2]*gRes;
    
    readMagData(magCount); // Read the x/y/z adc values
    getMres();
    magbias[0] = +470.; // User environmental x-axis correction in milliGauss, should be automatically calculated
    magbias[1] = +120.; // User environmental x-axis correction in milliGauss
    magbias[2] = +125.; // User environmental x-axis correction in milliGauss
    
    // Calculate the magnetometer values in milliGauss
    // Include factory calibration per data sheet and user environmental corrections
    mx = (float)magCount[0]*mRes*magCalibration[0] - magbias[0]; // get actual magnetometer value, this depends on scale being set
    my = (float)magCount[1]*mRes*magCalibration[1] - magbias[1];
    mz = (float)magCount[2]*mRes*magCalibration[2] - magbias[2];
    
  }
  
  
  Now = micros();
  deltat = ((Now - lastUpdate)/1000000.0f); // set integration time by time elapsed since last filter update
  lastUpdate = Now;
  
  sum += deltat; // sum for averaging filter update rate
  sumCount++;
  
  // Sensors x (y)-axis of the accelerometer is aligned with the y (x)-axis of the magnetometer;
  // the magnetometer z-axis (+ down) is opposite to z-axis (+ up) of accelerometer and gyro!
  // We have to make some allowance for this orientationmismatch in feeding the output to the quaternion filter.
  // For the MPU-9250, we have chosen a magnetic rotation that keeps the sensor forward along the x-axis just like
  // in the LSM9DS0 sensor. This rotation can be modified to allow any convenient orientation convention.
  // This is ok by aircraft orientation standards!
  // Pass gyro rate as rad/s
  // MadgwickQuaternionUpdate(ax, ay, az, gx*PI/180.0f, gy*PI/180.0f, gz*PI/180.0f, my, mx, mz);
  MahonyQuaternionUpdate(ax, ay, az, gx*PI/180.0f, gy*PI/180.0f, gz*PI/180.0f, my, mx, mz);
  
  
  if (!AHRS) {
    
    delt_t = millis() - count;
    if(delt_t > 500) {
      
      
      if(SerialDebug) {
        
        // Print acceleration values in milligs!
        Serial.print("X-acceleration: "); Serial.print(1000*ax); Serial.print(" mg ");
        Serial.print("Y-acceleration: "); Serial.print(1000*ay); Serial.print(" mg ");
        Serial.print("Z-acceleration: "); Serial.print(1000*az); Serial.println(" mg ");
        
        // Print gyro values in degree/sec
        Serial.print("X-gyro rate: "); Serial.print(gx, 3); Serial.print(" degrees/sec ");
        Serial.print("Y-gyro rate: "); Serial.print(gy, 3); Serial.print(" degrees/sec ");
        Serial.print("Z-gyro rate: "); Serial.print(gz, 3); Serial.println(" degrees/sec");
        
        // Print mag values in degree/sec
        Serial.print("X-mag field: "); Serial.print(mx); Serial.print(" mG ");
        Serial.print("Y-mag field: "); Serial.print(my); Serial.print(" mG ");
        Serial.print("Z-mag field: "); Serial.print(mz); Serial.println(" mG");
        
        tempCount = readTempData(); // Read the adc values
        temperature = ((float) tempCount) / 333.87 + 21.0; // Temperature in degrees Centigrade
        // Print temperature in degrees Centigrade
        Serial.print("Temperature is "); Serial.print(temperature, 1); Serial.println(" degrees C"); // Print T values to tenths of s degree C
        
      }
      
      
      
      count = millis();
      digitalWrite(myLed, !digitalRead(myLed)); // toggle led
      
    }
    
    
  }
  
  else {
    
    
    // Serial print and/or display at 0.5 s rate independent of data rates
    delt_t = millis() - count;
    if (delt_t > 500) {
      // update LCD once per half-second independent of read rate
      
      if(SerialDebug) {
        
        Serial.print("ax = "); Serial.print((int)1000*ax);
        Serial.print(" ay = "); Serial.print((int)1000*ay);
        Serial.print(" az = "); Serial.print((int)1000*az); Serial.println(" mg");
        Serial.print("gx = "); Serial.print( gx, 2);
        Serial.print(" gy = "); Serial.print( gy, 2);
        Serial.print(" gz = "); Serial.print( gz, 2); Serial.println(" deg/s");
        Serial.print("mx = "); Serial.print( (int)mx );
        Serial.print(" my = "); Serial.print( (int)my );
        Serial.print(" mz = "); Serial.print( (int)mz ); Serial.println(" mG");
        
        Serial.print("q0 = "); Serial.print(q[0]);
        Serial.print(" qx = "); Serial.print(q[1]);
        Serial.print(" qy = "); Serial.print(q[2]);
        Serial.print(" qz = "); Serial.println(q[3]);
        
      }
      
      
      // Define output variables from updated quaternion---these are Tait-Bryan angles, commonly used in aircraft orientation.
      // In this coordinate system, the positive z-axis is down toward Earth.
      // Yaw is the angle between Sensor x-axis and Earth magnetic North (or true North if corrected for local declination, looking down on the sensor positive yaw is counterclockwise.
      // Pitch is angle between sensor x-axis and Earth ground plane, toward the Earth is positive, up toward the sky is negative.
      // Roll is angle between sensor y-axis and Earth ground plane, y-axis up is positive roll.
      // These arise from the definition of the homogeneous rotation matrix constructed from quaternions.
      // Tait-Bryan angles as well as Euler angles are non-commutative; that is, the get the correct orientation the rotations must be
      // applied in the correct order which for this configuration is yaw, pitch, and then roll.
      // For more see http://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles which has additional links.
      yaw  = atan2(2.0f * (q[1] * q[2] + q[0] * q[3]), q[0] * q[0] + q[1] * q[1] - q[2] * q[2] - q[3] * q[3]);
      pitch = -asin(2.0f * (q[1] * q[3] - q[0] * q[2]));
      roll = atan2(2.0f * (q[0] * q[1] + q[2] * q[3]), q[0] * q[0] - q[1] * q[1] - q[2] * q[2] + q[3] * q[3]);
      pitch *= 180.0f / PI;
      yaw  *= 180.0f / PI;
      yaw  -= 13.8; // Declination at Danville, California is 13 degrees 48 minutes and 47 seconds on 2014-04-04
      roll *= 180.0f / PI;
      
      if(SerialDebug) {
        
        Serial.print("Yaw, Pitch, Roll: ");
        Serial.print(yaw, 2);
        Serial.print(", ");
        Serial.print(pitch, 2);
        Serial.print(", ");
        Serial.println(roll, 2);
        
        Serial.print("rate = "); Serial.print((float)sumCount/sum, 2); Serial.println(" Hz");
        
      }
      
      
      
      // With these settings the filter is updating at a ~145 Hz rate using the Madgwick scheme and
      // >200 Hz using the Mahony scheme even though the display refreshes at only 2 Hz.
      // The filter update rate is determined mostly by the mathematical steps in the respective algorithms,
      // the processor speed (8 MHz for the 3.3V Pro Mini), and the magnetometer ODR:
      // an ODR of 10 Hz for the magnetometer produce the above rates, maximum magnetometer ODR of 100 Hz produces
      // filter update rates of 36 - 145 and ~38 Hz for the Madgwick and Mahony schemes, respectively.
      // This is presumably because the magnetometer read takes longer than the gyro or accelerometer reads.
      // This filter update rate should be fast enough to maintain accurate platform orientation for
      // stabilization control of a fast-moving robot or quadcopter. Compare to the update rate of 200 Hz
      // produced by the on-board Digital Motion Processor of Invensense's MPU6050 6 DoF and MPU9150 9DoF sensors.
      // The 3.3 V 8 MHz Pro Mini is doing pretty well!
      
      
      count = millis();
      sumCount = 0;
      sum = 0;
      
    }
    
    
  }
}