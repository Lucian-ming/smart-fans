/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * <h2><center>&copy; Copyright (c) 2023 STMicroelectronics.
  * All rights reserved.</center></h2>
  *
  * This software component is licensed by ST under BSD 3-Clause license,
  * the "License"; You may not use this file except in compliance with the
  * License. You may obtain a copy of the License at:
  *                        opensource.org/licenses/BSD-3-Clause
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "adc.h"
#include "dma.h"
#include "i2c.h"
#include "rtc.h"
#include "tim.h"
#include "usart.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include "oled.h"
#include "NTC2Fen.h"
#include "LW_core.h"
#include "led.h"
#include "key.h"

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
char show_buff[32];
uint16_t T1_COUNT=0,ADC1_Array[2],Temp_Newmax=0,FAN_Speed=0,Light_Hd=0;
float Volt_Newmax=0,Volt_Oldmax=0;
uint8_t UART1_Reflag,UART3_Reflag,Uart1_Rxbuff[128],Uart3_Rxbuff[128];
uint16_t UART1_Len=0,UART3_Len=0;
unsigned char x=0;
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */
RTC_DateTypeDef sdatestructure;
RTC_TimeTypeDef stimestructure;



/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */
	char* endptr,mode_flag;
	uint8_t KEY_flag=0;

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_ADC1_Init();
  MX_TIM1_Init();
  MX_USART1_UART_Init();
  MX_I2C1_Init();
  MX_USART3_UART_Init();
  MX_RTC_Init();
  /* USER CODE BEGIN 2 */
	HAL_TIM_Base_Start_IT(&htim1);
	HAL_ADC_Start_DMA(&hadc1,(uint32_t*)ADC1_Array,2);  //开始DMA ADC采集
	HAL_TIM_PWM_Start(&htim1,TIM_CHANNEL_1);
	HAL_TIM_PWM_Start(&htim1,TIM_CHANNEL_2);
  __HAL_UART_ENABLE_IT(&huart1,UART_IT_IDLE);//使能空闲中断
	HAL_UART_Receive_DMA(&huart1,Uart1_Rxbuff,sizeof(Uart1_Rxbuff)-1);//开启DMA接收
	__HAL_UART_ENABLE_IT(&huart3,UART_IT_IDLE);//使能空闲中断
	HAL_UART_Receive_DMA(&huart3,Uart3_Rxbuff,sizeof(Uart3_Rxbuff)-1);//开启DMA接收
	OLED_Init();
	FAN_Speed=20;
	Light_Hd=20;
	One_Page();
	HAL_Delay(500);
	OLED_Clear();
	OLED_ShowString(0,0,(uint8_t*)"   Voice_FAN",16);
	
	/*测备份寄存器是否还存着这个值，存在立即退出RTC初始化，不存在进行RTC初始化(M4内核已解决日期无法保存问题)*/
	if(HAL_RTCEx_BKUPRead(&hrtc,RTC_BKP_DR1) != 0X9607)
	{
		RTC_Set(2023,10,17,11,52,40); //设置日期和时间
		HAL_RTCEx_BKUPWrite(&hrtc,RTC_BKP_DR1,0X9607);//向16位备份寄存器随便写入一个数据
	}
	else printf("RTC Storage OK!");
	RTC_Get();
  printf("%04d/%02d/%02d ",calendar.w_year, calendar.w_month, calendar.w_date);
  printf("%02d:%02d:%02d",calendar.hour, calendar.min, calendar.sec);
	printf("The Crystal Oscillator:%dMHZ\r\n",HAL_RCC_GetSysClockFreq()/1000000);
	

 
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
		LED2 = !LED2;
		if(UART1_Reflag)  //蓝牙数据处理
		{
			if(strstr((char*)Uart1_Rxbuff,(char*)"FAN"))
			{
				if(FindNumberInString((char*)Uart1_Rxbuff) <= 5) FAN_Speed=0;
				else FAN_Speed = FindNumberInString((char*)Uart1_Rxbuff);
			}
			else if(strstr((char*)Uart1_Rxbuff,(char*)"LIGHT"))
			{
				if(FindNumberInString((char*)Uart1_Rxbuff) <= 5) Light_Hd=0;
				else  Light_Hd = FindNumberInString((char*)Uart1_Rxbuff);
			}
			else if(strstr((char*)Uart1_Rxbuff,(char*)"RETIME"))
			{
				
			}
			UART1_Reflag=0;	
			UART1_Len=0;
			memset(Uart1_Rxbuff,0x00,sizeof(Uart1_Rxbuff)); //清空数组
			HAL_UART_Receive_DMA(&huart1,Uart1_Rxbuff,sizeof(Uart1_Rxbuff)-1);
		}
		
		
		if(UART3_Reflag)  //语音数据处理
		{
			if(!strcmp((char*)"FON\r\n",(char*)Uart3_Rxbuff)) 
			{
    		HAL_UART_Transmit_DMA(&huart3,(uint8_t*)"Fyes",8);
				FAN_Speed=20;
			}				
			else if(!strcmp((char*)"F+\r\n",(char*)Uart3_Rxbuff)) FAN_Speed=(FAN_Speed+10)%100;
			else if(!strcmp((char*)"F-\r\n",(char*)Uart3_Rxbuff))
			{
				if(FAN_Speed<=0) FAN_Speed=99;
				else FAN_Speed -= 10;
			}
			else if(!strcmp((char*)"FMAX\r\n",(char*)Uart3_Rxbuff)) FAN_Speed=99;
			else if(!strcmp((char*)"FMOD\r\n",(char*)Uart3_Rxbuff)) FAN_Speed=50;
			else if(!strcmp((char*)"FMIN\r\n",(char*)Uart3_Rxbuff)) FAN_Speed=10;
			else if(!strcmp((char*)"FOFF\r\n",(char*)Uart3_Rxbuff)) 
			{
				HAL_UART_Transmit_DMA(&huart3,(uint8_t*)"Foff",8);
				FAN_Speed=0;
			}
			
			if(!strcmp((char*)"LON\r\n",(char*)Uart3_Rxbuff)) 
			{
				HAL_UART_Transmit_DMA(&huart3,(uint8_t*)"Lyes",8);
				Light_Hd=20;         
			}				
			else if(!strcmp((char*)"L+\r\n",(char*)Uart3_Rxbuff)) Light_Hd=(Light_Hd+10)%100;
			else if(!strcmp((char*)"L-\r\n",(char*)Uart3_Rxbuff))
			{
				Light_Hd -= 10;
				if(Light_Hd<=0) Light_Hd=99;   
			}
			else if(!strcmp((char*)"LMAX\r\n",(char*)Uart3_Rxbuff)) Light_Hd=99;
			else if(!strcmp((char*)"LMOD\r\n",(char*)Uart3_Rxbuff)) Light_Hd=50;
			else if(!strcmp((char*)"LMIN\r\n",(char*)Uart3_Rxbuff)) Light_Hd=10;
			else if(!strcmp((char*)"LOFF\r\n",(char*)Uart3_Rxbuff)) 
			{
				HAL_UART_Transmit_DMA(&huart3,(uint8_t*)"Loff",8);
				Light_Hd=0;
			}
			HAL_UART_Transmit_DMA(&huart3,Uart3_Rxbuff,UART3_Len);
			UART3_Reflag=0;	
			UART3_Len=0;
			memset(Uart3_Rxbuff,0x00,sizeof(Uart3_Rxbuff)); //清空数组
			HAL_UART_Receive_DMA(&huart3,Uart3_Rxbuff,sizeof(Uart3_Rxbuff)-1);
		}
		
		
		
		KEY_flag = KEY_Scan(1);//按键处理
		if(KEY_flag == KEY1_PRESS)
		{
			mode_flag = (mode_flag+1)%2;
		}
		switch(mode_flag)
		{
			case 0:
			{
				if(KEY_flag == KEY2_PRESS) 
				{
					FAN_Speed=(FAN_Speed+5)%100;
				}
				if(KEY_flag == KEY3_PRESS)
				{
					if(FAN_Speed-- <=0) FAN_Speed=99;
				}
				break;
			}
			case 1:
			{
				if(KEY_flag == KEY2_PRESS) 
				{
					Light_Hd=(Light_Hd+5)%100;
				}
				if(KEY_flag == KEY3_PRESS)
				{
					if(Light_Hd-- <=0) Light_Hd=99;
				}
				break;
			}
		}
		
		TIM1->CCR1=FAN_Speed; TIM1->CCR2=Light_Hd;//风扇、灯光调节
		
		
		if(T1_COUNT%1000==0)  //外部供电电压检测
		{
			Volt_Newmax = ADC1_Array[0]*3.3f/4096*10+1.6;
			if(Volt_Newmax > Volt_Oldmax) 
			{
				printf("voltage%01.2f\r\n",Volt_Newmax);
				Volt_Oldmax=Volt_Newmax;
			}
		}
		else if(T1_COUNT%100==0)//屏幕刷新
		{
			sprintf(show_buff,"Fan_speed:%03d%%  ",FAN_Speed);
			OLED_ShowString(1,2,(uint8_t*)show_buff,16);
			sprintf(show_buff,"Light_HD:%03d%%   ",Light_Hd);
			OLED_ShowString(1,4,(uint8_t*)show_buff,16);
			if(!mode_flag) OLED_ShowChar(122,2,'<',16);
			else OLED_ShowChar(122,4,'<',16);
			
			for(x=0;x<10;x++)//测温
			{
				Temp_Newmax = (Temp_Newmax+tempDetect(ADC1_Array[1]*3.3f/4096));
			}
			Temp_Newmax =(Temp_Newmax/10)-10;
			printf("temp%02d\r\n ",Temp_Newmax);
			
			HAL_RTC_GetTime(&hrtc, &stimestructure, RTC_FORMAT_BIN);
      HAL_RTC_GetDate(&hrtc, &sdatestructure, RTC_FORMAT_BIN);
			sprintf(show_buff,"    %02d:%02d:%02d",stimestructure.Hours, stimestructure.Minutes, stimestructure.Seconds);
			OLED_ShowString(1,6,(uint8_t*)show_buff,16);
		}
	
		
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};
  RCC_PeriphCLKInitTypeDef PeriphClkInit = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE|RCC_OSCILLATORTYPE_LSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.LSEState = RCC_LSE_ON;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }
  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
  PeriphClkInit.PeriphClockSelection = RCC_PERIPHCLK_RTC|RCC_PERIPHCLK_ADC;
  PeriphClkInit.RTCClockSelection = RCC_RTCCLKSOURCE_LSE;
  PeriphClkInit.AdcClockSelection = RCC_ADCPCLK2_DIV6;
  if (HAL_RCCEx_PeriphCLKConfig(&PeriphClkInit) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */
//定时器回调函数，1ms中断一次 
/************************************************************************************************
//延时时间=预分频系数PCS-1 * 分频系数ARR-1 / 晶振频率MHZ 这里是72*100/72 000 000=0.0001s;
//PWM输出频率 = 晶振频率MHZ / (预分频系数PCS-1 * 分频系数ARR-1) 这里是72000000/72*100=10KHZ;
//占空比计算公式 ：占空比=想设的值 / 分配系数 * 100%  例如：40% = 40/100;
*************************************************************************************************/

void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)  //定时器更新中断回调函数
{
	if(htim->Instance == TIM1)  //判断TIM1是否发生中断
	{
		T1_COUNT = (T1_COUNT+1)%10001;
		if(T1_COUNT%1000==0) LED1=~LED1;	
	}
} 

//串口回调函数
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
	UNUSED(huart);
	if(huart ==&huart1)
	{
		UART1_Len = huart->RxXferSize-huart->hdmarx->Instance->CNDTR;
		UART1_Reflag=1;
	}
	if(huart ==&huart3)
	{
		UART3_Len = huart->RxXferSize-huart->hdmarx->Instance->CNDTR;
		UART3_Reflag=1;
	}
}

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
