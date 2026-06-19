/**
 * @file i2c_anomaly.c
 * @brief I2C transmission of anomaly detection results
 */

#include "i2c_anomaly.h"
#include <string.h>

/* I2C operation timeout in milliseconds */
#define I2C_TIMEOUT_MS  (100)

/**
 * @brief Calculate simple CRC16 for data validation (CCITT polynomial)
 * @param data: pointer to data buffer
 * @param len: length of data
 * @return CRC16 value
 */
uint16_t crc16_calculate(const uint8_t* data, size_t len)
{
  uint16_t crc = 0xFFFF;
  
  for (size_t i = 0; i < len; i++)
  {
    crc ^= (uint16_t)data[i] << 8;
    
    for (int j = 0; j < 8; j++)
    {
      if (crc & 0x8000)
      {
        crc = (crc << 1) ^ 0x1021;
      }
      else
      {
        crc = crc << 1;
      }
    }
  }
  
  return crc;
}

/**
 * @brief Initialize I2C for anomaly data transmission
 * @param hi2c: I2C handle
 * @return 0 on success, -1 on error
 */
int i2c_anomaly_init(I2C_HandleTypeDef* hi2c)
{
  if (hi2c == NULL)
  {
    return -1;
  }
  
  /* I2C is already initialized by HAL in main.c */
  /* Just verify the handle is valid */
  if (hi2c->Instance == NULL)
  {
    return -1;
  }
  
  return 0;
}

/**
 * @brief Send anomaly score over I2C
 * @param hi2c: I2C handle
 * @param anomaly_score: anomaly score value (0.0 - 1.0)
 * @param is_anomaly: 1 if anomaly detected, 0 if normal
 * @return 0 on success, -1 on error
 */
int i2c_send_anomaly_score(I2C_HandleTypeDef* hi2c, float anomaly_score, uint8_t is_anomaly)
{
  if (hi2c == NULL)
  {
    return -1;
  }
  
  /* Prepare data structure */
  anomaly_data_t data;
  memset(&data, 0, sizeof(anomaly_data_t));
  
  data.start_marker = 0xAA;
  data.anomaly_score = anomaly_score;
  data.is_anomaly = is_anomaly;
  
  /* Calculate CRC on all fields except CRC itself */
  uint8_t* data_ptr = (uint8_t*)&data;
  size_t crc_len = offsetof(anomaly_data_t, crc16);
  data.crc16 = crc16_calculate(data_ptr, crc_len);
  
  /* Send over I2C */
  HAL_StatusTypeDef status = HAL_I2C_Master_Transmit(
    hi2c,
    ANOMALY_I2C_ADDRESS,
    data_ptr,
    ANOMALY_DATA_SIZE,
    I2C_TIMEOUT_MS
  );
  
  if (status != HAL_OK)
  {
    return -1;
  }
  
  return 0;
}
