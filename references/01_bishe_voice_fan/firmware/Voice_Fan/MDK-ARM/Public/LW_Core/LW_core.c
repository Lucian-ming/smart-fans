#include "LW_core.h"
#include <stdarg.h>		  //  标准头文件


extern UART_HandleTypeDef huart1;
extern UART_HandleTypeDef huart3;

void LW_Delay_US(int z)
{
   int x;
	 for(;z>0;z--)
	   for(x=10;x>0;x--);
}


//   格式化可变变量字符串缓存
char  formatBuf[64];
//   格式化可变变量字符串
char *LW_Format(char *p,...)
{
    va_list ap;
		va_start(ap,p);
		vsprintf(formatBuf,p,ap);
		va_end(ap);
	  return formatBuf;
}


/********************************************************************************
	*方法名称： WS_GT21_Print_7X8_Code
	*功能：     从芯片读取ASCII码7X8点阵信息，通过串口格式化打印
  *参数：     wait :   等待发送时间，单位MS , 数据采用DMA传输，
                       需要等待发送完成，则写入等待时间
	*						
	*返回：			无
*********************************************************************************/

void LW_Debug(char *p,...)
{
	  /*  格式化数据  */
    va_list ap;
		va_start(ap,p);
		vsprintf(formatBuf,p,ap);
		va_end(ap);	
	
//  编译控制	
#ifdef DEBUG_EN    
	  //  信息输出接口
	  HAL_UART_Transmit_DMA(&huart1,(uint8_t *)formatBuf,strlen(formatBuf));
	  	
#endif	 
}

/**************************************************
  * 函数功能: 重定向c库函数printf到DEBUG_USARTx
  * 输入参数: 无
  * 返 回 值: 无
  * 说    明：无
  ************************************************/
int fputc(int ch, FILE *f)
{
	while((USART1->SR&0X40)==0);//循环发送,直到发送完毕
	USART1->DR = (uint8_t)ch;

//  HAL_UART_Transmit(&huart1, (uint8_t *)&ch, 1, 0xffff);
  return ch;
}
 
/******************************************************
  * 函数功能: 重定向c库函数getchar,scanf到DEBUG_USARTx
  * 输入参数: 无
  * 返 回 值: 无
  * 说    明：无
  *****************************************************/
int fgetc(FILE *f)
{
  uint8_t ch = 0;
  HAL_UART_Receive(&huart1, &ch, 1, 0xffff);
  return ch;
}


int FindLastCharIndex(const char* str, char ch,const char* arr[], int size) //检测字符串是否匹配
{
    for (int i = 0; i < size; i++) {
        int len = strlen(arr[i]);
        if (arr[i][len - 1] == ch && strcmp(str, arr[i]) == 0) {
            return i; // 返回最后一个字符匹配的字符串的索引
        }
    }
    return -1; // 如果最后一个字符不存在于数组中的任何字符串，或者字符串不匹配，则返回-1
}

int FindNumberInString(char* str) //检测字符串是否有数字并求和
{
	int num=0,j=0;
    for (int i = strlen(str);i>=0; i--) {
        if (isdigit(str[i])) 
				{
          num += (str[i] - '0')*pow(10,j);
					j++;
        }
    }
		if(num) return num;//存在数字，并返回之和
    else return -1;//不存在返回-1
}


int filter(int ad) //递推平均滤波法
{ 
	char count; 
	int  sum=0,value_buf[12],i=0;;
	value_buf[i++] = ad;
	
	if ( i == 12 )    i = 0;
	for ( count=0;count<12;count++)
	sum += value_buf[count];
	return sum/12;
}

