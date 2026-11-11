/**
 * @file encoder.c
 * @brief EC11 旋转编码器硬件模式驱动实现
 */
#include "encoder.h"
#include "stm32f1xx_hal.h"
#include "config/pins.h"

static TIM_HandleTypeDef g_htim3;
static uint16_t g_last_counter = 0;
static int32_t g_total_count = 0;

void encoder_init(void)
{
    GPIO_InitTypeDef gpio = {0};
    TIM_Encoder_InitTypeDef encoder_cfg = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_TIM3_CLK_ENABLE();

    /* PA6 (TIM3_CH1) 与 PA7 (TIM3_CH2)：上拉输入 */
    gpio.Pin = ENC_A_Pin | ENC_B_Pin;
    gpio.Mode = GPIO_MODE_INPUT;
    gpio.Pull = GPIO_PULLUP;
    gpio.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(ENC_Port, &gpio);

    /* 配置 TIM3 编码器模式：TI1 与 TI2 均计数 (4倍频)，配置 6 级输入数字滤波 */
    g_htim3.Instance = TIM3;
    g_htim3.Init.Prescaler = 0;
    g_htim3.Init.CounterMode = TIM_COUNTERMODE_UP;
    g_htim3.Init.Period = 0xFFFF;
    g_htim3.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    g_htim3.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_DISABLE;

    encoder_cfg.EncoderMode = TIM_ENCODERMODE_TI12;
    encoder_cfg.IC1Polarity = TIM_ICPOLARITY_RISING;
    encoder_cfg.IC1Selection = TIM_ICSELECTION_DIRECTTI;
    encoder_cfg.IC1Prescaler = TIM_ICPSC_DIV1;
    encoder_cfg.IC1Filter = 0x06; /* 硬件消抖滤波 */

    encoder_cfg.IC2Polarity = TIM_ICPOLARITY_RISING;
    encoder_cfg.IC2Selection = TIM_ICSELECTION_DIRECTTI;
    encoder_cfg.IC2Prescaler = TIM_ICPSC_DIV1;
    encoder_cfg.IC2Filter = 0x06;

    HAL_TIM_Encoder_Init(&g_htim3, &encoder_cfg);
    HAL_TIM_Encoder_Start(&g_htim3, TIM_CHANNEL_ALL);

    g_last_counter = (uint16_t)__HAL_TIM_GET_COUNTER(&g_htim3);
    g_total_count = 0;
}

int16_t encoder_get_delta(void)
{
    /* 使用无符号差值强转有符号 16 位，自动处理 0xFFFF 溢出回绕 */
    uint16_t current = (uint16_t)__HAL_TIM_GET_COUNTER(&g_htim3);
    int16_t raw_delta = (int16_t)(current - g_last_counter);
    g_last_counter = current;

    /* 标准 EC11 编码器通常每 1 个物理定位卡槽对应 4 个正交脉冲 (4倍频)
     * 若累计脉冲达到步长，转换为卡槽级 step
     */
    static int16_t pulse_accumulator = 0;
    pulse_accumulator += raw_delta;
    g_total_count += raw_delta;

    int16_t steps = pulse_accumulator / 4;
    pulse_accumulator %= 4;

    return steps;
}

int32_t encoder_get_total_count(void)
{
    return g_total_count;
}
