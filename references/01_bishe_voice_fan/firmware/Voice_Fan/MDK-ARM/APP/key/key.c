#include "key.h"


/*******************************************************************************
* 函 数 名         : KEY_Scan
* 函数功能		   : 按键扫描检测
* 输    入         : mode=0:单次按下按键
					 mode=1：连续按下按键
* 输    出         : 0：未有按键按下
					           KEY1_PRESS：  KEY1键按下   1
					           KEY2_PRESS：  KEY2键按下   2
					           KEY3_PRESS：  KEY3键按下   3
*******************************************************************************/
uint8_t KEY_Scan(uint8_t mode)
{
	static uint8_t key=1;
	
	if(mode==1) //连续按键按下
		key=1;
	if(key==1&&(KEY1==0||KEY2==0||KEY3==0)) //任意一个按键按下
	{
		//HAL_Delay(10);  //消抖
		key=0;
		if(KEY1==0)
		{
			while(!KEY1);
			return KEY1_PRESS; 
		}
		else if(KEY2==0)
		{
			while(!KEY2);
			return KEY2_PRESS; 
		}
		else if(KEY3==0)
		{
			while(!KEY3);
			return KEY3_PRESS;
		}			
	}
	else if(KEY1==1 && KEY2==1 && KEY3==1) //无按键按下
	{	
		key=1;
	}
	return 0;
}






