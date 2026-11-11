#include "led.h"


void LED1_Show(uint16_t shic,uint16_t time)  //LED1闪烁（时间基准，间隔）
{
	if(shic%time == 0) LED1 = ~LED1;
}

void LED2_Show(uint16_t shic,uint16_t time)  //LED2闪烁（时间基准，间隔）
{
	if(shic%time == 0) LED2 = ~LED2;
}


