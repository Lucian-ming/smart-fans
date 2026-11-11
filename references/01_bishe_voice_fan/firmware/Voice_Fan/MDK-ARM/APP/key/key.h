#ifndef _key_H
#define _key_H

#include "Systick.h"
#include "led.h"

//使用位操作定义
#define KEY1 	 PAin(0)
#define KEY2 	 PAin(1)
#define KEY3 	 PAin(2)


//定义各个按键值  
#define KEY1_PRESS 	  1
#define KEY2_PRESS		2
#define KEY3_PRESS		3


uint8_t KEY_Scan(uint8_t mode);


#endif
