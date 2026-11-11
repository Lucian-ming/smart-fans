/**
 * @file encoder.h
 * @brief EC11 旋转编码器驱动 (PA6 TIM3_CH1, PA7 TIM3_CH2)
 *
 * 特性：
 * - 采用 TIM3 原生硬件正交编码器接口模式 (TI12 4倍频)
 * - 启用数字硬件输入滤波 (IC1F/IC2F) 硬件级过滤机械触点抖动
 * - 无锁差分读取计数 (避免教学代码中的读后清零竞争窗口)
 * - 明确不初始化 PB12 按键
 */
#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

void encoder_init(void);
int16_t encoder_get_delta(void);
int32_t encoder_get_total_count(void);

#ifdef __cplusplus
}
#endif
