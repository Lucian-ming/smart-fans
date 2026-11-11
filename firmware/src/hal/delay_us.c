/**
 * @file delay_us.c
 * @brief Cycle-accurate microsecond delay using Cortex-M3 DWT CYCCNT
 */
#include "delay_us.h"

void delay_us_init(void)
{
    /* Enable TRC in DEMCR */
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
    /* Reset and enable DWT cycle counter */
    DWT->CYCCNT = 0;
    DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
}

void delay_us(uint32_t us)
{
    if (us == 0) return;
    const uint32_t ticks_per_us = SystemCoreClock / 1000000U;
    const uint32_t target_ticks = us * ticks_per_us;
    const uint32_t start_tick = DWT->CYCCNT;
    while ((DWT->CYCCNT - start_tick) < target_ticks) {
        __NOP();
    }
}
