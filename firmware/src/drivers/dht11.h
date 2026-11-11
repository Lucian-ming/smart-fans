/**
 * @file dht11.h
 * @brief DHT11 单总线温湿度传感器驱动 (PB9)
 *
 * 特性：
 * - 微秒级硬件延时 (基于 DWT)
 * - 完备的逐阶段超时保护，断线/松动绝不卡死主循环
 * - 40-bit 数据校验和校验
 */
#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    float temperature;
    float humidity;
    bool valid;
} dht11_reading_t;

void dht11_init(void);
bool dht11_read(float *temperature, float *humidity);
dht11_reading_t dht11_get_last_reading(void);

#ifdef __cplusplus
}
#endif
