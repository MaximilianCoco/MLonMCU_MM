/**
 * @file usart_image_protocol.c
 * @brief USART1 protocol implementation for receiving images and sending results
 */

#include "usart_image_protocol.h"
#include <string.h>
#include <stdio.h>
#define RX_CHUNK 16384

/**
 * @brief Calculate CRC16 (CCITT)
 */
uint16_t usart_crc16(const uint8_t* data, size_t len)
{
  uint16_t crc = 0xFFFF;
  
  for (size_t i = 0; i < len; i++)
  {
    crc ^= (uint16_t)data[i] << 8;
    for (int j = 0; j < 8; j++)
    {
      if (crc & 0x8000)
        crc = (crc << 1) ^ 0x1021;
      else
        crc = crc << 1;
    }
  }
  return crc;
}

/**
 * @brief Initialize USART protocol
 */
int usart_protocol_init(UART_HandleTypeDef* huart)
{
  if (huart == NULL)
    return -1;
  
  printf("USART Protocol ready - waiting for image data...\r\n");
  return 0;
}

/**
 * @brief Receive single byte with timeout
 */
static int usart_recv_byte(UART_HandleTypeDef* huart, uint8_t* byte, uint32_t timeout_ms)
{
  HAL_StatusTypeDef status = HAL_UART_Receive(huart, byte, 1, timeout_ms);
  return (status == HAL_OK) ? 0 : -1;
}

/**
 * @brief Receive image data from USART1
 * Protocol: [START_MARKER] [MSG_TYPE] [SIZE_4BYTES] [IMAGE_DATA] [CRC16] [END_MARKER]
 */
int usart_receive_image(UART_HandleTypeDef* huart, uint8_t* image_buffer, uint32_t timeout_ms)
{
  uint8_t byte;
  uint16_t received_crc;
  uint8_t msg_type;
  uint32_t data_size;
  
  if (huart == NULL || image_buffer == NULL)
    return -1;
  
  /* NO PRINTF DURING PROTOCOL! Text output interferes with binary data */
  
  /* Wait for start marker - scan and skip any text/garbage bytes */
  while (1)
  {
    if (usart_recv_byte(huart, &byte, timeout_ms) != 0)
    {
      return -1;
    }
    if (byte == PROTOCOL_START_MARKER)
    {
      break;  /* Found it */
    }
    /* Skip this byte - it's printf text or garbage */
  }
  
  /* Get message type */
  if (usart_recv_byte(huart, &msg_type, timeout_ms) != 0)
  {
    return -1;
  }
  
  if (msg_type != MSG_TYPE_IMAGE_DATA)
  {
    return -1;
  }
  
  /* Get size (4 bytes, little-endian) */
  uint8_t size_bytes[4];
  for (int i = 0; i < 4; i++)
  {
    if (usart_recv_byte(huart, &size_bytes[i], timeout_ms) != 0)
    {
      return -1;
    }
  }
  data_size = (size_bytes[0]) | (size_bytes[1] << 8) | (size_bytes[2] << 16) | (size_bytes[3] << 24);
  
  if (data_size != 150528)  /* 224*224*3 */
  {
    return -1;
  }
  
  /* Receive image data - NO PRINTING! */
  uint32_t received = 0;

  while (received < data_size)
  {
      uint32_t remaining = data_size - received;

      uint32_t chunk = (remaining > RX_CHUNK) ? RX_CHUNK : remaining;

      HAL_StatusTypeDef status =
          HAL_UART_Receive(huart,
                           image_buffer + received,
                           chunk,
                           100);   // 🔴 FIX: 1000 → 50ms max

      if (status == HAL_OK)
      {
          received += chunk;
      }
      else if (status == HAL_TIMEOUT)
      {
          // do NOT fail, just continue (data may be streaming)
          continue;
      }
      else
      {
          printf("RX fatal error at %lu\r\n", received);
          return -1;
      }
  }

  /* Receive CRC (2 bytes, little-endian) */
  uint8_t crc_bytes[2];
  if (usart_recv_byte(huart, &crc_bytes[0], timeout_ms) != 0 ||
      usart_recv_byte(huart, &crc_bytes[1], timeout_ms) != 0)
  {
    return -1;
  }
  received_crc = (crc_bytes[0]) | (crc_bytes[1] << 8);
  
  /* Verify CRC */
  uint16_t calculated_crc = usart_crc16(image_buffer, data_size);
  
  if (received_crc != calculated_crc)
  {
    return -1;
  }
  
  /* Wait for end marker */
  if (usart_recv_byte(huart, &byte, timeout_ms) != 0 || byte != PROTOCOL_END_MARKER)
  {
    return -1;
  }
  
  return 0;
}

/**
 * @brief Send anomaly detection result
 * Protocol: [START_MARKER] [MSG_TYPE] [ANOMALY_INT] [IS_ANOMALY] [CRC16] [END_MARKER]
 */
int usart_send_result(UART_HandleTypeDef* huart, float anomaly_score, uint8_t is_anomaly, uint32_t inference_us, uint32_t anomaly_us, uint32_t loadpic_us)
{
  if (huart == NULL)
    return -1;

  uint8_t buffer[20];
  int32_t anomaly_int = (int32_t)(anomaly_score * 10000);

  /* NO PRINTF DURING PROTOCOL! Build message silently */
  int idx = 0;
  buffer[idx++] = PROTOCOL_START_MARKER;
  buffer[idx++] = MSG_TYPE_RESULT;

  /* Add anomaly score (4 bytes, little-endian) */
  buffer[idx++] = (anomaly_int) & 0xFF;
  buffer[idx++] = (anomaly_int >> 8) & 0xFF;
  buffer[idx++] = (anomaly_int >> 16) & 0xFF;
  buffer[idx++] = (anomaly_int >> 24) & 0xFF;

  /* Add status */
  buffer[idx++] = is_anomaly;

  // NEW: inference time (uint32 little-endian)
    buffer[idx++] = (inference_us) & 0xFF;
    buffer[idx++] = (inference_us >> 8) & 0xFF;
    buffer[idx++] = (inference_us >> 16) & 0xFF;
    buffer[idx++] = (inference_us >> 24) & 0xFF;
    /* anomaly time */
    buffer[idx++] = (anomaly_us) & 0xFF;
    buffer[idx++] = (anomaly_us >> 8) & 0xFF;
    buffer[idx++] = (anomaly_us >> 16) & 0xFF;
    buffer[idx++] = (anomaly_us >> 24) & 0xFF;

    buffer[idx++] = (loadpic_us) & 0xFF;
    buffer[idx++] = (loadpic_us >> 8) & 0xFF;
    buffer[idx++] = (loadpic_us >> 16) & 0xFF;
    buffer[idx++] = (loadpic_us >> 24) & 0xFF;

  /* Calculate CRC on data portion */
  uint16_t crc = usart_crc16(&buffer[1], idx - 1);  /* Exclude start marker */
  buffer[idx++] = crc & 0xFF;
  buffer[idx++] = (crc >> 8) & 0xFF;

  buffer[idx++] = PROTOCOL_END_MARKER;

  /* Send */
  HAL_StatusTypeDef status = HAL_UART_Transmit(huart, buffer, idx, HAL_MAX_DELAY);

  if (status == HAL_OK) {
    /* Print AFTER sending */
    printf("[MCU RESULT] Result sent (anomaly=%ld, status=%d)\r\n",
           anomaly_int, is_anomaly);
    fflush(stdout);
    return 0;
  } else {
    printf("[MCU RESULT] ERROR: Failed to send result\r\n");
    fflush(stdout);
    return -1;
  }
}
