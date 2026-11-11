/**
 * @file buzzer.c
 * @brief 有源蜂鸣器驱动实现
 */
#include "buzzer.h"
#include "stm32f1xx_hal.h"
#include "config/pins.h"

typedef struct {
    uint8_t remaining_beeps;
    uint16_t on_time_ms;
    uint16_t off_time_ms;
    uint32_t phase_start_ms;
    bool is_on;
} buzzer_pattern_t;

static buzzer_pattern_t g_buz_state = {0};

void buzzer_init(void)
{
    GPIO_InitTypeDef gpio = {0};

    __HAL_RCC_GPIOB_CLK_ENABLE();

    /* PCB NPN三极管驱动有源蜂鸣器：低电平关断，高电平导通鸣叫。
     * 初始化必须先输出低电平（静音），再配置为推挽输出，防止上电产生尖锐误鸣 */
    HAL_GPIO_WritePin(BUZZER_Port, BUZZER_Pin, GPIO_PIN_RESET);

    gpio.Pin = BUZZER_Pin;
    gpio.Mode = GPIO_MODE_OUTPUT_PP;
    gpio.Pull = GPIO_NOPULL;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(BUZZER_Port, &gpio);

    buzzer_set(false);
}

void buzzer_set(bool on)
{
    /* PCB NPN驱动：PB15 输出高电平导通2N3904驱动蜂鸣器，低电平截止静音 */
    HAL_GPIO_WritePin(BUZZER_Port, BUZZER_Pin, on ? GPIO_PIN_SET : GPIO_PIN_RESET);
    g_buz_state.is_on = on;
}

void buzzer_beep(uint16_t duration_ms)
{
    buzzer_beep_pattern(1, duration_ms, 0);
}

void buzzer_beep_pattern(uint8_t count, uint16_t on_ms, uint16_t off_ms)
{
    if (count == 0 || on_ms == 0) {
        buzzer_set(false);
        g_buz_state.remaining_beeps = 0;
        return;
    }

    g_buz_state.remaining_beeps = count;
    g_buz_state.on_time_ms = on_ms;
    g_buz_state.off_time_ms = off_ms;
    g_buz_state.phase_start_ms = HAL_GetTick();

    buzzer_set(true);
}

void buzzer_tick(uint32_t now_ms)
{
    if (g_buz_state.remaining_beeps == 0) {
        return;
    }

    const uint32_t elapsed = now_ms - g_buz_state.phase_start_ms;

    if (g_buz_state.is_on) {
        if (elapsed >= g_buz_state.on_time_ms) {
            buzzer_set(false);
            g_buz_state.remaining_beeps--;
            g_buz_state.phase_start_ms = now_ms;

            if (g_buz_state.remaining_beeps == 0) {
                /* Finished pattern */
            }
        }
    } else {
        if (elapsed >= g_buz_state.off_time_ms) {
            buzzer_set(true);
            g_buz_state.phase_start_ms = now_ms;
        }
    }
}
