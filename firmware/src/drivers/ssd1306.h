/**
 * @file ssd1306.h
 * @brief 0.96寸 128x64 OLED (SSD1306) 驱动
 *
 * 挂载于共享 I2C1 总线，从机 7 位地址 0x3C
 */
#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

#define SSD1306_WIDTH  128
#define SSD1306_HEIGHT 64

bool ssd1306_init(void);
void ssd1306_clear(void);
void ssd1306_update(void);
void ssd1306_draw_string(uint8_t x, uint8_t y, const char *str);
void ssd1306_show_status(const char *mode_str, float temp, float humi,
                         int8_t fan_speed, const char *servo_str,
                         const char *last_evt);
void ssd1306_set_display_on(bool on);
bool ssd1306_is_display_on(void);

#ifdef __cplusplus
}
#endif
