/**
 * @file main.c
 * @brief 智能风扇固件入口（STM32F103C8T6 + STM32Cube HAL，骨架）
 *
 * 当前行为：HSE 8 MHz → PLL 72 MHz，UART1 115200 日志，PC13 心跳灯 0.5 s 翻转。
 * 用于验证时钟、串口与最小系统；业务逻辑按 firmware/README.md 的顺序逐步接入。
 */
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#include "stm32f1xx_hal.h"

#include "config/pins.h"
#include "config/version.h"

static UART_HandleTypeDef g_uart1;

static void SystemClock_Config(void);
static void GPIO_Init(void);
static void UART1_Init(void);
static void log_printf(const char *fmt, ...);

/* 不可恢复错误处理：关中断、LED 常亮（定义在文件末尾） */
void Error_Handler(void);

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    GPIO_Init();
    UART1_Init();

    log_printf("\r\n=== Smart Fan firmware %s ===\r\n", FW_VERSION);
    log_printf("build %s %s, HCLK %lu Hz\r\n", __DATE__, __TIME__,
               (unsigned long)HAL_RCC_GetHCLKFreq());

    /* TODO: 按以下顺序接入（每接入一层，先用串口命令验证）
     *   hal_pwm_init();       // TIM2_CH1 @ 25 kHz
     *   fan_driver_init();    // TIM1_CH1 输入捕获测转速 + 堵转检测
     *   temp_sensor_init();   // DS18B20（单总线）或 NTC（ADC）
     *   oled_init();          // I2C1 + U8g2
     *   voice_driver_init();  // USART2 解析语音词条
     *   gesture_driver_init();// I2C1 + PAJ7620，INT 触发
     *   app_init();           // 状态机 + 温控参数（存 Flash EEPROM 模拟区）
     */

    uint32_t last = HAL_GetTick();
    while (1) {
        const uint32_t now = HAL_GetTick();
        if (now - last >= 500U) {
            last = now;
            HAL_GPIO_TogglePin(LED_GPIO_Port, LED_Pin);
            /* TODO: app_tick(now); */
        }
    }
}

/**
 * @brief 8 MHz 外部晶振 → PLL ×9 → 72 MHz，APB1 = 36 MHz，APB2 = 72 MHz
 *
 * TIM2/TIM3 挂在 APB1（36 MHz），TIM1 挂在 APB2（72 MHz），
 * 定时器时钟在 APB 分频不为 1 时自动 ×2，见各驱动里的 PSC/ARR 计算。
 */
static void SystemClock_Config(void)
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};

    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState = RCC_HSE_ON;
    osc.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
    osc.PLL.PLLState = RCC_PLL_ON;
    osc.PLL.PLLSource = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLMUL = RCC_PLL_MUL9;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK) {
        Error_Handler();
    }

    clk.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                    RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV2;
    clk.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2) != HAL_OK) {
        Error_Handler();
    }
}

/**
 * @brief 基础 GPIO：心跳 LED（PC13，蓝板低有效）、按键与编码器输入
 *
 * 编码器 A/B 先按上拉输入配置，等 TIM3 编码器模式驱动接入时再切换为复用功能。
 */
static void GPIO_Init(void)
{
    GPIO_InitTypeDef gpio = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();

    /* LED：先写高电平（熄灭），再设为输出，避免上电闪一下 */
    HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_SET);
    gpio.Pin = LED_Pin;
    gpio.Mode = GPIO_MODE_OUTPUT_PP;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_GPIO_Port, &gpio);

    /* 编码器按键 + 备用按键：上拉输入，低有效 */
    gpio.Pin = ENC_SW_Pin | BTN_Pin;
    gpio.Mode = GPIO_MODE_INPUT;
    gpio.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOB, &gpio);

    /* 编码器 A/B：上拉输入（后续由 TIM3 编码器模式接管） */
    gpio.Pin = ENC_A_Pin | ENC_B_Pin;
    gpio.Mode = GPIO_MODE_INPUT;
    gpio.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &gpio);
}

/**
 * @brief UART1：PA9=TX（复用推挽）、PA10=RX（上拉输入），115200 8N1
 */
static void UART1_Init(void)
{
    GPIO_InitTypeDef gpio = {0};

    __HAL_RCC_USART1_CLK_ENABLE();

    gpio.Pin = GPIO_PIN_9;
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &gpio);

    gpio.Pin = GPIO_PIN_10;
    gpio.Mode = GPIO_MODE_INPUT;
    gpio.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &gpio);

    g_uart1.Instance = USART1;
    g_uart1.Init.BaudRate = 115200;
    g_uart1.Init.WordLength = UART_WORDLENGTH_8B;
    g_uart1.Init.StopBits = UART_STOPBITS_1;
    g_uart1.Init.Parity = UART_PARITY_NONE;
    g_uart1.Init.Mode = UART_MODE_TX_RX;
    g_uart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    g_uart1.Init.OverSampling = UART_OVERSAMPLING_16;
    if (HAL_UART_Init(&g_uart1) != HAL_OK) {
        Error_Handler();
    }
}

/** @brief 极简日志：阻塞发送，够用即可；后续可换成环形缓冲 + DMA */
static void log_printf(const char *fmt, ...)
{
    char buf[128];
    va_list ap;

    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);

    HAL_UART_Transmit(&g_uart1, (uint8_t *)buf, (uint16_t)strlen(buf), 100);
}

/** @brief 不可恢复错误：关中断并停在 LED 全亮，便于现场判断 */
void Error_Handler(void)
{
    __disable_irq();
    HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_RESET);
    while (1) {
    }
}
