#ifndef _NTC_H
#define _NTC_H
#include "system.h"

#define T25 298.15    //电压转温度的公式的采用
#define R25 10       //参考电阻10k
#define B	3590        //B值是热敏电阻的重要参数

#define Rp 10           //100k
#define T2 (273.15+25.0)  //T1和T2指的是K度
#define Bx 3590.0        //B值是热敏电阻的重要参数
#define Ka 298.15         //常数

extern float Volta;
extern float Temperture;
extern float Rntc;

void Get_Kelvin_Temperature(u16 t);  //方法一
void Get_Temperature(u16 ADC_Value); //方法二

u8 Lsens_Get_Val(u32 ADC_Val); //光敏电阻亮度计算


#endif

