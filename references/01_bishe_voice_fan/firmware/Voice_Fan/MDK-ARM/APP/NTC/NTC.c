#include "NTC.h"
#include "math.h"

float Volta=0.0;
float Temperture=0.0;
float Rntc=0.0;

//模拟量转电阻
float temp_Get_R(u16 adct)
{
	//单片机3.3v 供电 ==》 3v，先求出电压
	float v1 = (float)(adct*3.3)/4096;//ntc上的电压
	float v2 = 3.3f - v1;
	Volta  = v1;//ntc上的电压给方法二全局变量
	Rntc = (v1/v2)*10;
	return Rntc;
}
////实现ln(x) 的计算
//double myln(double a)
//{
//   int N = 15;//取了前15+1项来估算
//   int k,nk;
//   double x,xx,y;
//   x = (a-1)/(a+1);
//   xx = x*x;
//   nk = 2*N+1;
//   y = 1.0/nk;
//   for(k=N;k>0;k--)
//   {
//     nk = nk - 2;
//     y = 1.0/nk+xx*y;
//     
//   }
//   return 2.0*x*y;
//}
 
void Get_Kelvin_Temperature(u16 t)
{
	float N1,N2,N3;
	float Rntc = temp_Get_R(t);
	N1 = (log(R25)-log(Rntc))/B;
	N2 = 1/T25 - N1;
	N3 = 1/N2;
	Temperture = N3-273.15f;//开尔文转摄氏度

}



/*NTC 热敏电阻温度计算公式：Rt = R *EXP(B*(1/T1-1/T2))

其中，T1和T2指的是K度，即开尔文温度。

Rt 是热敏电阻在T1温度下的阻值。

R是热敏电阻在T2常温下的标称阻值。100K的热敏电阻25℃的值为100K（即R=100K）。T2=(273.15+25)

EXP是e的n次方

B值是热敏电阻的重要参数

通过转换可以得到温度T1与电阻Rt的关系T1=1/（ln（Rt/R）/B+1/T2）

对应的摄氏温度t=T1-273.15，同时+0.5的误差矫正。*/

void Get_Temperature(u16 ADC_Value)
{
	Volta = (float) ADC_Value/4095*3.3f;
	Rntc = (10*Volta/(3.3f-Volta));
	Temperture = (1/(log(Rntc/Rp)/Bx + (1/T2)))-273.15+0.5;
}


#define LSENS_READ_TIMES	10	//定义光敏传感器读取次数,读这么多次,然后取平均值

//读取Light Sens的值
//0~100:0,最暗;100,最亮 
u8 Lsens_Get_Val(u32 ADC_Val) //光敏电阻亮度计算
{
	u32 temp_val=0;
	u8 t;
	for(t=0;t<LSENS_READ_TIMES;t++)
	{
		temp_val+=ADC_Val;	//读取ADC值
		HAL_Delay(1);
	}
	temp_val/=LSENS_READ_TIMES;//得到平均值 
	if(temp_val>4000)temp_val=4000;
	return (u8)(100-(temp_val/40));
}




