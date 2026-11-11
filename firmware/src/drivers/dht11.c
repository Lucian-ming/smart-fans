/**
 * @file dht11.c
 * @brief DHT11 单总线温湿度传感器驱动实现 (PB9)
 */
#include "dht11.h"
#include "hal/delay_us.h"
#include "stm32f1xx_hal.h"
#include "config/pins.h"

static dht11_reading_t g_last_reading = {0.0f, 0.0f, false};

static inline void line_low(void)
{
    HAL_GPIO_WritePin(DHT11_DATA_Port, DHT11_DATA_Pin, GPIO_PIN_RESET);
}

static inline void line_high(void)
{
    HAL_GPIO_WritePin(DHT11_DATA_Port, DHT11_DATA_Pin, GPIO_PIN_SET);
}

static inline uint8_t line_read(void)
{
    return (uint8_t)HAL_GPIO_ReadPin(DHT11_DATA_Port, DHT11_DATA_Pin);
}

static bool wait_level(uint8_t target_level, uint32_t timeout_us)
{
    while (line_read() != target_level) {
        if (timeout_us == 0) return false;
        delay_us(1);
        timeout_us--;
    }
    return true;
}

void dht11_init(void)
{
    GPIO_InitTypeDef gpio = {0};

    __HAL_RCC_GPIOB_CLK_ENABLE();

    /* PB9 开漏输出带上拉，单总线双向直接读写，无需反复切换模式 */
    gpio.Pin = DHT11_DATA_Pin;
    gpio.Mode = GPIO_MODE_OUTPUT_OD;
    gpio.Pull = GPIO_PULLUP;
    gpio.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(DHT11_DATA_Port, &gpio);

    line_high();
}

bool dht11_read(float *temperature, float *humidity)
{
    uint8_t data[5] = {0};

    /* 1. 主机发送起始信号：拉低 20ms */
    line_low();
    HAL_Delay(20);

    /* 2. 释放总线拉高 30us，等待从机响应 */
    line_high();
    delay_us(30);

    /* 3. 校验 DHT11 响应信号：80us 低 + 80us 高 */
    if (!wait_level(0, 150)) return false; /* 等待被拉低 */
    if (!wait_level(1, 150)) return false; /* 等待拉高 */
    if (!wait_level(0, 150)) return false; /* 等待高电平结束进入数据帧 */

    /* 4. 接收 40 位数据 (关闭全局中断以保证微秒级延时绝对精确) */
    __disable_irq();
    for (int i = 0; i < 40; i++) {
        /* 每一位以 50us 低电平起始 */
        if (!wait_level(1, 100)) {
            __enable_irq();
            line_high();
            return false;
        }

        /* 高电平持续时间决定 0 (26-28us) 或 1 (70us) */
        delay_us(40);
        if (line_read() == GPIO_PIN_SET) {
            data[i / 8] |= (1 << (7 - (i % 8)));
            /* 等待高电平结束 */
            if (!wait_level(0, 100)) {
                __enable_irq();
                line_high();
                return false;
            }
        }
    }
    __enable_irq();

    /* 恢复总线空闲高电平 */
    line_high();

    /* 5. 校验和检验 */
    uint8_t sum = (uint8_t)(data[0] + data[1] + data[2] + data[3]);
    if (sum != data[4] || sum == 0) {
        return false;
    }

    /* DHT11: data[0]=湿度整数, data[1]=湿度小数, data[2]=温度整数, data[3]=温度小数 */
    float hum = (float)data[0] + ((float)data[1] * 0.1f);
    float tem = (float)data[2] + ((float)data[3] * 0.1f);

    if (humidity) *humidity = hum;
    if (temperature) *temperature = tem;

    g_last_reading.temperature = tem;
    g_last_reading.humidity = hum;
    g_last_reading.valid = true;

    return true;
}

dht11_reading_t dht11_get_last_reading(void)
{
    return g_last_reading;
}
