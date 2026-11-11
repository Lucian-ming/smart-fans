/**
 * @file max7219.h
 * @brief MAX7219 驱动 8x8 点阵模块 (支持双模块级联驱动)
 *
 * STM32 引脚接口:
 *   CS   -> PB1  (LOAD)
 *   CLK  -> PB10 (时钟)
 *   DIN  -> PB11 (数据)
 *   VCC  -> 5V (或 3.3V)
 *   GND  -> GND
 *
 * 级联引脚 (点阵1 -> 点阵2):
 *   点阵1 DOUT -> 点阵2 DIN
 *   点阵1 CLK  -> 点阵2 CLK
 *   点阵1 CS   -> 点阵2 CS
 *   点阵1 VCC  -> 点阵2 VCC
 *   点阵1 GND  -> 点阵2 GND
 */
#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* MAX7219 寄存器地址定义 */
#define MAX7219_REG_NOOP        0x00
#define MAX7219_REG_DIGIT0      0x01
#define MAX7219_REG_DIGIT1      0x02
#define MAX7219_REG_DIGIT2      0x03
#define MAX7219_REG_DIGIT3      0x04
#define MAX7219_REG_DIGIT4      0x05
#define MAX7219_REG_DIGIT5      0x06
#define MAX7219_REG_DIGIT6      0x07
#define MAX7219_REG_DIGIT7      0x08
#define MAX7219_REG_DECODEMODE  0x09
#define MAX7219_REG_INTENSITY   0x0A
#define MAX7219_REG_SCANLIMIT   0x0B
#define MAX7219_REG_SHUTDOWN    0x0C
#define MAX7219_REG_DISPLAYTEST 0x0F

/* 硬件引脚定义 (若未在 pins.h 中定义则使用默认) */
#ifndef MATRIX_Port
#define MATRIX_Port             GPIOB
#endif
#ifndef MATRIX_CS_Pin
#define MATRIX_CS_Pin           GPIO_PIN_1
#endif
#ifndef MATRIX_CLK_Pin
#define MATRIX_CLK_Pin          GPIO_PIN_10
#endif
#ifndef MATRIX_DIN_Pin
#define MATRIX_DIN_Pin          GPIO_PIN_11
#endif

typedef enum {
    MATRIX_MODE_STATIC = 0,
    MATRIX_MODE_FAN_ROTATE,
    MATRIX_MODE_HEART_PULSE
} matrix_mode_t;

/* 初始化与基础控制 */
void max7219_init(void);
void max7219_write_cascade(uint8_t reg1, uint8_t data1, uint8_t reg2, uint8_t data2);
void max7219_write_all(uint8_t reg, uint8_t val);
void max7219_write_reg(uint8_t reg, uint8_t data);

/* 点阵绘制 API */
void max7219_render_dual(const uint8_t left[8], const uint8_t right[8]);
void max7219_draw_buffer(const uint8_t buffer[8]);
void max7219_set_row(uint8_t row, uint8_t data);
void max7219_set_all(bool on);
void max7219_clear(void);

/* 参数与模式 */
void max7219_set_intensity(uint8_t level); /* 0 ~ 15 */
void max7219_set_display_test(bool enable);
void max7219_set_shutdown(bool shutdown);
void max7219_set_mode(matrix_mode_t mode);
matrix_mode_t max7219_get_mode(void);
void max7219_tick(uint32_t now_ms, int8_t fan_speed);

#ifdef __cplusplus
}
#endif
