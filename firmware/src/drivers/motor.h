/**
 * @file motor.h
 * @brief TB6612FNG 直流电机驱动 (PA0 PWM 25kHz, PA1 AIN1, PA5 AIN2, PB0 STBY)
 *
 * 严格上电安全保障：
 * 1. 上电初期 STBY 保持低电平，电机输出高阻
 * 2. 启用前必须先设方向与0占空比，最后使能STBY
 * 3. 25kHz 超声频PWM计算基于 APB1 倍频后的 72MHz 定时器时钟
 */
#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    MOTOR_DIR_STOP = 0,
    MOTOR_DIR_FORWARD,
    MOTOR_DIR_REVERSE
} motor_dir_t;

#define MOTOR_PWM_ARR_25KHZ  2879U  /* 72MHz / (0+1) / (2879+1) = 25000Hz */

void motor_init(void);
void motor_set_speed(int8_t percent); /* -100 ~ +100, 0为停止 */
void motor_emergency_stop(void);
int8_t motor_get_speed(void);
bool motor_is_active(void);

#ifdef __cplusplus
}
#endif
