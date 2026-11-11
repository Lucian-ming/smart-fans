/**
 * @file delay_us.h
 * @brief Cycle-accurate microsecond delay using Cortex-M3 DWT
 */
#pragma once

#include <stdint.h>
#include "stm32f1xx_hal.h"

#ifdef __cplusplus
extern "C" {
#endif

void delay_us_init(void);
void delay_us(uint32_t us);

#ifdef __cplusplus
}
#endif
