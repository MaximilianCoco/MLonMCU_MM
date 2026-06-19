/**
 * @file usart_image_protocol.h
 * @brief USART1 protocol for receiving and transmitting images and anomaly scores
 */

#ifndef USART_IMAGE_PROTOCOL_H
#define USART_IMAGE_PROTOCOL_H

#include <stdint.h>
#include <stddef.h>
#include "stm32u5xx_hal.h"

/* Protocol markers */
#define PROTOCOL_START_MARKER      (0xAA)
#define PROTOCOL_END_MARKER        (0xBB)

/* Message types */
#define MSG_TYPE_IMAGE_DATA        (0x01)
#define MSG_TYPE_RESULT            (0x02)
#define MSG_TYPE_ACK               (0x03)
#define MSG_TYPE_ERROR             (0x04)

/* Image message structure:
 * [START_MARKER] [MSG_TYPE] [SIZE_4BYTES] [IMAGE_DATA] [CRC16] [END_MARKER]
 * Total: 1 + 1 + 4 + 150528 + 2 + 1 = 150537 bytes
 */

typedef struct {
  uint8_t start_marker;
  uint8_t msg_type;
  uint32_t data_size;
  uint8_t* data;
  uint16_t crc16;
  uint8_t end_marker;
} usart_message_t;

/* Result message:
 * [START_MARKER] [MSG_TYPE] [ANOMALY_INT32] [IS_ANOMALY] [CRC16] [END_MARKER]
 * Total: 1 + 1 + 4 + 1 + 2 + 1 = 10 bytes
 */

typedef struct {
  uint8_t start_marker;
  uint8_t msg_type;
  int32_t anomaly_int;  /* Anomaly score * 10000 */
  uint8_t is_anomaly;
  uint16_t crc16;
  uint8_t end_marker;
} usart_result_message_t;

/**
 * @brief Initialize USART protocol
 * @param hi2c: UART handle
 * @return 0 on success
 */
int usart_protocol_init(UART_HandleTypeDef* huart);

/**
 * @brief Receive image data from USART1 (blocking)
 * @param image_buffer: pointer to buffer (150528 bytes for 224x224x3 int8)
 * @param timeout_ms: timeout in milliseconds
 * @return 0 on success, -1 on error/timeout
 */
int usart_receive_image(UART_HandleTypeDef* huart, uint8_t* image_buffer, uint32_t timeout_ms);

/**
 * @brief Send anomaly detection result over USART1
 * @param anomaly_score: anomaly score (0.0 - 1.0)
 * @param is_anomaly: 1 if anomaly, 0 if normal
 * @return 0 on success
 */
int usart_send_result(UART_HandleTypeDef* huart, float anomaly_score, uint8_t is_anomaly, uint32_t inference_us, uint32_t anomaly_us, uint32_t loadpic_us);

/**
 * @brief Calculate CRC16
 * @param data: pointer to data
 * @param len: length of data
 * @return CRC16 value
 */
uint16_t usart_crc16(const uint8_t* data, size_t len);

#endif /* USART_IMAGE_PROTOCOL_H */
