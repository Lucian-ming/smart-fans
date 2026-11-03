/**
 * @file pins.h
 * @brief 引脚分配 —— 与 docs/hardware/pinmap.md 保持同步
 *
 * 目标：STM32F103C8T6（LQFP48）。换封装/改板时只改本文件与各驱动初始化。
 */
#pragma once

#include "stm32f1xx_hal.h"

/* ---- 心跳 LED（蓝板 PC13，低电平点亮）---- */
#define LED_Pin          GPIO_PIN_13
#define LED_GPIO_Port    GPIOC

/* ---- 按键 / 编码器 ---- */
#define BTN_Pin          GPIO_PIN_13   /* PB13，备用按键，低有效 */
#define BTN_GPIO_Port    GPIOB
#define ENC_SW_Pin       GPIO_PIN_12   /* PB12，编码器按键，低有效 */
#define ENC_SW_GPIO_Port GPIOB
#define ENC_A_Pin        GPIO_PIN_6    /* TIM3_CH1，编码器模式 */
#define ENC_B_Pin        GPIO_PIN_7    /* TIM3_CH2 */
#define ENC_GPIO_Port    GPIOA

/* ---- 风扇 ---- */
#define FAN_PWM_Pin      GPIO_PIN_0    /* TIM2_CH1 @ 25 kHz */
#define FAN_PWM_GPIO_Port GPIOA
#define FAN_TACH_Pin     GPIO_PIN_8    /* TIM1_CH1 输入捕获（4-pin 风扇 FG） */
#define FAN_TACH_GPIO_Port GPIOA

/* ---- 温度传感器 ---- */
#define TEMP_Pin         GPIO_PIN_1    /* DS18B20 单总线（4.7k 上拉到 3.3V） */
#define TEMP_GPIO_Port   GPIOA

/* ---- OLED（I2C1）---- */
#define OLED_SCL_Pin     GPIO_PIN_6    /* PB6 */
#define OLED_SDA_Pin     GPIO_PIN_7    /* PB7 */
#define OLED_GPIO_Port   GPIOB

/* ---- 蜂鸣器（经三极管/MOSFET 驱动，禁止直驱）---- */
#define BUZZER_Pin       GPIO_PIN_14   /* PB14 */
#define BUZZER_GPIO_Port GPIOB

/* ---- 调试串口（UART1）---- */
#define UART_TX_Pin      GPIO_PIN_9    /* PA9 */
#define UART_RX_Pin      GPIO_PIN_10   /* PA10 */

/* ---- 语音模块（USART2，SU-03T / ASR-PRO）---- */
#define VOICE_TX_Pin     GPIO_PIN_2    /* PA2 → 语音模块 RX */
#define VOICE_RX_Pin     GPIO_PIN_3    /* PA3 ← 语音模块 TX */
#define VOICE_GPIO_Port  GPIOA

/* ---- 手势传感器（PAJ7620U2，与 OLED 共用 I2C1）---- */
#define GESTURE_INT_Pin      GPIO_PIN_4   /* PA4，开漏中断输入 */
#define GESTURE_INT_GPIO_Port GPIOA

/* ---- 可选：12V 输入电压检测（分压到 ≤3.3V）---- */
#define VBAT_SENSE_Pin   GPIO_PIN_5    /* PA5 / ADC12_IN5 */
