/**
 * @file max7219.c
 * @brief MAX7219 驱动 8x8 点阵模块 (支持双模块级联驱动)
 */
#include "max7219.h"
#include "config/pins.h"
#include "hal/delay_us.h"
#include "stm32f1xx_hal.h"

/* 4 帧顺时针平滑旋转小风车点阵字模 */
static const uint8_t g_fan_frames[4][8] = {
    /* Frame 0: 十字带弯尖叶片 (0°) */
    {0x18, 0x18, 0x1B, 0xFF, 0xFF, 0xD8, 0x18, 0x18},
    /* Frame 1: 45° 倾斜对角叶片 (45°) */
    {0x03, 0x06, 0x1E, 0x3C, 0x3C, 0x78, 0x60, 0xC0},
    /* Frame 2: 反向十字弯尖 (90°) */
    {0x18, 0x18, 0x18, 0xDF, 0xFB, 0x18, 0x18, 0x18},
    /* Frame 3: 135° 倾斜对角叶片 (135°) */
    {0xC0, 0x60, 0x78, 0x3C, 0x3C, 0x1E, 0x06, 0x03}
};

static matrix_mode_t g_matrix_mode = MATRIX_MODE_FAN_ROTATE;
static uint32_t g_last_frame_ms = 0;
static uint8_t g_cur_frame = 0;

static inline void cs_high(void)
{
    HAL_GPIO_WritePin(MATRIX_Port, MATRIX_CS_Pin, GPIO_PIN_SET);
}

static inline void cs_low(void)
{
    HAL_GPIO_WritePin(MATRIX_Port, MATRIX_CS_Pin, GPIO_PIN_RESET);
}

static inline void clk_high(void)
{
    HAL_GPIO_WritePin(MATRIX_Port, MATRIX_CLK_Pin, GPIO_PIN_SET);
}

static inline void clk_low(void)
{
    HAL_GPIO_WritePin(MATRIX_Port, MATRIX_CLK_Pin, GPIO_PIN_RESET);
}

static inline void din_set(bool high)
{
    HAL_GPIO_WritePin(MATRIX_Port, MATRIX_DIN_Pin, high ? GPIO_PIN_SET : GPIO_PIN_RESET);
}

static void send_byte(uint8_t byte)
{
    for (int i = 7; i >= 0; i--) {
        clk_low();
        din_set((byte >> i) & 0x01);
        delay_us(1);
        clk_high();
        delay_us(1);
    }
}

/**
 * @brief 级联双模块写寄存器
 * @param reg1 模块1寄存器
 * @param data1 模块1数据
 * @param reg2 模块2寄存器
 * @param data2 模块2数据
 */
void max7219_write_cascade(uint8_t reg1, uint8_t data1, uint8_t reg2, uint8_t data2)
{
    cs_low();
    delay_us(1);

    /* 先发送进入模块2 (右眼) 的数据，溢出过去 */
    send_byte(reg2);
    send_byte(data2);

    /* 后发送停留在模块1 (左眼) 的数据 */
    send_byte(reg1);
    send_byte(data1);

    clk_low();
    delay_us(1);
    cs_high();
    delay_us(1);
}

/**
 * @brief 向所有级联模块广播写入相同寄存器和数值
 */
void max7219_write_all(uint8_t reg, uint8_t val)
{
    max7219_write_cascade(reg, val, reg, val);
}

/**
 * @brief 兼容单模块写寄存器 (同时向模块1与模块2写入)
 */
void max7219_write_reg(uint8_t reg, uint8_t data)
{
    max7219_write_all(reg, data);
}

void max7219_render_dual(const uint8_t left[8], const uint8_t right[8])
{
    for (uint8_t r = 0; r < 8; r++) {
        uint8_t row_addr = r + 1;
        uint8_t d_left = left ? left[r] : 0x00;
        uint8_t d_right = right ? right[r] : 0x00;
        max7219_write_cascade(row_addr, d_left, row_addr, d_right);
    }
}

void max7219_init(void)
{
    GPIO_InitTypeDef gpio = {0};

    __HAL_RCC_GPIOB_CLK_ENABLE();

    /* 配置 PB1 (CS), PB10 (CLK), PB11 (DIN) 为推挽输出 */
    gpio.Pin = MATRIX_CS_Pin | MATRIX_CLK_Pin | MATRIX_DIN_Pin;
    gpio.Mode = GPIO_MODE_OUTPUT_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(MATRIX_Port, &gpio);

    cs_high();
    clk_low();
    din_set(false);
    delay_us(50);

    /* 1. 退出硬件关断模式 (Normal Operation) */
    max7219_write_all(MAX7219_REG_SHUTDOWN, 0x01);

    /* 2. 关闭 BCD 译码模式 (8x8 点阵逐像素控制) */
    max7219_write_all(MAX7219_REG_DECODEMODE, 0x00);

    /* 3. 设置扫描行数：扫描全部 8 行 (Scan Limit: 0~7) */
    max7219_write_all(MAX7219_REG_SCANLIMIT, 0x07);

    /* 4. 设置默认中等适中亮度 (4 / 15，不刺眼且清晰) */
    max7219_write_all(MAX7219_REG_INTENSITY, 0x08);

    /* 5. 退出全亮测试模式，进入正常显存驱动模式 */
    max7219_write_all(MAX7219_REG_DISPLAYTEST, 0x00);

    /* 6. 清屏 */
    max7219_clear();
}

void max7219_set_intensity(uint8_t level)
{
    if (level > 0x0F) level = 0x0F;
    max7219_write_all(MAX7219_REG_INTENSITY, level);
}

void max7219_set_all(bool on)
{
    uint8_t val = on ? 0xFF : 0x00;
    for (uint8_t row = 0; row < 8; row++) {
        max7219_write_all(MAX7219_REG_DIGIT0 + row, val);
    }
}

void max7219_set_display_test(bool enable)
{
    max7219_write_all(MAX7219_REG_DISPLAYTEST, enable ? 0x01 : 0x00);
}

void max7219_set_row(uint8_t row, uint8_t data)
{
    if (row < 8) {
        max7219_write_all(MAX7219_REG_DIGIT0 + row, data);
    }
}

void max7219_draw_buffer(const uint8_t buffer[8])
{
    if (!buffer) return;
    for (uint8_t row = 0; row < 8; row++) {
        max7219_write_all(MAX7219_REG_DIGIT0 + row, buffer[row]);
    }
}

void max7219_clear(void)
{
    max7219_set_all(false);
}

void max7219_set_shutdown(bool shutdown)
{
    max7219_write_all(MAX7219_REG_SHUTDOWN, shutdown ? 0x00 : 0x01);
}

void max7219_set_mode(matrix_mode_t mode)
{
    g_matrix_mode = mode;
    if (g_matrix_mode == MATRIX_MODE_FAN_ROTATE) {
        g_cur_frame = 0;
        max7219_draw_buffer(g_fan_frames[0]);
    }
}

matrix_mode_t max7219_get_mode(void)
{
    return g_matrix_mode;
}

void max7219_tick(uint32_t now_ms, int8_t fan_speed)
{
    if (g_matrix_mode != MATRIX_MODE_FAN_ROTATE) return;

    if (fan_speed <= 0) {
        if (g_cur_frame != 0) {
            g_cur_frame = 0;
            max7219_draw_buffer(g_fan_frames[0]);
        }
        return;
    }

    int32_t spd = fan_speed;
    if (spd > 100) spd = 100;
    if (spd < 10) spd = 10;
    uint32_t interval_ms = (uint32_t)(220 - (spd * 17) / 10);
    if (interval_ms < 45) interval_ms = 45;

    if (now_ms - g_last_frame_ms >= interval_ms) {
        g_last_frame_ms = now_ms;
        g_cur_frame = (g_cur_frame + 1) % 4;
        max7219_draw_buffer(g_fan_frames[g_cur_frame]);
    }
}
