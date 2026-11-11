/*****************************
编写核心代码，尽量做到不依赖硬件



*****************************/


#ifndef __CORE_H__
#define __CORE_H__

#include "main.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include <math.h>

#define DEBUG_EN 1



//   格式化可变变量字符串
char *LW_Format(char *p,...);

//   调试输出
void LW_Debug( char *p,...);


void LW_Delay_US(int z);

int FindLastCharIndex(const char* str, char ch,const char* arr[], int size); //检测字符串是否匹配

int FindNumberInString(char* str); //检测字符串是否有数字并求和


int filter(int ad); //递推平均滤波法

#endif



