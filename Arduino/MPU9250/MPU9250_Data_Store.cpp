
/* MPU9250 Basic Example Code

Demonstrate basic MPU-9250 functionality including parameterizing the register addresses, initializing the sensor,
getting properly scaled accelerometer, gyroscope, and magnetometer data out. Added display functions to
allow display to on breadboard monitor. Addition of 9 DoF sensor fusion using open source Madgwick and
Mahony filter algorithms. Sketch runs on the 3.3 V 8 MHz Pro Mini and the Teensy 3.1.

SDA and SCL should have external pull-up resistors (to 3.3V).
10k resistors are on the EMSENSR-9250 breakout board.

Hardware setup:
MPU9250 Breakout -------- Arduino
VDD --------------------- 3.3V
ADO --------------------- 3.3V
SDA --------------------- A4
SCL --------------------- A5
GND --------------------- GND

*/
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include "MPU9250_Register_Map.h"
#include "Wire.cpp"

// Using the MSENSR-9250 breakout board, ADO is set to 0
// Seven-bit device address is 110100 for ADO = 0 and 110101 for ADO = 1
#define ADO 1
#if ADO
#define MPU9250_ADDRESS 0x69 // Device address when ADO = 1
#else
#define MPU9250_ADDRESS 0x68 // Device address when ADO = 0
#define AK8963_ADDRESS  0x0C  // Address of magnetometer
#endif

#define AHRS true // set to false for basic data read
#define SerialDebug true  // set to true to get Serial output for debugging

// Set initial input parameters
enum Ascale {
  AFS_2G = 0,
  AFS_4G,
  AFS_8G,
  AFS_16G
};

enum Gscale {
  GFS_250DPS = 0,
  GFS_500DPS,
  GFS_1000DPS,
  GFS_2000DPS
};

enum Mscale {
  MFS_14BITS = 0, // 0.60 mG per LSB
  MFS_16BITS      // 0.15 mG per LSB
};

// Specify sensor full scale
uint8_t Gscale = GFS_250DPS;
uint8_t Ascale = AFS_2G;
uint8_t Mscale = MFS_16BITS; // Choose either 14-bit or 16-bit magnetometer resolution
uint8_t Mmode = 0x02; // 2 for 8 Hz, 6 for 100 Hz continuous magnetometer data read

float aRes, gRes, mRes;  // scale resolutions per LSB for the sensors

// Pin definitions
int intPin = 12; // These can be changed, 2 and 3 are the Arduinos ext int pins
int myLed = 13; // Set up pin 13 led for toggling

int16_t accelCount[3]; // Stores the 16-bit signed accelerometer sensor output
int16_t gyroCount[3];  // Stores the 16-bit signed gyro sensor output
int16_t magCount[3]; // Stores the 16-bit signed magnetometer sensor output

// Factory mag calibration, mag bias, gyro bias and accelerometer bias
float magCalibration[3] = {0, 0, 0},
      magbias[3]        = {0, 0, 0},
      gyroBias[3]       = {0, 0, 0},
      accelBias[3]      = {0, 0, 0};

int16_t tempCount;  // temperature raw count output
float   temperature; // Stores the real internal chip temperature in degrees Celsius

float   SelfTest[6]; // holds results of gyro and accelerometer self test

// global constants for 9 DoF fusion and AHRS (Attitude and Heading Reference System)
float GyroMeasError = PI * (40.0f / 180.0f);  // gyroscope measurement error in rads/s (start at 40 deg/s)
float GyroMeasDrift = PI * (0.0f / 180.0f);  // gyroscope measurement drift in rad/s/s (start at 0.0 deg/s/s)
// There is a tradeoff in the beta parameter between accuracy and response speed.
// In the original Madgwick study, beta of 0.041 (corresponding to GyroMeasError of 2.7 degrees/s) was found to give optimal accuracy.
// However, with this value, the LSM9SD0 response time is about 10 seconds to a stable initial quaternion.
// Subsequent changes also require a longish lag time to a stable output, not fast enough for a quadcopter or robot car!
// By increasing beta (GyroMeasError) by about a factor of fifteen, the response time constant is reduced to ~2 sec
// I haven't noticed any reduction in solution accuracy. This is essentially the I coefficient in a PID control sense;
// the bigger the feedback coefficient, the faster the solution converges, usually at the expense of accuracy.
// In any case, this is the free parameter in the Madgwick filtering and fusion scheme.
float beta = sqrt(3.0f / 4.0f) * GyroMeasError;  // compute beta
float zeta = sqrt(3.0f / 4.0f) * GyroMeasDrift;  // compute zeta, the other free parameter in the Madgwick scheme usually set to a small or zero value
#define Kp 2.0f * 5.0f // these are the free parameters in the Mahony filter and fusion scheme, Kp for proportional feedback, Ki for integral
#define Ki 0.0f

uint32_t delt_t = 0; // used to control display output rate
uint32_t count = 0, sumCount = 0; // used to control display output rate
float pitch, yaw, roll;
float deltat = 0.0f, sum = 0.0f; // integration interval for both filter schemes
uint32_t lastUpdate = 0, firstUpdate = 0; // used to calculate integration interval
uint32_t Now = 0; // used to calculate integration interval

float ax, ay, az, gx, gy, gz, mx, my, mz; // variables to hold latest sensor data values
float q[4] = {1.0f, 0.0f, 0.0f, 0.0f}; // vector to hold quaternion
float eInt[3] = {0.0f, 0.0f, 0.0f};  // vector to hold integral error for Mahony method


// Set of useful function to access acceleration. gyroscope, magnetometer, and temperature data

/**
 * Sets the global `mRes` with the Magnetometer resolution.
 * Possible magnetometer scales and register bit settings are:
 * 14 bit 0
 * 16 bit 1
 */
void getMres() {
  switch (Mscale) {
    case MFS_14BITS:
      mRes = 10.*4219./8190.;
      break;
    case MFS_16BITS:
      mRes = 10.*4219./32760.0;
      break; 
  }
}

/**
 * Sets the global `gRes` with the Gyroscope resolution.
 * Possible Gyro scales and register bit settings are:
 *  250 DPS 00
 *  500 DPS 01
 *  1000 DPS 10
 *  2000 DPS 11
 */
void getGres() {
  switch (Gscale) {
    case GFS_250DPS:
      gRes = 250.0/32768.0;
      break;
    case GFS_500DPS:
      gRes = 500.0/32768.0;
      break;
    case GFS_1000DPS:
      gRes = 1000.0/32768.0;
      break;
    case GFS_2000DPS:
      gRes = 2000.0/32768.0;
      break;
  }
}

/**
 * Sets the global `aRes` with the Accelerometer resolution.
 * Possible Accelerometer scales and register bit settings are:
 *  2 Gs 00
 *  4 Gs 01
 *  8 Gs 10
 *  16 Gs 11
 */
void getAres() {
  switch (Ascale) {
    case AFS_2G:
      aRes = 2.0/32768.0;
      break;
    case AFS_4G:
      aRes = 4.0/32768.0;
      break;
    case AFS_8G:
      aRes = 8.0/32768.0;
      break;
    case AFS_16G:
      aRes = 16.0/32768.0;
      break;
  }
}

/**
 * Reads the Accelerometer data from the device.
 * Reformats to a 3D vector.
 * @param destination Address of the variable holding the values.
 */
void readAccelData(int16_t * destination) {
  uint8_t rawData[6]; // x/y/z accel register data stored here
  readBytes(MPU9250_ADDRESS, ACCEL_XOUT_H, 6, &rawData[0]);
  destination[0] = ((int16_t)rawData[0] << 8) | rawData[1];
  destination[1] = ((int16_t)rawData[2] << 8) | rawData[3];
  destination[2] = ((int16_t)rawData[4] << 8) | rawData[5];
}

/**
 * Reads the Gyroscope data from the device.
 * Reformats to a 3D vector.
 * @param destination Address of the variable holding the values.
 */
void readGyroData(int16_t * destination) {
  uint8_t rawData[6]; // x/y/z gyro register data stored here
  readBytes(MPU9250_ADDRESS, GYRO_XOUT_H, 6, &rawData[0]);
  destination[0] = ((int16_t)rawData[0] << 8) | rawData[1];
  destination[1] = ((int16_t)rawData[2] << 8) | rawData[3];
  destination[2] = ((int16_t)rawData[4] << 8) | rawData[5];
}

/**
 * Reads the Magnetometer data from the device.
 * Reformats to a 3D vector.
 * @param destination Address of the variable holding the values.
 */
void readMagData(int16_t * destination) {
  uint8_t rawData[7];

  if(readByte(AK8963_ADDRESS, AK8963_ST1) & 0x01) {
    // wait for magnetometer data ready bit to be set
    readBytes(AK8963_ADDRESS, AK8963_XOUT_L, 7, &rawData[0]);

    uint8_t c = rawData[6];
    if(!(c & 0x08)) {
      // Check if magnetic sensor overflow set, if not then report data
      destination[0] = ((int16_t)rawData[1] << 8) | rawData[0];
      destination[1] = ((int16_t)rawData[3] << 8) | rawData[2];
      destination[2] = ((int16_t)rawData[5] << 8) | rawData[4];
    }
  }
}

/**
 * Reads the Magnetometer data from the device.
 * @return 16 bit Temperature reading data.
 */
int16_t readTempData() {
  uint8_t rawData[2];

  // Read the two raw data registers sequentially into data array
  readBytes(MPU9250_ADDRESS, TEMP_OUT_H, 2, &rawData[0]);
  return ((int16_t)rawData[0] << 8) | rawData[1];
}

/**
 * Initializes the magnetometer.
 * @param destination Sets the sensitivity adjustment values to the address.
 */
void initAK8963(float * destination) {
  // First extract the factory calibration for each magnetometer axis
  uint8_t rawData[3]; // x/y/z gyro calibration data stored here

  // Power down magnetometer
  writeByte(AK8963_ADDRESS, AK8963_CNTL, 0x00);
  delay(10);

  // Enter Fuse ROM access mode
  writeByte(AK8963_ADDRESS, AK8963_CNTL, 0x0F);
  delay(10);

  // Read the x-, y-, and z-axis calibration values
  readBytes(AK8963_ADDRESS, AK8963_ASAX, 3, &rawData[0]);

  // Return x-axis sensitivity adjustment values, etc.
  destination[0] = (float)(rawData[0] - 128)/256. + 1.;
  destination[1] = (float)(rawData[1] - 128)/256. + 1.;
  destination[2] = (float)(rawData[2] - 128)/256. + 1.;

  // Power down magnetometer
  writeByte(AK8963_ADDRESS, AK8963_CNTL, 0x00);
  delay(10);

  // Configure the magnetometer for continuous read and highest resolution
  // set Mscale bit 4 to 1 (0) to enable 16 (14) bit resolution in CNTL register,
  // and enable continuous mode data acquisition Mmode (bits [3:0])
  // 0010 for 8 Hz and 0110 for 100 Hz sample rates
  // Set magnetometer data resolution and sample ODR
  writeByte(AK8963_ADDRESS, AK8963_CNTL, Mscale << 4 | Mmode);
  delay(10);
}

/**
 * Initializes the MPU9250.
 */
void initMPU9250() {
  
  // wake up device
  // Clear sleep mode bit (6), enable all sensors
  writeByte(MPU9250_ADDRESS, PWR_MGMT_1, 0x00);
  // Wait for all registers to reset
  delay(100);
  
  // get stable time source
  // Auto select clock source to be PLL gyroscope reference if ready else
  writeByte(MPU9250_ADDRESS, PWR_MGMT_1, 0x01);
  delay(200);
  
  // Configure Gyro and Thermometer
  // Disable FSYNC and set thermometer and gyro bandwidth to 41 and 42 Hz, respectively;
  // minimum delay time for this setting is 5.9 ms, which means sensor fusion update rates cannot
  // be higher than 1 / 0.0059 = 170 Hz
  // DLPF_CFG = bits 2:0 = 011; this limits the sample rate to 1000 Hz for both
  // With the MPU9250, it is possible to get gyro sample rates of 32 kHz (!), 8 kHz, or 1 kHz
  writeByte(MPU9250_ADDRESS, CONFIG, 0x03);
  
  // Set sample rate = gyroscope output rate/(1 + SMPLRT_DIV)
  // Use a 200 Hz rate; a rate consistent with the filter update rate
  writeByte(MPU9250_ADDRESS, SMPLRT_DIV, 0x04);
  // determined inset in CONFIG above
  
  // Set gyroscope full scale range
  // Range selects FS_SEL and AFS_SEL are 0 - 3, so 2-bit values are left-shifted into positions 4:3
  uint8_t c = readByte(MPU9250_ADDRESS, GYRO_CONFIG);
  // writeRegister(GYRO_CONFIG, c & ~0xE0); // Clear self-test bits [7:5]
  // Clear Fchoice bits [1:0]
  writeByte(MPU9250_ADDRESS, GYRO_CONFIG, c & ~0x02);
  // Clear AFS bits [4:3]
  writeByte(MPU9250_ADDRESS, GYRO_CONFIG, c & ~0x18);
  // Set full scale range for the gyro
  writeByte(MPU9250_ADDRESS, GYRO_CONFIG, c | Gscale << 3);
  // writeRegister(GYRO_CONFIG, c | 0x00);
  // Set Fchoice for the gyro to 11 by writing its inverse to bits 1:0 of GYRO_CONFIG
  
  // Set accelerometer full-scale range configuration
  c = readByte(MPU9250_ADDRESS, ACCEL_CONFIG);
  // Clear self-test bits [7:5]
  // writeRegister(ACCEL_CONFIG, c & ~0xE0);
  // Clear AFS bits [4:3]
  writeByte(MPU9250_ADDRESS, ACCEL_CONFIG, c & ~0x18);
  // Set full scale range for the accelerometer
  writeByte(MPU9250_ADDRESS, ACCEL_CONFIG, c | Ascale << 3);
  
  // Set accelerometer sample rate configuration
  // It is possible to get a 4 kHz sample rate from the accelerometer by choosing 1 for
  // accel_fchoice_b bit [3]; in this case the bandwidth is 1.13 kHz
  c = readByte(MPU9250_ADDRESS, ACCEL_CONFIG2);
  // Clear accel_fchoice_b (bit 3) and A_DLPFG (bits [2:0])
  writeByte(MPU9250_ADDRESS, ACCEL_CONFIG2, c & ~0x0F);
  // Set accelerometer rate to 1 kHz and bandwidth to 41 Hz
  writeByte(MPU9250_ADDRESS, ACCEL_CONFIG2, c | 0x03);
  
  // The accelerometer, gyro, and thermometer are set to 1 kHz sample rates,
  // but all these rates are further reduced by a factor of 5 to 200 Hz because of the SMPLRT_DIV setting
  
  // Configure Interrupts and Bypass Enable
  // Set interrupt pin active high, push-pull, hold interrupt pin level HIGH until interrupt cleared,
  // clear on read of INT_STATUS, and enable I2C_BYPASS_EN so additional chips
  // can join the I2C bus and all can be controlled by the Arduino as master
  writeByte(MPU9250_ADDRESS, INT_PIN_CFG, 0x22);
  // Enable data ready (bit 0) interrupt
  writeByte(MPU9250_ADDRESS, INT_ENABLE, 0x01);
  delay(100);
}

/**
 * Function which accumulates gyro and accelerometer data after device initialization.
 * It calculates the average of the at-rest readings and then loads the resulting 
 * offsets into accelerometer and gyro bias registers.
 * @param dest1 Factory Bias
 * @param dest2 Calibrated Bias
 */
void calibrateMPU9250(float * dest1, float * dest2) {
  // data array to hold accelerometer and gyro x, y, z, data
  uint8_t data[12];
  uint16_t ii, packet_count, fifo_count;
  int32_t gyro_bias[3] = {0, 0, 0},
          accel_bias[3] = {0, 0, 0};
  
  // reset device
  writeByte(MPU9250_ADDRESS, PWR_MGMT_1, 0x80); // Write a one to bit 7 reset bit; toggle reset device
  delay(100);
  
  // get stable time source; Auto select clock source to be PLL gyroscope reference if ready
  // else use the internal oscillator, bits 2:0 = 001
  writeByte(MPU9250_ADDRESS, PWR_MGMT_1, 0x01);
  writeByte(MPU9250_ADDRESS, PWR_MGMT_2, 0x00);
  delay(200);
  
  // Configure device for bias calculation
  // Disable all interrupts
  writeByte(MPU9250_ADDRESS, INT_ENABLE, 0x00);
  // Disable FIFO
  writeByte(MPU9250_ADDRESS, FIFO_EN, 0x00);
  // Turn on internal clock source
  writeByte(MPU9250_ADDRESS, PWR_MGMT_1, 0x00);
  // Disable I2C master
  writeByte(MPU9250_ADDRESS, I2C_MST_CTRL, 0x00);
  // Disable FIFO and I2C master modes
  writeByte(MPU9250_ADDRESS, USER_CTRL, 0x00);
  // Reset FIFO and DMP
  writeByte(MPU9250_ADDRESS, USER_CTRL, 0x0C);
  delay(15);
  
  // Configure MPU6050 gyro and accelerometer for bias calculation
  // Set low-pass filter to 188 Hz
  writeByte(MPU9250_ADDRESS, CONFIG, 0x01);
  // Set sample rate to 1 kHz
  writeByte(MPU9250_ADDRESS, SMPLRT_DIV, 0x00);
  // Set gyro full-scale to 250 degrees per second, maximum sensitivity
  writeByte(MPU9250_ADDRESS, GYRO_CONFIG, 0x00);
  // Set accelerometer full-scale to 2 g, maximum sensitivity
  writeByte(MPU9250_ADDRESS, ACCEL_CONFIG, 0x00);
  
  uint16_t gyrosensitivity = 131;  // = 131 LSB/degrees/sec
  uint16_t accelsensitivity = 16384; // = 16384 LSB/g
  
  // Configure FIFO to capture accelerometer and gyro data for bias calculation
  // Enable FIFO
  writeByte(MPU9250_ADDRESS, USER_CTRL, 0x40);
  // Enable gyro and accelerometer sensors for FIFO (max size 512 bytes in MPU-9150)
  writeByte(MPU9250_ADDRESS, FIFO_EN, 0x78);
  // accumulate 40 samples in 40 milliseconds = 480 bytes
  delay(40);
  
  // At end of sample accumulation, turn off FIFO sensor read
  // Disable gyro and accelerometer sensors for FIFO
  writeByte(MPU9250_ADDRESS, FIFO_EN, 0x00);
  // read FIFO sample count
  readBytes(MPU9250_ADDRESS, FIFO_COUNTH, 2, &data[0]);
  fifo_count = ((uint16_t)data[0] << 8) | data[1];
  // How many sets of full gyro and accelerometer data for averaging
  packet_count = fifo_count/12;
  
  for (ii = 0; ii < packet_count; ii++) {
    int16_t accel_temp[3] = {0, 0, 0}, gyro_temp[3] = {0, 0, 0};

    // read data for averaging
    readBytes(MPU9250_ADDRESS, FIFO_R_W, 12, &data[0]);
    // Form signed 16-bit integer for each sample in FIFO
    accel_temp[0] = (int16_t)(((int16_t)data[0] << 8) | data[1] );
    accel_temp[1] = (int16_t)(((int16_t)data[2] << 8) | data[3] );
    accel_temp[2] = (int16_t)(((int16_t)data[4] << 8) | data[5] );
    gyro_temp[0] = (int16_t)(((int16_t)data[6] << 8) | data[7] );
    gyro_temp[1] = (int16_t)(((int16_t)data[8] << 8) | data[9] );
    gyro_temp[2] = (int16_t)(((int16_t)data[10] << 8) | data[11]);

    // Sum individual signed 16-bit biases to get accumulated signed 32-bit biases
    accel_bias[0] += (int32_t) accel_temp[0];
    accel_bias[1] += (int32_t) accel_temp[1];
    accel_bias[2] += (int32_t) accel_temp[2];
    gyro_bias[0] += (int32_t) gyro_temp[0];
    gyro_bias[1] += (int32_t) gyro_temp[1];
    gyro_bias[2] += (int32_t) gyro_temp[2];
  }

  // Normalize sums to get average count biases
  accel_bias[0] /= (int32_t) packet_count;
  accel_bias[1] /= (int32_t) packet_count;
  accel_bias[2] /= (int32_t) packet_count;
  gyro_bias[0] /= (int32_t) packet_count;
  gyro_bias[1] /= (int32_t) packet_count;
  gyro_bias[2] /= (int32_t) packet_count;
  
  if(accel_bias[2] > 0L) {
    accel_bias[2] -= (int32_t) accelsensitivity;
  }
  else {
    // Remove gravity from the z-axis accelerometer bias calculation
    accel_bias[2] += (int32_t) accelsensitivity;
  }
  
  
  // Construct the gyro biases for push to the hardware gyro bias registers
  // which are reset to zero upon device startup
  // Divide by 4 to get 32.9 LSB per deg/s to conform to expected bias input format
  data[0] = (-gyro_bias[0]/4 >> 8) & 0xFF;
  // Biases are additive, so change sign on calculated average gyro biases
  data[1] = (-gyro_bias[0]/4)  & 0xFF;
  data[2] = (-gyro_bias[1]/4 >> 8) & 0xFF;
  data[3] = (-gyro_bias[1]/4)  & 0xFF;
  data[4] = (-gyro_bias[2]/4 >> 8) & 0xFF;
  data[5] = (-gyro_bias[2]/4)  & 0xFF;
  
  // Push gyro biases to hardware registers
  writeByte(MPU9250_ADDRESS, XG_OFFSET_H, data[0]);
  writeByte(MPU9250_ADDRESS, XG_OFFSET_L, data[1]);
  writeByte(MPU9250_ADDRESS, YG_OFFSET_H, data[2]);
  writeByte(MPU9250_ADDRESS, YG_OFFSET_L, data[3]);
  writeByte(MPU9250_ADDRESS, ZG_OFFSET_H, data[4]);
  writeByte(MPU9250_ADDRESS, ZG_OFFSET_L, data[5]);
  
  // Output scaled gyro biases for display in the main program
  dest1[0] = (float) gyro_bias[0]/(float) gyrosensitivity;
  dest1[1] = (float) gyro_bias[1]/(float) gyrosensitivity;
  dest1[2] = (float) gyro_bias[2]/(float) gyrosensitivity;
  
  // Construct the accelerometer biases for push to the hardware accelerometer bias registers.
  // These registers contain factory trim values which must be added to the calculated accelerometer biases;
  // on boot up these registers will hold non-zero values.
  // In addition, bit 0 of the lower byte must be preserved since it is used for temperature
  // compensation calculations. Accelerometer bias registers expect bias input as 2048 LSB per g, so that
  // the accelerometer biases calculated above must be divided by 8.
  
  // A place to hold the factory accelerometer trim biases
  int32_t accel_bias_reg[3] = {0, 0, 0};

  // Read factory accelerometer trim values
  readBytes(MPU9250_ADDRESS, XA_OFFSET_H, 2, &data[0]);
  accel_bias_reg[0] = (int32_t) (((int16_t)data[0] << 8) | data[1]);
  readBytes(MPU9250_ADDRESS, YA_OFFSET_H, 2, &data[0]);
  accel_bias_reg[1] = (int32_t) (((int16_t)data[0] << 8) | data[1]);
  readBytes(MPU9250_ADDRESS, ZA_OFFSET_H, 2, &data[0]);
  accel_bias_reg[2] = (int32_t) (((int16_t)data[0] << 8) | data[1]);

  // Define mask for temperature compensation bit 0 of lower byte of accelerometer bias registers
  uint32_t mask = 1uL;
  // Define array to hold mask bit for each accelerometer bias axis
  uint8_t mask_bit[3] = {0, 0, 0};
  
  for(ii = 0; ii < 3; ii++) {
    // If temperature compensation bit is set, record that fact in mask_bit
    if((accel_bias_reg[ii] & mask)) {
      mask_bit[ii] = 0x01;
    }
  }

  // Construct total accelerometer bias, including calculated average accelerometer bias from above
  // Subtract calculated averaged accelerometer bias scaled to 2048 LSB/g (16 g full scale)
  accel_bias_reg[0] -= (accel_bias[0]/8);
  accel_bias_reg[1] -= (accel_bias[1]/8);
  accel_bias_reg[2] -= (accel_bias[2]/8);
  
  data[0] = (accel_bias_reg[0] >> 8) & 0xFF;
  data[1] = (accel_bias_reg[0])  & 0xFF;
  // preserve temperature compensation bit when writing back to accelerometer bias registers
  data[1] = data[1] | mask_bit[0];
  data[2] = (accel_bias_reg[1] >> 8) & 0xFF;
  data[3] = (accel_bias_reg[1])  & 0xFF;
  // preserve temperature compensation bit when writing back to accelerometer bias registers
  data[3] = data[3] | mask_bit[1];
  data[4] = (accel_bias_reg[2] >> 8) & 0xFF;
  data[5] = (accel_bias_reg[2])  & 0xFF;
  // preserve temperature compensation bit when writing back to accelerometer bias registers
  data[5] = data[5] | mask_bit[2];
  
  // Apparently this is not working for the acceleration biases in the MPU-9250
  // Are we handling the temperature correction bit properly?
  // Push accelerometer biases to hardware registers
  writeByte(MPU9250_ADDRESS, XA_OFFSET_H, data[0]);
  writeByte(MPU9250_ADDRESS, XA_OFFSET_L, data[1]);
  writeByte(MPU9250_ADDRESS, YA_OFFSET_H, data[2]);
  writeByte(MPU9250_ADDRESS, YA_OFFSET_L, data[3]);
  writeByte(MPU9250_ADDRESS, ZA_OFFSET_H, data[4]);
  writeByte(MPU9250_ADDRESS, ZA_OFFSET_L, data[5]);
  
  // Output scaled accelerometer biases for display in the main program
  dest2[0] = (float)accel_bias[0]/(float)accelsensitivity;
  dest2[1] = (float)accel_bias[1]/(float)accelsensitivity;
  dest2[2] = (float)accel_bias[2]/(float)accelsensitivity;
}

/**
 * Does the Accelerometer and Gyroscope self test. Checks current calibration
 * with respect to factory settings.
 * Returns the percent deviation from factory trim values.
 * +/- 14 or less deviation is a pass.
 * @param destination The destination address to store the calibration results.
 */
void MPU9250SelfTest(float * destination) {
  uint8_t rawData[6] = {0, 0, 0, 0, 0, 0};
  uint8_t selfTest[6];
  int16_t gAvg[3], aAvg[3], aSTAvg[3], gSTAvg[3];
  float factoryTrim[6];
  uint8_t FS = 0;
  
  // Set gyro sample rate to 1 kHz
  writeByte(MPU9250_ADDRESS, SMPLRT_DIV, 0x00);
  // Set gyro sample rate to 1 kHz and DLPF to 92 Hz
  writeByte(MPU9250_ADDRESS, CONFIG, 0x02);
  // Set full scale range for the gyro to 250 dps
  writeByte(MPU9250_ADDRESS, GYRO_CONFIG, 1<<FS);
  // Set accelerometer rate to 1 kHz and bandwidth to 92 Hz
  writeByte(MPU9250_ADDRESS, ACCEL_CONFIG2, 0x02);
  // Set full scale range for the accelerometer to 2 g
  writeByte(MPU9250_ADDRESS, ACCEL_CONFIG, 1<<FS);
  
  // Get average current values of gyro and acclerometer
  for( int ii = 0; ii < 200; ii++) {
    readBytes(MPU9250_ADDRESS, ACCEL_XOUT_H, 6, &rawData[0]);
    aAvg[0] += (int16_t)(((int16_t)rawData[0] << 8) | rawData[1]);
    aAvg[1] += (int16_t)(((int16_t)rawData[2] << 8) | rawData[3]);
    aAvg[2] += (int16_t)(((int16_t)rawData[4] << 8) | rawData[5]);
    
    readBytes(MPU9250_ADDRESS, GYRO_XOUT_H, 6, &rawData[0]);
    gAvg[0] += (int16_t)(((int16_t)rawData[0] << 8) | rawData[1]);
    gAvg[1] += (int16_t)(((int16_t)rawData[2] << 8) | rawData[3]);
    gAvg[2] += (int16_t)(((int16_t)rawData[4] << 8) | rawData[5]);
  }
  
  // Get average of 200 values and store as average current readings
  for (int ii =0; ii < 3; ii++) {
    aAvg[ii] /= 200;
    gAvg[ii] /= 200;
  }
  
  // Configure the accelerometer for self-test
  // Enable self test on all three axes and set accelerometer range to +/- 2 g
  writeByte(MPU9250_ADDRESS, ACCEL_CONFIG, 0xE0);
  // Enable self test on all three axes and set gyro range to +/- 250 degrees/s
  writeByte(MPU9250_ADDRESS, GYRO_CONFIG, 0xE0);
  // Delay a while to let the device stabilize
  delay(25);
  
  // Get average self-test values of gyro and accelerometer
  for (int ii = 0; ii < 200; ii++) {
    // Read the six raw data registers into data array
    readBytes(MPU9250_ADDRESS, ACCEL_XOUT_H, 6, &rawData[0]);
    aSTAvg[0] += (int16_t)(((int16_t)rawData[0] << 8) | rawData[1]);
    aSTAvg[1] += (int16_t)(((int16_t)rawData[2] << 8) | rawData[3]);
    aSTAvg[2] += (int16_t)(((int16_t)rawData[4] << 8) | rawData[5]);
    
    // Read the six raw data registers sequentially into data array
    readBytes(MPU9250_ADDRESS, GYRO_XOUT_H, 6, &rawData[0]);
    gSTAvg[0] += (int16_t)(((int16_t)rawData[0] << 8) | rawData[1]);
    gSTAvg[1] += (int16_t)(((int16_t)rawData[2] << 8) | rawData[3]);
    gSTAvg[2] += (int16_t)(((int16_t)rawData[4] << 8) | rawData[5]);
  }

  // Get average of 200 values and store as average self-test readings
  for (int ii =0; ii < 3; ii++) {
    aSTAvg[ii] /= 200;
    gSTAvg[ii] /= 200;
  }
  
  // Configure the gyro and accelerometer for normal operation
  writeByte(MPU9250_ADDRESS, ACCEL_CONFIG, 0x00);
  writeByte(MPU9250_ADDRESS, GYRO_CONFIG, 0x00);
  delay(25);
  
  // Retrieve accelerometer and gyro factory Self-Test Code from USR_Reg
  // X-axis accel self-test results
  selfTest[0] = readByte(MPU9250_ADDRESS, SELF_TEST_X_ACCEL);
  // Y-axis accel self-test results
  selfTest[1] = readByte(MPU9250_ADDRESS, SELF_TEST_Y_ACCEL);
  // Z-axis accel self-test results
  selfTest[2] = readByte(MPU9250_ADDRESS, SELF_TEST_Z_ACCEL);
  // X-axis gyro self-test results
  selfTest[3] = readByte(MPU9250_ADDRESS, SELF_TEST_X_GYRO);
  // Y-axis gyro self-test results
  selfTest[4] = readByte(MPU9250_ADDRESS, SELF_TEST_Y_GYRO);
  // Z-axis gyro self-test results
  selfTest[5] = readByte(MPU9250_ADDRESS, SELF_TEST_Z_GYRO);
  
  // Retrieve factory self-test value from self-test code reads
  factoryTrim[0] = (float)(2620/1<<FS)*(pow(1.01, ((float)selfTest[0] - 1.0)));
  factoryTrim[1] = (float)(2620/1<<FS)*(pow(1.01, ((float)selfTest[1] - 1.0)));
  factoryTrim[2] = (float)(2620/1<<FS)*(pow(1.01, ((float)selfTest[2] - 1.0)));
  factoryTrim[3] = (float)(2620/1<<FS)*(pow(1.01, ((float)selfTest[3] - 1.0)));
  factoryTrim[4] = (float)(2620/1<<FS)*(pow(1.01, ((float)selfTest[4] - 1.0)));
  factoryTrim[5] = (float)(2620/1<<FS)*(pow(1.01, ((float)selfTest[5] - 1.0)));
  
  // Report results as a ratio of (STR - FT)/FT
  // The change from Factory Trim of the Self-Test Response
  for (int i = 0; i < 3; i++) {
    destination[i]   = 100.0*((float)(aSTAvg[i] - aAvg[i]))/factoryTrim[i];
    destination[i+3] = 100.0*((float)(gSTAvg[i] - gAvg[i]))/factoryTrim[i+3];
  }
}
