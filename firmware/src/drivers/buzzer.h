/**
 * @file buzzer.h
 * @brief 有源蜂鸣器驱动 (PB15 -> 2N3904 NPN三极管基极)
 *
 * 硬件安全策略：上电默认低电平（关闭）；支持非阻塞单响、多响节拍。
 */
#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

void buzzer_init(void);
void buzzer_set(bool on);
void buzzer_beep(uint16_t duration_ms);
void buzzer_beep_pattern(uint8_t count, uint16_t on_ms, uint16_t off_ms);
void buzzer_tick(uint32_t now_ms);

#ifdef __cplusplus
}
#endif
