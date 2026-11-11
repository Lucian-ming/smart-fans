/**
 * @file pins.h
 * @brief 引脚分配 —— 与 fan_ctrl_revB 硬件 PCB 保持严格同步 (Rev B4)
 *
 * 目标：STM32F103C8T6 最小系统核心板（蓝板插座形式，95x95mm 主板，85mm 孔距）
 */
#pragma once

#include "stm32f1xx_hal.h"

/* ---- 心跳 LED（蓝板 PC13，低电平点亮）---- */
#define LED_Pin          GPIO_PIN_13
#define LED_GPIO_Port    GPIOC

/* ---- 旋转编码器 EC11 (PA6/PA7 正交编码 + PB12 下按按键模式切换) ---- */
#define ENC_A_Pin        GPIO_PIN_6    /* PA6，TIM3_CH1，编码器 A 相 */
#define ENC_B_Pin        GPIO_PIN_7    /* PA7，TIM3_CH2，编码器 B 相 */
#define ENC_Port         GPIOA

#define ENC_SW_Pin       GPIO_PIN_12   /* PB12，旋钮下按按键：专职模式切换 (手动 / 自动温控) */
#define ENC_SW_Port      GPIOB

/* ---- 独立按键模块（大按键 2 键配置）---- */
#define KEY1_POWER_Pin   GPIO_PIN_13   /* PB13，独立按键 1：专职风扇电源启停 (ON/OFF) */
#define KEY1_POWER_Port  GPIOB

#define KEY2_SWING_Pin   GPIO_PIN_14   /* PB14，独立按键 2：专职摇摆头控制 (CW/CCW/STOP) */
#define KEY2_SWING_Port  GPIOB

/* ---- TB6612FNG 130直流电机驱动 ---- */
#define TB_PWMA_Pin      GPIO_PIN_0    /* PA0，TIM2_CH1 @ 25 kHz，电机转速 PWM */
#define TB_PWMA_Port     GPIOA

#define TB_AIN1_Pin      GPIO_PIN_1    /* PA1，电机转向控制 1 */
#define TB_AIN1_Port     GPIOA

#define TB_AIN2_Pin      GPIO_PIN_5    /* PA5，电机转向控制 2 */
#define TB_AIN2_Port     GPIOA

#define TB_STBY_Pin      GPIO_PIN_0    /* PB0，TB6612 使能控制（高电平工作，板载 10k 下拉） */
#define TB_STBY_Port     GPIOB

/* ---- DHT11 温湿度传感器 ---- */
#define DHT11_DATA_Pin   GPIO_PIN_9    /* PB9，单总线数据引脚（板载 4.7k 上拉到 3.3V） */
#define DHT11_DATA_Port  GPIOB

/* ---- MG90S 360° 左右扫风舵机 ---- */
#define SERVO_PWM_Pin    GPIO_PIN_8    /* PB8，TIM4_CH3 @ 50 Hz */
#define SERVO_PWM_Port   GPIOB

/* ---- OLED (0x3C) 与手势传感器 PAJ7620 (0x73)（I2C1 总线，板载双 4.7k 上拉）---- */
#define I2C1_SCL_Pin     GPIO_PIN_6    /* PB6 */
#define I2C1_SDA_Pin     GPIO_PIN_7    /* PB7 */
#define I2C1_Port        GPIOB

/* ---- PAJ7620 手势传感器中断 ---- */
#define GESTURE_INT_Pin  GPIO_PIN_4    /* PA4，EXTI4 下降沿中断 */
#define GESTURE_INT_Port GPIOA

/* ---- 有源蜂鸣器驱动 ---- */
#define BUZZER_Pin       GPIO_PIN_15   /* PB15，经 1k 限流驱动 2N3904 NPN 三极管 */
#define BUZZER_Port      GPIOB

/* ---- 调试串口（USART1）---- */
#define UART1_TX_Pin     GPIO_PIN_9    /* PA9 */
#define UART1_RX_Pin     GPIO_PIN_10   /* PA10 */
#define UART1_Port       GPIOA

/* ---- 语音模块（USART2，ASR-PRO 离线免唤醒交互）---- */
#define VOICE_TX_Pin     GPIO_PIN_2    /* PA2 → ASR-PRO RX */
#define VOICE_RX_Pin     GPIO_PIN_3    /* PA3 ← ASR-PRO TX */
#define VOICE_Port       GPIOA

/* ---- 8x8 MAX7219 点阵屏：引脚释放 (转接由 ASR-PRO 语音核心板直接级联驱动表情显示) ---- */
/* PB1, PB10, PB11 现已释放并留空 */

