#ifndef Wire_Abstraction
#define Wire_Abstraction

/**
  * Writes the parameter data to the particular address of the I2C device.
  * This is an abstraction of the Wire Library routines.
  * @param address The address of the I2C device.
  * @param subAddress The address of the register we're writing into.
  * @param data The data to be written into the register.
  * @see Wire library
  */
void writeByte (
  uint8_t address,
  uint8_t subAddress,
  uint8_t data
) {
  Wire.beginTransmission(address); // Initialize the Tx buffer
  Wire.write(subAddress); // Put slave register address in Tx buffer
  Wire.write(data); // Put data in Tx buffer
  Wire.endTransmission(); // Send the Tx buffer
}

/**
 * Reads the value of the particular register of the I2C device.
 * This is an abstraction of the Wire Library routines.
 * @param address The address of the I2C device.
 * @param subAddress The address of the register we're reading from.
 * @returns The data from the slave register as specified in the subAddress.
 */
uint8_t readByte (
  uint8_t address,
  uint8_t subAddress
) {
  uint8_t data; // `data` will store the register data
  Wire.beginTransmission(address); // Initialize the Tx buffer
  Wire.write(subAddress);  // Put slave register address in Tx buffer
  Wire.endTransmission(false);  // Send the Tx buffer, but send a restart to keep connection alive
  Wire.requestFrom(address, (uint8_t) 1); // Read one byte from slave register address
  data = Wire.read();  // Fill Rx buffer with result
  return data;  // Return data read from slave register
}

/**
 * Reads multiple bytes from the given register address.
 * This is an abstraction of the Wire Library routine.
 * @param address The address of the I2C device.
 * @param subAddress The address of the register we're reading from.
 * @param count The number of bytes that needs to be read.
 * @param dest The address of the destination data store to save the retrieved value to.
 */
void readBytes (
  uint8_t address,
  uint8_t subAddress,
  uint8_t count,
  uint8_t * dest
) {
  Wire.beginTransmission(address);  // Initialize the Tx buffer
  Wire.write(subAddress); // Put slave register address in Tx buffer
  Wire.endTransmission(false);  // Send the Tx buffer, but send a restart to keep connection alive
  uint8_t i = 0;
  Wire.requestFrom(address, count); // Read bytes from slave register address
  while (Wire.available()) { 
    dest[i++] = Wire.read();
  }
}

#endif