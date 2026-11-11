#include "oled.h"
#include "bmp.h"
#include "adc.h"
#include "usart.h"



void One_Page(void)//首页显示湖南工业
{
	static char i=0;
	OLED_ShowString(4,0,(uint8_t*)"Hunan Industry",16);
	OLED_ShowString(2,2,(uint8_t*)"Chinese Changsha",16);
	for(i=0;i<4;i++) OLED_ShowCHinese(32+i*16,5,i+7);
}
