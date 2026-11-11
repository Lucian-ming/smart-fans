/**
 * @file motor.c
 * @brief TB6612FNG 直流电机驱动实现
 */
#include "motor.h"
#include "stm32f1xx_hal.h"
#include "config/pins.h"

static TIM_HandleTypeDef g_htim2;
static int8_t g_current_speed = 0;

static void motor_gpio_init(void)
{
    GPIO_InitTypeDef gpio = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();

    /* 必须先拉低 STBY 与方向控制脚，再配置为输出，防止上电抖动冲转 */
    HAL_GPIO_WritePin(TB_STBY_Port, TB_STBY_Pin, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(TB_AIN1_Port, TB_AIN1_Pin, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(TB_AIN2_Port, TB_AIN2_Pin, GPIO_PIN_RESET);

    /* PB0: TB_STBY */
    gpio.Pin = TB_STBY_Pin;
    gpio.Mode = GPIO_MODE_OUTPUT_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(TB_STBY_Port, &gpio);

    /* PA1: TB_AIN1, PA5: TB_AIN2 */
    gpio.Pin = TB_AIN1_Pin | TB_AIN2_Pin;
    gpio.Mode = GPIO_MODE_OUTPUT_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOA, &gpio);

    /* PA0: TIM2_CH1 复用推挽输出 */
    gpio.Pin = TB_PWMA_Pin;
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(TB_PWMA_Port, &gpio);
}

static void motor_timer_init(void)
{
    TIM_OC_InitTypeDef oc_config = {0};

    __HAL_RCC_TIM2_CLK_ENABLE();

    /* APB1 预分频为 2，故 TIM2CLK = PCLK1 * 2 = 36MHz * 2 = 72MHz
     * 目标频率 25kHz: PSC = 0, ARR = 72,000,000 / 25,000 - 1 = 2879
     */
    g_htim2.Instance = TIM2;
    g_htim2.Init.Prescaler = 0;
    g_htim2.Init.CounterMode = TIM_COUNTERMODE_UP;
    g_htim2.Init.Period = MOTOR_PWM_ARR_25KHZ;
    g_htim2.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    g_htim2.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
    HAL_TIM_PWM_Init(&g_htim2);

    oc_config.OCMode = TIM_OCMODE_PWM1;
    oc_config.Pulse = 0; /* 默认 0 占空比 */
    oc_config.OCPolarity = TIM_OCPOLARITY_HIGH;
    oc_config.OCFastMode = TIM_OCFAST_DISABLE;
    HAL_TIM_PWM_ConfigChannel(&g_htim2, &oc_config, TIM_CHANNEL_1);

    HAL_TIM_PWM_Start(&g_htim2, TIM_CHANNEL_1);
}

void motor_init(void)
{
    motor_gpio_init();
    motor_timer_init();
    motor_emergency_stop();
}

void motor_set_speed(int8_t percent)
{
    if (percent > 100) percent = 100;
    if (percent < -100) percent = -100;

    g_current_speed = percent;

    if (percent == 0) {
        /* 停止电机：先关 PWM，再关方向，最后关 STBY */
        __HAL_TIM_SET_COMPARE(&g_htim2, TIM_CHANNEL_1, 0);
        HAL_GPIO_WritePin(TB_AIN1_Port, TB_AIN1_Pin, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(TB_AIN2_Port, TB_AIN2_Pin, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(TB_STBY_Port, TB_STBY_Pin, GPIO_PIN_RESET);
        return;
    }

    uint32_t duty_counts;
    if (percent > 0) {
        /* 正转：AIN1=1, AIN2=0 */
        HAL_GPIO_WritePin(TB_AIN1_Port, TB_AIN1_Pin, GPIO_PIN_SET);
        HAL_GPIO_WritePin(TB_AIN2_Port, TB_AIN2_Pin, GPIO_PIN_RESET);
        duty_counts = ((uint32_t)percent * (MOTOR_PWM_ARR_25KHZ + 1)) / 100U;
    } else {
        /* 反转：AIN1=0, AIN2=1 */
        HAL_GPIO_WritePin(TB_AIN1_Port, TB_AIN1_Pin, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(TB_AIN2_Port, TB_AIN2_Pin, GPIO_PIN_SET);
        duty_counts = ((uint32_t)(-percent) * (MOTOR_PWM_ARR_25KHZ + 1)) / 100U;
    }

    if (duty_counts > (MOTOR_PWM_ARR_25KHZ + 1)) {
        duty_counts = MOTOR_PWM_ARR_25KHZ + 1;
    }

    __HAL_TIM_SET_COMPARE(&g_htim2, TIM_CHANNEL_1, duty_counts);

    /* 方向与占空比就绪后，使能 TB6612 STBY */
    HAL_GPIO_WritePin(TB_STBY_Port, TB_STBY_Pin, GPIO_PIN_SET);
}

void motor_emergency_stop(void)
{
    g_current_speed = 0;
    /* 立即断开使能 */
    HAL_GPIO_WritePin(TB_STBY_Port, TB_STBY_Pin, GPIO_PIN_RESET);
    /* 关断方向管脚 */
    HAL_GPIO_WritePin(TB_AIN1_Port, TB_AIN1_Pin, GPIO_PIN_RESET);
    HAL_GPIO_WritePin(TB_AIN2_Port, TB_AIN2_Pin, GPIO_PIN_RESET);
    /* 占空比归零 */
    __HAL_TIM_SET_COMPARE(&g_htim2, TIM_CHANNEL_1, 0);
}

int8_t motor_get_speed(void)
{
    return g_current_speed;
}

bool motor_is_active(void)
{
    return (g_current_speed != 0 &&
            HAL_GPIO_ReadPin(TB_STBY_Port, TB_STBY_Pin) == GPIO_PIN_SET);
}
