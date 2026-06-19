/**
  ******************************************************************************
  * @file    app_x-cube-ai.c
  * @author  X-CUBE-AI C code generator
  * @brief   AI program body
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */

 /*
  * Description
  *   v1.0 - Minimum template to show how to use the Embedded Client API
  *          model. Only one input and one output is supported. All
  *          memory resources are allocated statically (AI_NETWORK_XX, defines
  *          are used).
  *          Re-target of the printf function is out-of-scope.
  *   v2.0 - add multiple IO and/or multiple heap support
  *
  *   For more information, see the embeded documentation:
  *
  *       [1] %X_CUBE_AI_DIR%/Documentation/index.html
  *
  *   X_CUBE_AI_DIR indicates the location where the X-CUBE-AI pack is installed
  *   typical : C:\Users\[user_name]\STM32Cube\Repository\STMicroelectronics\X-CUBE-AI\7.1.0
  */

#ifdef __cplusplus
 extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/

#if defined ( __ICCARM__ )
#elif defined ( __CC_ARM ) || ( __GNUC__ )
#endif

/* System headers */
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <inttypes.h>
#include <string.h>

#include "app_x-cube-ai.h"
#include "main.h"
#include "ai_datatypes_defines.h"
#include "network.h"
#include "network_data.h"
#include "memory_bank.h"


 /* USER CODE BEGIN includes */
#include "usart_image_protocol.h"
 extern UART_HandleTypeDef huart1;
#include "core_cm33.h"   // STM32U5 = Cortex-M33

static void DWT_Init(void)
{
    /* Enable trace and debug block */
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;

    /* Reset cycle counter */
    DWT->CYCCNT = 0;

    /* Enable cycle counter */
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
}
 /* USER CODE END includes */

/* IO buffers ----------------------------------------------------------------*/

#if !defined(AI_NETWORK_INPUTS_IN_ACTIVATIONS)
AI_ALIGNED(4) ai_i8 data_in_1[AI_NETWORK_IN_1_SIZE_BYTES];
ai_i8* data_ins[AI_NETWORK_IN_NUM] = {
data_in_1
};
#else
ai_i8* data_ins[AI_NETWORK_IN_NUM] = {
NULL
};
#endif

#if !defined(AI_NETWORK_OUTPUTS_IN_ACTIVATIONS)
AI_ALIGNED(4) ai_i8 data_out_1[AI_NETWORK_OUT_1_SIZE_BYTES];
ai_i8* data_outs[AI_NETWORK_OUT_NUM] = {
data_out_1
};
#else
ai_i8* data_outs[AI_NETWORK_OUT_NUM] = {
NULL
};
#endif

/* Activations buffers -------------------------------------------------------*/

AI_ALIGNED(32)
static uint8_t pool0[AI_NETWORK_DATA_ACTIVATION_1_SIZE];

ai_handle data_activations0[] = {pool0};

/* AI objects ----------------------------------------------------------------*/

static ai_handle network = AI_HANDLE_NULL;

static ai_buffer* ai_input;
static ai_buffer* ai_output;


static int ai_boostrap(ai_handle *act_addr)
{
  ai_error err;

  /* Create and initialize an instance of the model */
  err = ai_network_create_and_init(&network, act_addr, NULL);
  if (err.type != AI_ERROR_NONE) {
    //ai_log_err(err, "ai_network_create_and_init");
    return -1;
  }

  ai_input = ai_network_inputs_get(network, NULL);
  ai_output = ai_network_outputs_get(network, NULL);

#if defined(AI_NETWORK_INPUTS_IN_ACTIVATIONS)
  /*  In the case where "--allocate-inputs" option is used, memory buffer can be
   *  used from the activations buffer. This is not mandatory.
   */
  for (int idx=0; idx < AI_NETWORK_IN_NUM; idx++) {
	data_ins[idx] = ai_input[idx].data;
  }
#else
  for (int idx=0; idx < AI_NETWORK_IN_NUM; idx++) {
	  ai_input[idx].data = data_ins[idx];
  }
#endif

#if defined(AI_NETWORK_OUTPUTS_IN_ACTIVATIONS)
  /*  In the case where "--allocate-outputs" option is used, memory buffer can be
   *  used from the activations buffer. This is no mandatory.
   */
  for (int idx=0; idx < AI_NETWORK_OUT_NUM; idx++) {
	data_outs[idx] = ai_output[idx].data;
  }
#else
  for (int idx=0; idx < AI_NETWORK_OUT_NUM; idx++) {
	ai_output[idx].data = data_outs[idx];
  }
#endif

  return 0;
}

static int ai_run(void)
{
  ai_i32 batch;

  batch = ai_network_run(network, ai_input, ai_output);
  if (batch != 1) {
    //ai_log_err(ai_network_get_error(network),"ai_network_run");
    return -1;
  }

  return 0;
}

/* USER CODE BEGIN 2 */

/* Quantization parameters for output (from network.c) */
#define OUTPUT_SCALE       (8.462232653982937e-05f)
#define OUTPUT_ZERO_POINT  (12)
#define CPU_FREQ_HZ 160000000U
#define RATIO 0.00000625

/* Quantization parameters for input (from network.c) */
#define INPUT_SCALE       (0.01845340058207512f)
#define INPUT_ZERO_POINT  (-13)

/* Model input dimensions */
#define INPUT_HEIGHT      (224)
#define INPUT_WIDTH       (224)
#define INPUT_CHANNELS    (3)
#define INPUT_SIZE        (INPUT_HEIGHT * INPUT_WIDTH * INPUT_CHANNELS)

static float memory_bank_norm[MEMORY_N_VECTORS][MEMORY_VECTOR_DIM];

void init_memory_bank(void)
{
    for (int m = 0; m < MEMORY_N_VECTORS; m++)
    {
        float norm_sq = 0.0f;

        for (int d = 0; d < MEMORY_VECTOR_DIM; d++)
        {
            float v = (float)memory_bank[m][d] * MEMORY_SCALE;
            memory_bank_norm[m][d] = v;
            norm_sq += v * v;
        }

        float norm = sqrtf(norm_sq);

        for (int d = 0; d < MEMORY_VECTOR_DIM; d++)
        {
            memory_bank_norm[m][d] =
                (norm > 1e-8f) ? (memory_bank_norm[m][d] / norm) : 0.0f;
        }
    }
}


static inline uint32_t get_cycles(void)
{
    return DWT->CYCCNT;
}
/*
 * @brief Convert RGB uint8 image to quantized int8 format
 * @param rgb_image: pointer to RGB image data (uint8, 0-255)
 * @param quant_image: pointer to output quantized data (int8)
 * @param size: number of pixels (H*W*C)

void quantize_image(const uint8_t* rgb_image, ai_i8* quant_image, uint32_t size)
{
  for (uint32_t i = 0; i < size; i++)
  {
    float normalized = (float)rgb_image[i] / INPUT_SCALE + INPUT_ZERO_POINT;
    quant_image[i] = (ai_i8)((normalized >= 0.0f) ? (normalized + 0.5f) : (normalized - 0.5f));
  }
}
*/

/**
 * @brief Compute adaptive average pooling at 1x1 (global average)
 * Assumes features are quantized int8 (28x28x76) in CHW format
 * @param features: pointer to model output (28*28*76 = 59584 bytes)
 * @param pooled: output buffer for 1x1 pooling (76 floats)
 *
 * CHW format: features[c * spatial_h * spatial_w + h * spatial_w + w]
 */
void adaptive_avg_pool_1x1(const ai_i8* features, float* pooled)
{
    const int H = 28;
    const int W = 28;
    const int C = 76;
    const int N = H * W;

    const float scale = OUTPUT_SCALE;
    const float zp = OUTPUT_ZERO_POINT;

    for (int c = 0; c < C; c++)
    {
        int32_t sum_q = 0;

        const ai_i8* ptr = features + c * N;

        // faster linear scan (removes inner loop)
        for (int i = 0; i < N; i++)
        {
            sum_q += ptr[i];
        }

        // correct dequantized mean
        float mean_q = (float)sum_q / (float)N;

        pooled[c] = (mean_q - zp) * scale;
    }
}
/**
 * @brief Compute adaptive average pooling at 2x2
 * Divides 28x28 spatial into 2x2 blocks and averages each block
 * Output: 2x2x76 = 304 values
 * @param features: pointer to model output (28*28*76) in CHW format
 * @param pooled: output buffer for 2x2 pooling (304 floats)
 *
 * CHW format: features[c * spatial_h * spatial_w + h * spatial_w + w]
 * Output also in CHW: pooled[c * out_h * out_w + oh * out_w + ow]
 */
void adaptive_avg_pool_2x2(const ai_i8* features, float* pooled)
{
    const int H = 28;
    const int W = 28;
    const int C = 76;

    const int out_h = 2;
    const int out_w = 2;

    const int block_h = H >> 1;   // 14
    const int block_w = W >> 1;   // 14

    const int spatial_size = H * W;
    const int out_size = out_h * out_w;

    const float scale = OUTPUT_SCALE;
    const float zp = OUTPUT_ZERO_POINT;

    for (int c = 0; c < C; c++)
    {
        const ai_i8* base = features + c * spatial_size;

        for (int oh = 0; oh < out_h; oh++)
        {
            int h_start = oh * block_h;
            int h_end   = h_start + block_h;

            for (int ow = 0; ow < out_w; ow++)
            {
                int w_start = ow * block_w;
                int w_end   = w_start + block_w;

                int32_t sum_q = 0;

                for (int h = h_start; h < h_end; h++)
                {
                    const ai_i8* row = base + h * W;

                    for (int w = w_start; w < w_end; w++)
                    {
                        sum_q += row[w];
                    }
                }

                float mean_q = (float)sum_q / (float)(block_h * block_w);

                int out_idx = c * out_size + oh * out_w + ow;
                pooled[out_idx] = (mean_q - zp) * scale;
            }
        }
    }
}
/**
 * @brief Concatenate and L2-normalize pooled features
 * Concatenates 1x1 pooling (76) with 2x2 pooling (304) -> 380 total
 * @param pool_1x1: 1x1 pooled features (76 values)
 * @param pool_2x2: 2x2 pooled features (304 values)
 * @param output: output buffer (380 values, L2 normalized)
 */
void pool_features(const float* pool_1x1, const float* pool_2x2, float* output)
{
  const int dim1x1 = 76;
  const int dim2x2 = 304;
  const int total_dim = 380;

  /* Concatenate: [pool_1x1 | pool_2x2] */
  memcpy(output, pool_1x1, dim1x1 * sizeof(float));
  memcpy(output + dim1x1, pool_2x2, dim2x2 * sizeof(float));

  /* L2 normalization */
  float norm_sq = 0.0f;
  for (int i = 0; i < total_dim; i++)
  {
    norm_sq += output[i] * output[i];
  }

  float norm = sqrtf(norm_sq);
  if (norm > 1e-8f)  /* Avoid division by zero */
  {
    for (int i = 0; i < total_dim; i++)
    {
      output[i] /= norm;
    }
  }
}

/**
 * @brief Compute anomaly score matching the Python reference implementation.
 *
 * Python reference (anomaly_score function in benchmark script):
 *   v = F.normalize(v, dim=1)                          # L2-normalize query
 *   dist = ((v.unsqueeze(1) - memory.unsqueeze(0))**2).sum(dim=2)  # squared L2 distance
 *   score = dist.min(dim=1).values                     # min over memory bank
 *
 * Key differences vs the old C implementation:
 *   - OLD: used dot-product / cosine similarity  -> WRONG
 *   - NEW: uses squared Euclidean distance       -> matches Python
 *   - OLD: clamped result to [0, 1]              -> WRONG (corrupts values)
 *   - NEW: returns raw min-distance, no clamping -> matches Python
 *   - Memory vectors are dequantized (int8 * scale) then L2-renormalized
 *     to match the Python quantize_memory() which calls F.normalize after
 *     dequantizing the int8 values.
 *
 * @param features: L2-normalized query vector (MEMORY_VECTOR_DIM floats)
 * @return anomaly score (min squared Euclidean distance to memory bank)
 *         Higher = more anomalous. No clamping applied.
 */

/*
float compute_anomaly_score(const float* features)
{
  // v = F.normalize(v, dim=1) - normalize the query features
  float v[MEMORY_VECTOR_DIM];
  float norm_sq = 0.0f;
  for (int d = 0; d < MEMORY_VECTOR_DIM; d++)
  {
    norm_sq += features[d] * features[d];
  }
  float norm = sqrtf(norm_sq);
  for (int d = 0; d < MEMORY_VECTOR_DIM; d++)
  {
    v[d] = (norm > 1e-8f) ? (features[d] / norm) : 0.0f;
  }

  // dist = ((v - memory)**2).sum(); score = dist.min()
  float min_dist = 3.402823466e+38F;
  for (int m = 0; m < MEMORY_N_VECTORS; m++)
  {
    float dist = 0.0f;
    for (int d = 0; d < MEMORY_VECTOR_DIM; d++)
    {
      float mem_val = (float)memory_bank[m][d] * MEMORY_SCALE;
      float diff = v[d] - mem_val;
      dist += diff * diff;
    }
    if (dist < min_dist)
      min_dist = dist;
  }

  return min_dist;
}
*/

float compute_anomaly_score(const float* v)
{
    float min_dist = 10000;

    for (int m = 0; m < MEMORY_N_VECTORS; m++)
    {
        const float* mem = memory_bank_norm[m];

        float dist = 0.0f;

        #pragma GCC unroll 4
        for (int d = 0; d < MEMORY_VECTOR_DIM; d++)
        {
            float diff = v[d] - mem[d];
            dist += diff * diff;
        }

        if (dist < min_dist)
            min_dist = dist;
    }

    return min_dist;
}

int acquire_and_process_data(ai_i8* data[])
{
  /* Receive image data from USART1 */
  if (data[0] != NULL)
  {
    //printf("\r\n[MCU ACQUIRE] === WAITING FOR IMAGE ===\r\n");
    fflush(stdout);
    /* Allow UART text to flush before binary receive begins */
    HAL_Delay(100);

    /* Wait indefinitely for image over USART1 (no timeout, no fallback) */
    int recv_result = usart_receive_image(&huart1, (uint8_t*)data[0], HAL_MAX_DELAY);

    if (recv_result == 0)
    {
      //printf("[MCU ACQUIRE] Image received\r\n");
      fflush(stdout);

      return 0;
    }    else
    {
      //printf("[MCU ACQUIRE] ERROR: Failed to receive image\r\n");
      fflush(stdout);
      return -1;
    }
  }

  //printf("[MCU ACQUIRE] ERROR: Input buffer not allocated\r\n");
  fflush(stdout);
  return -1;
}

int post_process(ai_i8* data[], uint32_t inference_time, uint32_t loadpic_us)
{
  /* Compute anomaly score from model output
   * Output format: int8 quantized features
   * Output dimensions: 28 x 28 x 76 = 59,584 values
   */

  if (data[0] != NULL)
  {
	 uint32_t start = get_cycles();
    /* Allocate buffers for pooling (on stack if possible, or use static) */
    static float pool_1x1[76];
    static float pool_2x2[304];
    static float pooled_features[380];

    /* Step 1: Adaptive average pooling at 1x1 (global average) */
    //printf("[MCU POST] Step 1: Computing 1x1 pooling...\r\n");
    fflush(stdout);
    adaptive_avg_pool_1x1(data[0], pool_1x1);
    //printf("[MCU POST] Pool 1x1 done (76 values)\r\n");
    fflush(stdout);

    /* Step 2: Adaptive average pooling at 2x2 */
    //printf("[MCU POST] Step 2: Computing 2x2 pooling...\r\n");
    fflush(stdout);
    adaptive_avg_pool_2x2(data[0], pool_2x2);
    //printf("[MCU POST] Pool 2x2 done (304 values)\r\n");
    fflush(stdout);

    /* Step 3: Concatenate and L2-normalize */
    //printf("[MCU POST] Step 3: Concatenating and normalizing features...\r\n");
    fflush(stdout);
    pool_features(pool_1x1, pool_2x2, pooled_features);
    //printf("[MCU POST] Features pooled and normalized (380 dims)\r\n");
    fflush(stdout);

    /* Step 4: Compute anomaly score
     *
     * Returns min squared Euclidean distance to memory bank.
     * Score is NOT clamped - raw distance value, same as Python reference.
     * The threshold was calibrated offline as: mu + 4*sigma on normal
     * training samples (see compute_threshold() in the Python script).
     * Update ANOMALY_THRESHOLD below to match the value printed by
     * the Python benchmark pipeline for your specific memory bank.
     * printf("[MCU POST] Step 4: Computing anomaly score...\r\n");
     */

    fflush(stdout);
    float anomaly = compute_anomaly_score(pooled_features);

    /* Threshold: set this to the value of `thr` printed by compute_threshold()
     * in the Python benchmark script (mu + 4*sigma on normal training samples).
     * The old hardcoded 0.5f was wrong for a squared-distance metric.
     */
#ifndef ANOMALY_THRESHOLD
#define ANOMALY_THRESHOLD (0.006842f)   /* <-- UPDATE with value from Python pipeline */
#endif

    uint8_t is_anomaly = (anomaly > ANOMALY_THRESHOLD) ? 1 : 0;

    /* Output results */
    //printf("\r\n[MCU RESULT] ============= ANOMALY DETECTION RESULTS =============\r\n");

    /* Print score with 6 decimal places using integer arithmetic */
    int32_t anomaly_int  = (int32_t)(anomaly);
    int32_t anomaly_frac = (int32_t)((anomaly - (float)anomaly_int) * 1000000.0f);
    if (anomaly_frac < 0) anomaly_frac = -anomaly_frac;
    //printf("[MCU RESULT] Anomaly Score: %ld.%06ld\r\n", anomaly_int, anomaly_frac);

    /*if (is_anomaly)
    {
      printf("[MCU RESULT] Status: ANOMALY DETECTED (score > threshold)\r\n");
    }
    else
    {
      printf("[MCU RESULT] Status: NORMAL (score <= threshold)\r\n");
    }*/
    //printf("[MCU RESULT] ==============================================================\r\n");
    fflush(stdout);

    /* IMPORTANT: Send result over USART */
    //printf("[MCU RESULT] Sending binary result...\r\n");
    fflush(stdout);
    uint32_t end = get_cycles();
    uint32_t cycles = end - start;
    uint32_t anomaly_us = cycles *RATIO;


    usart_send_result(&huart1, anomaly, is_anomaly, inference_time, anomaly_us, loadpic_us);
    //printf("[MCU RESULT] Result sent\r\n");
    fflush(stdout);


    return 0;
  }

  //printf("[MCU POST] ERROR: Output buffer not available\r\n");
  return -1;
}
/* USER CODE END 2 */

/* Entry points --------------------------------------------------------------*/

void MX_X_CUBE_AI_Init(void)
{
    /* USER CODE BEGIN 5 */
  //printf("\r\n========== MCU STARTUP ==========\r\n");
  //printf("TEMPLATE - initialization\r\n");
  fflush(stdout);
  DWT_Init();

  ai_boostrap(data_activations0);

  init_memory_bank();
  /* Initialize USART protocol for image reception */
  usart_protocol_init(&huart1);

  //printf("========== WAITING FOR HOST CONNECTION ==========\r\n");
  fflush(stdout);
    /* USER CODE END 5 */
}

void MX_X_CUBE_AI_Process(void)
{
  int res;

  //printf("[MCU MAIN] Starting inference loop\r\n");
  uint32_t start;
  uint32_t end;
  uint32_t cycles;
  uint32_t inference_us;
  uint32_t loadpic_us;


  fflush(stdout);

  if (!network) {
        //ai_log_err(err, "Network not initialized");
    return;
  }

  while (1)
  {
    /* Receive image */
	start = get_cycles();
    res = acquire_and_process_data(data_ins);
    end = get_cycles();
    cycles = end - start;
    loadpic_us = cycles * RATIO;



    if (res != 0) {
      //printf("[MCU MAIN] Image receive failed\r\n");
      continue;
    }

    /* Run inference */
    start = get_cycles();

    res = ai_run();

    end = get_cycles();
    cycles = end - start;
    inference_us = cycles *RATIO;


    if (res != 0) {
      //printf("[MCU MAIN] Inference failed\r\n");
      continue;
    }

    /* Send result */
    res = post_process(data_outs, inference_us, loadpic_us);

    if (res != 0) {
      //printf("[MCU MAIN] Post-process failed\r\n");
    }
  }
}
#ifdef __cplusplus
}
#endif
