/**
  ******************************************************************************
  * @file    rtc.h
  * @brief   This file contains all the function prototypes for
  *          the rtc.c file
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
/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __RTC_H__
#define __RTC_H__

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

extern RTC_HandleTypeDef hrtc;

/* USER CODE BEGIN Private defines */

typedef struct 
{
	__IO uint8_t hour;
	__IO uint8_t min;
	__IO uint8_t sec;			
	//公历日月年周
	__IO uint16_t w_year;
	__IO uint8_t  w_month;
	__IO uint8_t  w_date;
	__IO uint8_t  week;	
}_calendar_obj;	
extern _calendar_obj calendar;				//日历结构体


/* USER CODE END Private defines */

void MX_RTC_Init(void);

/* USER CODE BEGIN Prototypes */


void rtc_init_user(void);
void RTC_Set(uint16_t syear,uint8_t smon,uint8_t sday,uint8_t hour,uint8_t min,uint8_t sec);
void RTC_Get(void);
uint8_t Is_Leap_Year(uint16_t year);
uint8_t RTC_Get_Week(uint16_t year,uint8_t month,uint8_t day);


/* USER CODE END Prototypes */

#ifdef __cplusplus
}
#endif

#endif /* __RTC_H__ */

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
