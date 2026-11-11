/**
 * @file paj7620.h
 * @brief PAJ7620U2 手势传感器驱动 (I2C: 0x73, INT: PA4)
 *
 * 9种非接触手势识别，硬件中断触发或轮询读取。
 */
#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

#define PAJ7620_GESTURE_NONE            0x0000
#define PAJ7620_GESTURE_UP              0x0001
#define PAJ7620_GESTURE_DOWN            0x0002
#define PAJ7620_GESTURE_LEFT            0x0004
#define PAJ7620_GESTURE_RIGHT           0x0008
#define PAJ7620_GESTURE_FORWARD         0x0010
#define PAJ7620_GESTURE_BACKWARD        0x0020
#define PAJ7620_GESTURE_CLOCKWISE       0x0040
#define PAJ7620_GESTURE_COUNTER_CLOCK   0x0080
#define PAJ7620_GESTURE_WAVE            0x0100

bool paj7620_init(void);
bool paj7620_is_connected(void);
uint16_t paj7620_read_gesture(void);
bool paj7620_has_interrupt(void);
const char* paj7620_gesture_to_str(uint16_t gesture);

#ifdef __cplusplus
}
#endif
