#ifndef _led_H
#define _led_H

#include "system.h"

#define LED1 PBout(12)
#define LED2 PBout(13)


void LED1_Show(uint16_t shic,uint16_t time);  //LED1闪烁（时间基准，间隔）
void LED2_Show(uint16_t shic,uint16_t time);  //LED2闪烁（时间基准，间隔）

#endif
