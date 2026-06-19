/**
 * @file i2c_anomaly.h
 * @brief I2C transmission of anomaly detection results
 */

#ifndef I2C_ANOMALY_H
#define I2C_ANOMALY_H

#include <stdint.h>
#include <stddef.h>
#include "stm32u5xx_hal.h"

/* I2C Slave Address for anomaly data transmission */
#define ANOMALY_I2C_ADDRESS  (0x50 << 1)  /* 7-bit address shifted to 8-bit */

/* Data structure for I2C transmission */
typedef struct {
  uint8_t start_marker;           /* 0xAA - indicates valid data */
  float anomaly_score;             /* Anomaly score (0.0 - 1.0) */
  uint8_t is_anomaly;              /* 1 if anomaly detected, 0 if normal */
  uint8_t reserved[3];             /* Reserved for future use */
  uint16_t crc16;                  /* Simple CRC for data validation */
} anomaly_data_t;

#define ANOMALY_DATA_SIZE sizeof(anomaly_data_t)

/**
 * @brief Initialize I2C for anomaly data transmission
 * @note Call this once during initialization
 * @return 0 on success, -1 on error
 */
int i2c_anomaly_init(I2C_HandleTypeDef* hi2c);

/**
 * @brief Send anomaly score over I2C
 * @param anomaly_score: anomaly score value (0.0 - 1.0)
 * @param is_anomaly: 1 if anomaly detected, 0 if normal
 * @return 0 on success, -1 on error
 */
int i2c_send_anomaly_score(I2C_HandleTypeDef* hi2c, float anomaly_score, uint8_t is_anomaly);

/**
 * @brief Calculate simple CRC16 for data validation
 * @param data: pointer to data buffer
 * @param len: length of data
 * @return CRC16 value
 */
uint16_t crc16_calculate(const uint8_t* data, size_t len);

#endif /* I2C_ANOMALY_H */
