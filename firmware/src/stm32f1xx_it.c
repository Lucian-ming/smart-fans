/**
 * @file stm32f1xx_it.c
 * @brief 最小中断向量实现
 *
 * HAL_Delay / HAL_GetTick 依赖 SysTick 中断调用 HAL_IncTick()。
 * 后续接入定时器捕获、串口 DMA 时，对应的 IRQHandler 也加在这里。
 */
#include "stm32f1xx_hal.h"

void SysTick_Handler(void)
{
    HAL_IncTick();
}
