#include "Systick.h"
//#include "usart.h"
uint8_t SYSClockFreq=0;//时钟频率MHz

/*******************************************************************************
* 函 数 名         : My_delay_us
* 函数功能		     : us级延时，
* 输    入         : us：要延时的us数
					          注意:us:0~190887435(最大值即 2^32/fac_us@fac_us=22.5)
* 输    出         : 无
*******************************************************************************/
void My_delay_us(uint32_t us)
{
 uint32_t ticks;
 uint32_t told,tnow,tcnt=0;
 uint32_t reload=SysTick->LOAD; //LOAD 的值

 
 if(!SYSClockFreq)
 {
	 SYSClockFreq = HAL_RCC_GetSysClockFreq()/1000000;  //获取系统时钟频率
//	 printf("被调用了");
 }
 ticks=us*SYSClockFreq; //需要的节拍数
 told=SysTick->VAL; //刚进入时的计数器值
 while(1)
 {
	 tnow=SysTick->VAL;
	 if(tnow!=told)
	 {
		 if(tnow<told)tcnt+=told-tnow; //这里注意一下 SYSTICK 是一个递减的计数器就可以
		 else tcnt+=reload-tnow+told;
		 told=tnow;
		 if(tcnt>=ticks)break; //时间超过/等于要延迟的时间,则退出.
	 }
 }
}

/*******************************************************************************
* 函 数 名         : My_delay_ms
* 函数功能		     : ms级延时，
* 输    入         : ms：要延时的ms数 0~65535
* 输    出         : 无
*******************************************************************************/
void My_delay_ms(uint16_t ms)
{
 uint32_t i;
 for(i=0;i<ms;i++) My_delay_us(1000);
}



