#ifndef _Systick_H
#define _Systick_H
#include "system.h"

extern uint8_t SYSClockFreq;//时钟频率MHz

void My_delay_us(uint32_t us);  //us级延时
void My_delay_ms(uint16_t ms);  //ms级延时




#endif
