/**
 * @file matrix_test_main.c
 * @brief STM32F103C8T6 专用双 8x8 MAX7219 点阵屏硬件检测固件
 *
 * 接线说明 (STM32 -> 点阵屏输入端):
 *   VCC  -> STM32 5V (或 3.3V)
 *   GND  -> STM32 GND
 *   CS   -> STM32 PB1  (LOAD)
 *   CLK  -> STM32 PB10 (时钟)
 *   DIN  -> STM32 PB11 (数据)
 *
 * 级联接线 (点阵1 -> 点阵2):
 *   点阵1 DOUT -> 点阵2 DIN
 *   点阵1 CLK  -> 点阵2 CLK
 *   点阵1 CS   -> 点阵2 CS
 *   点阵1 VCC  -> 点阵2 VCC
 *   点阵1 GND  -> 点阵2 GND
 *
 * 调试输出:
 *   USART1 (PA9 TX, 115200 8-N-1) 打印当前测试步骤
 *   PC13 板载心跳 LED 闪烁指示固件正常运行
 */
#include <stdio.h>
#include <stdarg.h>
#include <string.h>

#include "stm32f1xx_hal.h"
#include "config/pins.h"
#include "hal/delay_us.h"
#include "drivers/max7219.h"

UART_HandleTypeDef g_uart1;

/* 供 SysTick 中断调用，测试程序无需按键消抖 */
void button_poll(void)
{
}


/* ---- 调试串口 (USART1 PA9 TX @ 115200) ---- */
static void UART1_Init(void)
{
    __HAL_RCC_USART1_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    GPIO_InitTypeDef gpio = {0};
    gpio.Pin = GPIO_PIN_9; /* TX */
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &gpio);

    gpio.Pin = GPIO_PIN_10; /* RX */
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
    HAL_UART_Init(&g_uart1);
}

static void log_msg(const char *fmt, ...)
{
    char buf[256];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);
    HAL_UART_Transmit(&g_uart1, (uint8_t *)buf, (uint16_t)strlen(buf), 200);
}

/* ---- 系统时钟 (72MHz HSE 外部晶振) ---- */
static void SystemClock_Config(void)
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};

    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState = RCC_HSE_ON;
    osc.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
    osc.HSIState = RCC_HSI_ON;
    osc.PLL.PLLState = RCC_PLL_ON;
    osc.PLL.PLLSource = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLMUL = RCC_PLL_MUL9; /* 8MHz * 9 = 72MHz */
    if (HAL_RCC_OscConfig(&osc) != HAL_OK) {
        /* 若无外部8M晶振，自动回退到内部8M HSI倍频 64MHz */
        osc.OscillatorType = RCC_OSCILLATORTYPE_HSI;
        osc.HSEState = RCC_HSE_OFF;
        osc.PLL.PLLSource = RCC_PLLSOURCE_HSI_DIV2;
        osc.PLL.PLLMUL = RCC_PLL_MUL16;
        HAL_RCC_OscConfig(&osc);
    }

    clk.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                    RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV2;
    clk.APB2CLKDivider = RCC_HCLK_DIV1;
    HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2);
}

/* ---- PC13 板载指示灯 ---- */
static void LED_Init(void)
{
    __HAL_RCC_GPIOC_CLK_ENABLE();
    GPIO_InitTypeDef gpio = {0};
    gpio.Pin = GPIO_PIN_13;
    gpio.Mode = GPIO_MODE_OUTPUT_PP;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOC, &gpio);
    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_SET); /* 熄灭 */
}

/* ---- 测试图形字模 ---- */
static const uint8_t s_all_on[8]   = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
static const uint8_t s_all_off[8]  = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};

/* 数字 1 与 2 (用于单独验证各模块位置) */
static const uint8_t s_num_1[8] = {
    0x18, // . . . 1 1 . . .
    0x38, // . . 1 1 1 . . .
    0x18, // . . . 1 1 . . .
    0x18, // . . . 1 1 . . .
    0x18, // . . . 1 1 . . .
    0x18, // . . . 1 1 . . .
    0x18, // . . . 1 1 . . .
    0x7E  // . 1 1 1 1 1 1 .
};

static const uint8_t s_num_2[8] = {
    0x3C, // . . 1 1 1 1 . .
    0x66, // . 1 1 . . 1 1 .
    0x06, // . . . . . 1 1 .
    0x0C, // . . . . 1 1 . .
    0x18, // . . . 1 1 . . .
    0x30, // . . 1 1 . . . .
    0x60, // . 1 1 . . . . .
    0x7E  // . 1 1 1 1 1 1 .
};

/* 棋盘格交替花纹 (用于检测相邻引脚与焊点短路) */
static const uint8_t s_check_a[8] = {
    0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55
};
static const uint8_t s_check_b[8] = {
    0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA
};

/* 萌宠大眼 */
static const uint8_t s_eye_normal[8] = {
    0x3C, 0x7E, 0xE7, 0xC3, 0xC3, 0xE7, 0x7E, 0x3C
};

/* 欢喜笑眼 ^^ */
static const uint8_t s_eye_happy[8] = {
    0x00, 0x3C, 0x7E, 0xE7, 0xC3, 0x81, 0x00, 0x00
};

/* 爱心萌眼 <3 */
static const uint8_t s_eye_heart[8] = {
    0x00, 0x66, 0xFF, 0xFF, 0x7E, 0x3C, 0x18, 0x00
};

/* 闭眼/眨眼 */
static const uint8_t s_eye_closed[8] = {
    0x00, 0x00, 0x00, 0x7E, 0x7E, 0x00, 0x00, 0x00
};

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    LED_Init();
    UART1_Init();
    delay_us_init();

    log_msg("\r\n======================================================\r\n");
    log_msg("  STM32F103 MAX7219 Dual 8x8 Dot Matrix Hardware Test\r\n");
    log_msg("  Pinout:\r\n");
    log_msg("    PB1  -> CS  (LOAD)\r\n");
    log_msg("    PB10 -> CLK (SPI Clock)\r\n");
    log_msg("    PB11 -> DIN (Serial Data)\r\n");
    log_msg("    5V   -> VCC (or 3.3V)\r\n");
    log_msg("    GND  -> GND\r\n");
    log_msg("  Cascade Connection:\r\n");
    log_msg("    Module 1 DOUT -> Module 2 DIN\r\n");
    log_msg("    Module 1 CLK  -> Module 2 CLK\r\n");
    log_msg("    Module 1 CS   -> Module 2 CS\r\n");
    log_msg("======================================================\r\n\r\n");

    /* 初始化 MAX7219 驱动 */
    log_msg("[INIT] Initializing MAX7219 GPIOs (PB1, PB10, PB11)... ");
    max7219_init();
    log_msg("OK\r\n");

    uint32_t round = 1;

    while (1) {
        log_msg("------------------------------------------------------\r\n");
        log_msg(">>> Starting Test Cycle Round #%lu <<<\r\n", (unsigned long)round++);

        /* -----------------------------------------------------------------
         * 阶段 1: 硬件全亮自检模式 (Display Test)
         * 强制点亮全部 64+64=128 颗 LED，直接判断芯片供电与通信是否正常
         * ----------------------------------------------------------------- */
        log_msg("[TEST 1/5] Display Test: ALL 128 LEDs must be ON (2.5 sec)...\r\n");
        HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET); /* 点亮 PC13 LED */
        max7219_set_display_test(true);
        HAL_Delay(2500);
        max7219_set_display_test(false);
        max7219_clear();
        HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_SET);
        HAL_Delay(300);

        /* -----------------------------------------------------------------
         * 阶段 2: 独立点阵定位测试 (先测模块1，再测模块2)
         * ----------------------------------------------------------------- */
        log_msg("[TEST 2/5] Module 1 (Left) shows '1', Module 2 is OFF (1.5 sec)...\r\n");
        max7219_render_dual(s_num_1, s_all_off);
        HAL_Delay(1500);

        log_msg("[TEST 2/5] Module 2 (Right) shows '2', Module 1 is OFF (1.5 sec)...\r\n");
        max7219_render_dual(s_all_off, s_num_2);
        HAL_Delay(1500);

        /* -----------------------------------------------------------------
         * 阶段 3: 棋盘格交替闪烁 (排查相邻引脚短路或虚焊)
         * ----------------------------------------------------------------- */
        log_msg("[TEST 3/5] Checkerboard Pattern Alternation (2 sec)...\r\n");
        for (int i = 0; i < 4; i++) {
            max7219_render_dual(s_check_a, s_check_b);
            HAL_Delay(300);
            max7219_render_dual(s_check_b, s_check_a);
            HAL_Delay(300);
        }

        /* -----------------------------------------------------------------
         * 阶段 4: 双眼表情动画测试 (大眼、眨眼、欢喜笑眼、爱心眼)
         * ----------------------------------------------------------------- */
        log_msg("[TEST 4/5] Facial Emotion Animation Demo...\r\n");

        /* 4.1 常态大眼 */
        log_msg("  - Normal Eyes (1.5s)\r\n");
        max7219_render_dual(s_eye_normal, s_eye_normal);
        HAL_Delay(1500);

        /* 4.2 眨眼动作 */
        log_msg("  - Blink Eyes\r\n");
        max7219_render_dual(s_eye_closed, s_eye_closed);
        HAL_Delay(180);
        max7219_render_dual(s_eye_normal, s_eye_normal);
        HAL_Delay(1000);

        /* 4.3 欢喜笑眼 ^^ */
        log_msg("  - Happy Smile (1.5s)\r\n");
        max7219_render_dual(s_eye_happy, s_eye_happy);
        HAL_Delay(1500);

        /* 4.4 爱心萌眼 <3 */
        log_msg("  - Love Hearts (1.5s)\r\n");
        max7219_render_dual(s_eye_heart, s_eye_heart);
        HAL_Delay(1500);

        /* -----------------------------------------------------------------
         * 阶段 5: 逐级亮度测试 (0 极暗 -> 15 极亮)
         * ----------------------------------------------------------------- */
        log_msg("[TEST 5/5] Intensity Sweep Test (Low to High)...\r\n");
        max7219_render_dual(s_eye_normal, s_eye_normal);
        for (uint8_t br = 0; br <= 15; br += 3) {
            max7219_set_intensity(br);
            HAL_Delay(200);
        }
        max7219_set_intensity(8); /* 恢复默认亮度 8 */

        max7219_clear();
        HAL_Delay(500);
    }
}

void Error_Handler(void)
{
    while (1) {
        HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
        HAL_Delay(100);
    }
}
