/**
 * @file i2c_bus.h
 * @brief 共享 I2C1 健壮总线驱动 (PB6 SCL, PB7 SDA)
 *
 * 针对面包板试验的高容错设计：
 * - 完备的从机 ACK 校验与微秒级超时机制，绝不死循环挂起
 * - 内置 I2C 硬件死锁恢复程序 (9 个时钟脉冲脱机解除 + STOP)
 * - 挂载设备：SSD1306 0.96 OLED (0x3C), PAJ7620 手势传感器 (0x73)
 */
#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

void i2c_bus_init(void);
void i2c_bus_recover(void);
bool i2c_bus_write(uint8_t dev_addr, const uint8_t *data, uint16_t len);
bool i2c_bus_write_reg(uint8_t dev_addr, uint8_t reg_addr, uint8_t value);
bool i2c_bus_read_reg(uint8_t dev_addr, uint8_t reg_addr, uint8_t *data, uint16_t len);
bool i2c_bus_read_regs(uint8_t dev_addr, uint8_t reg_addr, uint8_t *buffer, uint16_t len);
bool i2c_bus_probe(uint8_t dev_addr);
void i2c_bus_scan(void);

#ifdef __cplusplus
}
#endif
