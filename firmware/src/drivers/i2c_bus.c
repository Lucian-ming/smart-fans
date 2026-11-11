/**
 * @file i2c_bus.c
 * @brief 共享 I2C1 健壮总线驱动实现 (PB6 SCL, PB7 SDA)
 */
#include "i2c_bus.h"
#include "hal/delay_us.h"
#include "stm32f1xx_hal.h"
#include "config/pins.h"
#include <stdio.h>

#define I2C_HALF_DELAY_US 5U   /* 标准 100 kHz I2C，兼顾长面包板寄生电容与 4.7k 上拉电阻 */
#define I2C_TIMEOUT_LOOPS 500U

static inline void scl_high(void)
{
    HAL_GPIO_WritePin(I2C1_Port, I2C1_SCL_Pin, GPIO_PIN_SET);
}

static inline void scl_low(void)
{
    HAL_GPIO_WritePin(I2C1_Port, I2C1_SCL_Pin, GPIO_PIN_RESET);
}

static inline void sda_high(void)
{
    HAL_GPIO_WritePin(I2C1_Port, I2C1_SDA_Pin, GPIO_PIN_SET);
}

static inline void sda_low(void)
{
    HAL_GPIO_WritePin(I2C1_Port, I2C1_SDA_Pin, GPIO_PIN_RESET);
}

static inline uint8_t sda_read(void)
{
    return (uint8_t)HAL_GPIO_ReadPin(I2C1_Port, I2C1_SDA_Pin);
}

static inline uint8_t scl_read(void)
{
    return (uint8_t)HAL_GPIO_ReadPin(I2C1_Port, I2C1_SCL_Pin);
}

static bool wait_scl_high(void)
{
    uint32_t timeout = I2C_TIMEOUT_LOOPS;
    scl_high();
    while (scl_read() == GPIO_PIN_RESET) {
        if (--timeout == 0) {
            return false; /* 时钟延展超时 */
        }
        delay_us(1);
    }
    return true;
}

void i2c_bus_init(void)
{
    GPIO_InitTypeDef gpio = {0};

    __HAL_RCC_GPIOB_CLK_ENABLE();

    /* PB6 (SCL) 与 PB7 (SDA)：开漏输出，外接上拉（板载有4.7k） */
    gpio.Pin = I2C1_SCL_Pin | I2C1_SDA_Pin;
    gpio.Mode = GPIO_MODE_OUTPUT_OD;
    gpio.Pull = GPIO_PULLUP;
    gpio.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(I2C1_Port, &gpio);

    scl_high();
    sda_high();

    /* 初始化时执行一次总线清理与复位 */
    i2c_bus_recover();
}

void i2c_bus_recover(void)
{
    /* 硬件死锁恢复：当面包板或从机复位导致从机将 SDA 持续拉低时，
     * 主机产生最多 9 个时钟脉冲，迫使从机移出数据位并释放 SDA
     */
    sda_high();
    delay_us(I2C_HALF_DELAY_US);

    for (int i = 0; i < 9; i++) {
        scl_low();
        delay_us(I2C_HALF_DELAY_US);
        scl_high();
        delay_us(I2C_HALF_DELAY_US);
        if (sda_read() != GPIO_PIN_RESET) {
            break; /* 从机已释放 SDA */
        }
    }

    /* 发送一个明确的 STOP 条件 */
    sda_low();
    delay_us(I2C_HALF_DELAY_US);
    scl_high();
    delay_us(I2C_HALF_DELAY_US);
    sda_high();
    delay_us(I2C_HALF_DELAY_US);
}

static bool i2c_start(void)
{
    sda_high();
    if (!wait_scl_high()) return false;
    delay_us(I2C_HALF_DELAY_US);

    if (sda_read() == GPIO_PIN_RESET) {
        /* 总线被异常占用，尝试恢复 */
        i2c_bus_recover();
        sda_high();
        if (!wait_scl_high()) return false;
    }

    sda_low();
    delay_us(I2C_HALF_DELAY_US);
    scl_low();
    delay_us(I2C_HALF_DELAY_US);
    return true;
}

static void i2c_stop(void)
{
    sda_low();
    delay_us(I2C_HALF_DELAY_US);
    scl_high();
    delay_us(I2C_HALF_DELAY_US);
    sda_high();
    delay_us(I2C_HALF_DELAY_US);
}

static bool i2c_write_byte(uint8_t byte)
{
    for (uint8_t i = 0; i < 8; i++) {
        if (byte & 0x80) {
            sda_high();
        } else {
            sda_low();
        }
        byte <<= 1;
        delay_us(I2C_HALF_DELAY_US);

        if (!wait_scl_high()) return false;
        delay_us(I2C_HALF_DELAY_US);
        scl_low();
        delay_us(I2C_HALF_DELAY_US);
    }

    /* 读从机 ACK */
    sda_high();
    delay_us(I2C_HALF_DELAY_US);
    if (!wait_scl_high()) return false;
    delay_us(I2C_HALF_DELAY_US);

    bool ack = (sda_read() == GPIO_PIN_RESET);
    scl_low();
    delay_us(I2C_HALF_DELAY_US);

    return ack;
}

static uint8_t i2c_read_byte(bool send_ack)
{
    uint8_t byte = 0;
    sda_high();

    for (uint8_t i = 0; i < 8; i++) {
        byte <<= 1;
        if (!wait_scl_high()) return 0xFF;
        delay_us(I2C_HALF_DELAY_US);
        if (sda_read() != GPIO_PIN_RESET) {
            byte |= 0x01;
        }
        scl_low();
        delay_us(I2C_HALF_DELAY_US);
    }

    /* 发送主机 ACK 或 NACK */
    if (send_ack) {
        sda_low();
    } else {
        sda_high();
    }
    delay_us(I2C_HALF_DELAY_US);
    scl_high();
    delay_us(I2C_HALF_DELAY_US);
    scl_low();
    delay_us(I2C_HALF_DELAY_US);
    sda_high();

    return byte;
}

bool i2c_bus_write(uint8_t dev_addr, const uint8_t *data, uint16_t len)
{
    if (!i2c_start()) return false;

    /* 写设备 7-bit 地址 (左移1位，最低位0表示写) */
    if (!i2c_write_byte(dev_addr << 1)) {
        i2c_stop();
        return false;
    }

    for (uint16_t i = 0; i < len; i++) {
        if (!i2c_write_byte(data[i])) {
            i2c_stop();
            return false;
        }
    }

    i2c_stop();
    return true;
}

bool i2c_bus_write_reg(uint8_t dev_addr, uint8_t reg_addr, uint8_t value)
{
    uint8_t buf[2] = {reg_addr, value};
    return i2c_bus_write(dev_addr, buf, 2);
}

bool i2c_bus_read_regs(uint8_t dev_addr, uint8_t reg_addr, uint8_t *buffer, uint16_t len)
{
    if (buffer == NULL || len == 0) return false;

    if (!i2c_start()) return false;

    /* 发送寄存器地址 */
    if (!i2c_write_byte(dev_addr << 1)) {
        i2c_stop();
        return false;
    }

    if (!i2c_write_byte(reg_addr)) {
        i2c_stop();
        return false;
    }

    /* 重复起始条件进行读取 */
    if (!i2c_start()) return false;

    if (!i2c_write_byte((dev_addr << 1) | 0x01)) {
        i2c_stop();
        return false;
    }

    for (uint16_t i = 0; i < len; i++) {
        bool send_ack = (i < (len - 1));
        buffer[i] = i2c_read_byte(send_ack);
    }

    i2c_stop();
    return true;
}

bool i2c_bus_read_reg(uint8_t dev_addr, uint8_t reg_addr, uint8_t *data, uint16_t len)
{
    return i2c_bus_read_regs(dev_addr, reg_addr, data, len);
}

bool i2c_bus_probe(uint8_t dev_addr)
{
    if (!i2c_start()) return false;
    bool ack = i2c_write_byte(dev_addr << 1);
    i2c_stop();
    return ack;
}

void i2c_bus_scan(void)
{
    printf("\r\n--- I2C Bus Scan (0x01 - 0x77) ---\r\n     ");
    for (int x = 0; x < 16; x++) {
        printf("%X  ", x);
    }
    printf("\r\n");

    for (uint8_t row = 0; row < 128; row += 16) {
        printf("%02X: ", row);
        for (uint8_t col = 0; col < 16; col++) {
            uint8_t addr = row + col;
            if (addr == 0 || addr > 0x77) {
                printf("   ");
                continue;
            }
            if (i2c_bus_probe(addr)) {
                printf("%02X ", addr);
            } else {
                printf("-- ");
            }
        }
        printf("\r\n");
    }
}
