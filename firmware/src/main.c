/**
 * @file main.c
 * @brief 桌面智能风扇主固件入口 (STM32F103C8T6 + STM32Cube HAL)
 *
 * 硬件基准：fan_ctrl_revB 硬件 PCB 网络与面板接口
 * 安全策略：
 *   - 上电初期 STBY 保持低电平，直流电机与连续旋转舵机 PWM 占空比为 0
 *   - 蜂鸣器默认为关，各驱动统一汇入事件状态机，禁止驱动层直接抢写 PWM
 *   - 默认处于安全待机/测试模式，等待按键、语音、手势或串口 CLI 触发
 */
#include <stdarg.h>
#include <stdio.h>
#include <string.h>

#include "stm32f1xx_hal.h"
#include "config/pins.h"
#include "config/version.h"

#include "hal/delay_us.h"
#include "drivers/buzzer.h"
#include "drivers/button.h"
#include "drivers/motor.h"
#include "drivers/servo.h"
#include "drivers/encoder.h"
#include "drivers/i2c_bus.h"
#include "drivers/ssd1306.h"
#include "drivers/paj7620.h"
#include "drivers/dht11.h"
#include "drivers/voice_asr.h"
#include "app/fan_fsm.h"
#include "app/cli_test.h"

UART_HandleTypeDef g_uart1;
uint8_t g_cli_rx_byte = 0;

static void SystemClock_Config(void);
static void GPIO_Init(void);
static void UART1_Init(void);
static void log_printf(const char *fmt, ...);

int __io_putchar(int ch)
{
    HAL_UART_Transmit(&g_uart1, (uint8_t *)&ch, 1, 100);
    return ch;
}

int __io_getchar(void)
{
    uint8_t ch = 0;
    HAL_UART_Receive(&g_uart1, &ch, 1, HAL_MAX_DELAY);
    return ch;
}

void Error_Handler(void);

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    GPIO_Init();
    UART1_Init();
    delay_us_init();

    log_printf("\r\n========================================\r\n");
    log_printf("  Smart Fan Firmware v%s\r\n", FW_VERSION);
    log_printf("  Build: %s %s\r\n", __DATE__, __TIME__);
    log_printf("  SYSCLK: %lu Hz, APB1: %lu Hz, APB2: %lu Hz\r\n",
               (unsigned long)HAL_RCC_GetSysClockFreq(),
               (unsigned long)HAL_RCC_GetPCLK1Freq(),
               (unsigned long)HAL_RCC_GetPCLK2Freq());
    log_printf("========================================\r\n");

    /* 逐模块安全初始化 */
    log_printf("[INIT] 1. Buzzer (PB15)... ");
    buzzer_init();
    log_printf("OK (Silent)\r\n");

    log_printf("[INIT] 2. TB6612 Motor (PA0 PWM 25kHz, PA1/PA5 Dir, PB0 STBY)... ");
    motor_init();
    log_printf("OK (Safe Low, STBY=0, Duty=0)\r\n");

    log_printf("[INIT] 3. Continuous Servo (PB8 TIM4_CH3 50Hz)... ");
    servo_init();
    log_printf("OK (Stopped, 0us duty)\r\n");

    log_printf("[INIT] 4. Buttons (PB13 KEY1, PB14 KEY2)... ");
    button_init();
    log_printf("OK (Debounced, PB12 disabled)\r\n");

    log_printf("[INIT] 5. EC11 Encoder (PA6 TIM3_CH1, PA7 TIM3_CH2)... ");
    encoder_init();
    log_printf("OK (Hardware TI12 Mode with Filter)\r\n");

    log_printf("[INIT] 6. Shared I2C1 Bus (PB6 SCL, PB7 SDA)... ");
    i2c_bus_init();
    log_printf("OK (Bus Recovered)\r\n");

    log_printf("[INIT] 7. OLED SSD1306 (0x3C)... ");
    bool oled_ok = ssd1306_init();
    if (oled_ok) {
        log_printf("OK (Detected)\r\n");
        ssd1306_show_status("STANDBY", 0.0f, 0.0f, 0, "STOP", "INIT_OK");
    } else {
        log_printf("SKIPPED (Not detected or unplugged)\r\n");
    }

    log_printf("[INIT] 8. Gesture Sensor PAJ7620 (0x73, INT: PA4)... ");
    bool gest_ok = paj7620_init();
    if (gest_ok) {
        log_printf("OK (PartID: 0x7620)\r\n");
    } else {
        log_printf("SKIPPED (Not detected or unplugged)\r\n");
    }

    log_printf("[INIT] 9. DHT11 Sensor (PB9)... ");
    dht11_init();
    log_printf("OK\r\n");

    log_printf("[INIT] 10. Voice ASR-PRO (USART2 PA2/PA3 @ 115200)... ");
    voice_asr_init();
    log_printf("OK (Ring Buffer & IRQ Ready)\r\n");

    log_printf("[INIT] 11. Central Event State Machine & CLI... ");
    app_fsm_init();
    cli_test_init();
    log_printf("OK (State: POWER_OFF)\r\n");

    /* 启动双音提示音 */
    buzzer_beep_pattern(2, 60, 50);

    cli_print_banner();

    uint32_t last_led_ms = HAL_GetTick();
    uint32_t last_dht_ms = HAL_GetTick();
    uint32_t last_oled_ms = HAL_GetTick();

    static bool s_oled_sleeping = false;
    static uint32_t s_power_off_time_ms = 0;
    static fan_system_state_t s_last_sys_state = FAN_STATE_POWER_OFF;

    /* 开机初始化时记录初始关机待机时间 */
    s_power_off_time_ms = HAL_GetTick();

    while (1) {
        const uint32_t now = HAL_GetTick();

        /* 1. 串口交互测试控制台轮询 */
        cli_test_poll();

        /* 2. PCB按键事件派发 (KEY1电源启停，KEY2短按摇头/长按模式切换) */
        button_event_t b_evt;
        while ((b_evt = button_pop_event()) != BTN_EVT_NONE) {
            /* 任何实体按键按下即刻唤醒 OLED */
            s_power_off_time_ms = now;
            if (s_oled_sleeping) {
                s_oled_sleeping = false;
                ssd1306_set_display_on(true);
            }

            if (b_evt == BTN_EVT_KEY1_SHORT || b_evt == BTN_EVT_KEY1_LONG) {
                buzzer_beep(40); /* 按键提示音 */
                fan_event_t evt = {EVENT_TYPE_POWER_TOGGLE, 0, 0.0f, "KEY1_POWER"};
                app_fsm_post_event(&evt);
            } else if (b_evt == BTN_EVT_KEY2_SHORT) {
                buzzer_beep(40); /* KEY2短按：单声提示音，切换摇头 */
                fan_event_t evt = {EVENT_TYPE_SWING_TOGGLE, 0, 0.0f, "KEY2_SWING"};
                app_fsm_post_event(&evt);
            } else if (b_evt == BTN_EVT_KEY2_LONG) {
                buzzer_beep_pattern(2, 50, 40); /* KEY2长按：双声提示音，切换模式 */
                fan_event_t evt = {EVENT_TYPE_MODE_TOGGLE, 0, 0.0f, "KEY2_MODE"};
                app_fsm_post_event(&evt);
            } else if (b_evt == BTN_EVT_ENC_SW_SHORT || b_evt == BTN_EVT_ENC_SW_LONG) {
                buzzer_beep_pattern(2, 50, 40);
                fan_event_t evt = {EVENT_TYPE_MODE_TOGGLE, 0, 0.0f, "KNOB_MODE"};
                app_fsm_post_event(&evt);
            }
        }

        /* 3. EC11 编码器旋转检测 */
        int16_t enc_delta = encoder_get_delta();
        if (enc_delta != 0) {
            s_power_off_time_ms = now;
            if (s_oled_sleeping) {
                s_oled_sleeping = false;
                ssd1306_set_display_on(true);
            }
            fan_event_t evt = {EVENT_TYPE_SPEED_STEP, (int16_t)(enc_delta * 10), 0.0f, "ENCODER"};
            app_fsm_post_event(&evt);
            buzzer_beep(20);
        }

        /* 4. 语音 ASR-PRO 串口帧解析与事件派发 */
        voice_asr_poll();
        voice_cmd_t vcmd = voice_asr_pop_command();
        if (vcmd != VOICE_CMD_NONE) {
            /* 任何语音命令/唤醒词到来，立即唤醒 OLED 屏并重置 10 秒倒计时 */
            s_power_off_time_ms = now;
            if (s_oled_sleeping) {
                s_oled_sleeping = false;
                ssd1306_set_display_on(true);
            }

            buzzer_beep_pattern(2, 50, 40);
            if (vcmd == VOICE_CMD_WAKEUP) {
                /* 唤醒词收到提示音与屏幕显示 */
                fan_event_t evt = {EVENT_TYPE_NONE, 0, 0.0f, "VOICE:HELLO"};
                app_fsm_post_event(&evt);
            } else if (vcmd == VOICE_CMD_FAN_ON) {
                fan_event_t evt = {EVENT_TYPE_SPEED_SET, 40, 0.0f, "VOICE:FON"};
                app_fsm_post_event(&evt);
                voice_asr_send_ack("Fyes\r\n");
            } else if (vcmd == VOICE_CMD_FAN_OFF) {
                fan_event_t evt = {EVENT_TYPE_SPEED_SET, 0, 0.0f, "VOICE:FOFF"};
                app_fsm_post_event(&evt);
                voice_asr_send_ack("Foff\r\n");
            } else if (vcmd == VOICE_CMD_SPEED_UP) {
                fan_event_t evt = {EVENT_TYPE_SPEED_STEP, 10, 0.0f, "VOICE:F+"};
                app_fsm_post_event(&evt);
            } else if (vcmd == VOICE_CMD_SPEED_DOWN) {
                fan_event_t evt = {EVENT_TYPE_SPEED_STEP, -10, 0.0f, "VOICE:F-"};
                app_fsm_post_event(&evt);
            } else if (vcmd == VOICE_CMD_SPEED_MAX) {
                fan_event_t evt = {EVENT_TYPE_SPEED_SET, 100, 0.0f, "VOICE:FMAX"};
                app_fsm_post_event(&evt);
            } else if (vcmd == VOICE_CMD_SPEED_MED) {
                fan_event_t evt = {EVENT_TYPE_SPEED_SET, 50, 0.0f, "VOICE:FMOD"};
                app_fsm_post_event(&evt);
            } else if (vcmd == VOICE_CMD_SPEED_MIN) {
                fan_event_t evt = {EVENT_TYPE_SPEED_SET, 20, 0.0f, "VOICE:FMIN"};
                app_fsm_post_event(&evt);
            } else if (vcmd == VOICE_CMD_MODE_TOGGLE) {
                fan_event_t evt = {EVENT_TYPE_MODE_TOGGLE, 0, 0.0f, "VOICE:MODE"};
                app_fsm_post_event(&evt);
            } else if (vcmd == VOICE_CMD_MODE_AUTO) {
                fan_event_t evt = {EVENT_TYPE_MODE_SET, (int16_t)FAN_STATE_AUTO_TEMP, 0.0f, "VOICE:AUTO"};
                app_fsm_post_event(&evt);
            } else if (vcmd == VOICE_CMD_MODE_MANUAL) {
                fan_event_t evt = {EVENT_TYPE_MODE_SET, (int16_t)FAN_STATE_MANUAL_RUN, 0.0f, "VOICE:MANU"};
                app_fsm_post_event(&evt);
            } else if (vcmd == VOICE_CMD_SWING_ON) {
                fan_event_t evt = {EVENT_TYPE_SWING_SET, 1, 0.0f, "VOICE:SWON"};
                app_fsm_post_event(&evt);
            } else if (vcmd == VOICE_CMD_SWING_OFF) {
                fan_event_t evt = {EVENT_TYPE_SWING_SET, 0, 0.0f, "VOICE:SWOFF"};
                app_fsm_post_event(&evt);
            } else if (vcmd == VOICE_CMD_SWING_TOGGLE) {
                fan_event_t evt = {EVENT_TYPE_SWING_TOGGLE, 0, 0.0f, "VOICE:SWTOG"};
                app_fsm_post_event(&evt);
            } else if (vcmd == VOICE_CMD_SWING_SPEED_UP) {
                fan_event_t evt = {EVENT_TYPE_SWING_SPEED_STEP, 1, 0.0f, "VOICE:SW+"};
                app_fsm_post_event(&evt);
            } else if (vcmd == VOICE_CMD_SWING_SPEED_DOWN) {
                fan_event_t evt = {EVENT_TYPE_SWING_SPEED_STEP, -1, 0.0f, "VOICE:SW-"};
                app_fsm_post_event(&evt);
            } else if (vcmd == VOICE_CMD_SLEEP) {
                fan_event_t evt1 = {EVENT_TYPE_SPEED_SET, 20, 0.0f, "VOICE:SLEEP"};
                app_fsm_post_event(&evt1);
                fan_event_t evt2 = {EVENT_TYPE_SWING_SET, 0, 0.0f, "VOICE:SLEEP"};
                app_fsm_post_event(&evt2);
                voice_asr_send_ack("FSLEEP_OK\r\n");
            } else if (vcmd == VOICE_CMD_QUERY_TEMP) {
                const fan_fsm_ctx_t *ctx = app_fsm_get_context();
                float t = ctx ? ctx->current_temperature : 25.0f;
                if (t < 24.0f) {
                    voice_asr_send_ack("T_COOL\r\n");
                } else if (t < 28.0f) {
                    voice_asr_send_ack("T_COMF\r\n");
                } else if (t < 31.0f) {
                    voice_asr_send_ack("T_WARM\r\n");
                } else {
                    voice_asr_send_ack("T_HOT\r\n");
                }
            } else if (vcmd == VOICE_CMD_QUERY_STATUS) {
                const fan_fsm_ctx_t *ctx = app_fsm_get_context();
                if (ctx && ctx->sys_state == FAN_STATE_POWER_OFF) {
                    voice_asr_send_ack("S_OFF\r\n");
                } else if (ctx && ctx->sys_state == FAN_STATE_AUTO_TEMP) {
                    voice_asr_send_ack("S_AUTO\r\n");
                } else {
                    voice_asr_send_ack("S_RUN\r\n");
                }
            }
        }

        /* 5. PAJ7620 手势识别检测与热插拔自愈 */
        if (!gest_ok) {
            static uint32_t last_gest_retry_ms = 0;
            if (now - last_gest_retry_ms >= 1000U) {
                last_gest_retry_ms = now;
                if (paj7620_init()) {
                    gest_ok = true;
                    log_printf("[HOTPLUG] PAJ7620 gesture sensor detected & re-initialized!\r\n");
                }
            }
        } else {
            static uint32_t last_gest_poll_ms = 0;
            static uint32_t last_gest_act_ms = 0;
            bool trigger_read = paj7620_has_interrupt();

            /* 若硬件中断或每 30ms 轮询一次 */
            if (!trigger_read && (now - last_gest_poll_ms >= 30U)) {
                trigger_read = true;
                last_gest_poll_ms = now;
            }

            if (trigger_read) {
                uint16_t gesture = paj7620_read_gesture();
                if (gesture != PAJ7620_GESTURE_NONE) {
                    /* 手势识别立即唤醒 OLED 屏并重置倒计时 */
                    s_power_off_time_ms = now;
                    if (s_oled_sleeping) {
                        s_oled_sleeping = false;
                        ssd1306_set_display_on(true);
                    }

                    if (now - last_gest_act_ms >= 200U) {
                        last_gest_act_ms = now;
                        log_printf("[GESTURE] >>> Recognized: %s (Raw: 0x%04X, INT: %s) <<<\r\n",
                                   paj7620_gesture_to_str(gesture), gesture,
                                   paj7620_has_interrupt() ? "LOW" : "HIGH");

                        if (gesture == PAJ7620_GESTURE_UP) {
                            buzzer_beep(30);
                            fan_event_t evt = {EVENT_TYPE_SPEED_STEP, 10, 0.0f, "GEST_UP"};
                            app_fsm_post_event(&evt);
                        } else if (gesture == PAJ7620_GESTURE_DOWN) {
                            buzzer_beep(30);
                            fan_event_t evt = {EVENT_TYPE_SPEED_STEP, -10, 0.0f, "GEST_DOWN"};
                            app_fsm_post_event(&evt);
                        } else if (gesture == PAJ7620_GESTURE_FORWARD) {
                            buzzer_beep(40);
                            fan_event_t evt = {EVENT_TYPE_SPEED_SET, 50, 0.0f, "GEST_FWD_ON"};
                            app_fsm_post_event(&evt);
                        } else if (gesture == PAJ7620_GESTURE_BACKWARD) {
                            buzzer_beep_pattern(2, 40, 40);
                            fan_event_t evt = {EVENT_TYPE_SPEED_SET, 0, 0.0f, "GEST_BACK_OFF"};
                            app_fsm_post_event(&evt);
                        } else if (gesture == PAJ7620_GESTURE_RIGHT) {
                            buzzer_beep(30);
                            fan_event_t evt = {EVENT_TYPE_SWING_SET, 1, 0.0f, "GEST_SWING_ON"};
                            app_fsm_post_event(&evt);
                        } else if (gesture == PAJ7620_GESTURE_LEFT) {
                            buzzer_beep(30);
                            fan_event_t evt = {EVENT_TYPE_SWING_SET, 0, 0.0f, "GEST_SWING_OFF"};
                            app_fsm_post_event(&evt);
                        } else if (gesture == PAJ7620_GESTURE_CLOCKWISE || gesture == PAJ7620_GESTURE_COUNTER_CLOCK) {
                            buzzer_beep_pattern(2, 40, 40);
                            fan_event_t evt = {EVENT_TYPE_MODE_TOGGLE, 0, 0.0f, "GEST_CIRCLE"};
                            app_fsm_post_event(&evt);
                        } else if (gesture == PAJ7620_GESTURE_WAVE) {
                            buzzer_beep_pattern(3, 30, 30);
                            fan_event_t evt = {EVENT_TYPE_POWER_TOGGLE, 0, 0.0f, "GEST_WAVE"};
                            app_fsm_post_event(&evt);
                        }
                    }
                }
            }
        }

        /* 6. 蜂鸣器节奏、中央状态机 Tick 与 舵机扫风 Tick */
        buzzer_tick(now);
        app_fsm_tick(now);
        servo_tick(now);

        const fan_fsm_ctx_t *fsm_ctx = app_fsm_get_context();
        if (fsm_ctx->sys_state != s_last_sys_state) {
            if (fsm_ctx->sys_state == FAN_STATE_POWER_OFF) {
                s_power_off_time_ms = now;
                if (s_oled_sleeping) {
                    s_oled_sleeping = false;
                    ssd1306_set_display_on(true);
                }
            } else {
                if (s_oled_sleeping) {
                    s_oled_sleeping = false;
                    ssd1306_set_display_on(true);
                }
            }
            s_last_sys_state = fsm_ctx->sys_state;
        }

        /* 关机满 10 秒后熄灭 OLED，进入低功耗待机 */
        if (fsm_ctx->sys_state == FAN_STATE_POWER_OFF) {
            if (!s_oled_sleeping && (now - s_power_off_time_ms >= 10000U)) {
                ssd1306_clear();
                ssd1306_update();
                ssd1306_set_display_on(false);
                s_oled_sleeping = true;
            }
        }

        /* 7. 定时周期任务：DHT11 采样 (每 2 秒一次) */
        if (now - last_dht_ms >= 2000U) {
            last_dht_ms = now;
            float t = 0.0f, h = 0.0f;
            if (dht11_read(&t, &h)) {
                fan_event_t evt = {EVENT_TYPE_TEMP_UPDATE, 0, t, "DHT11"};
                evt.float_param = t;
                app_fsm_post_event(&evt);
                app_fsm_set_humidity(h);
            }
        }

        /* 8. 定时周期任务：OLED 刷新与热插拔自愈 */
        if (!oled_ok) {
            static uint32_t last_oled_retry_ms = 0;
            if (now - last_oled_retry_ms >= 500U) {
                last_oled_retry_ms = now;
                if (ssd1306_init()) {
                    oled_ok = true;
                    s_oled_sleeping = false;
                    log_printf("[HOTPLUG] OLED SSD1306 detected!\r\n");
                }
            }
        } else if (!s_oled_sleeping && (now - last_oled_ms >= 150U)) {
            last_oled_ms = now;
            const fan_fsm_ctx_t *ctx = app_fsm_get_context();
            const char *mode_str = (ctx->sys_state == FAN_STATE_POWER_OFF) ? "STANDBY" :
                                   (ctx->sys_state == FAN_STATE_MANUAL_RUN) ? "MANUAL" :
                                   (ctx->sys_state == FAN_STATE_AUTO_TEMP) ? "AUTO_TEMP" : "TEST";
            const char *servo_str = (ctx->swing_mode == FAN_SWING_OFF) ? "OFF" : "ON";

            char desc_buf[32];
            const char *display_desc = ctx->last_event_desc;
            if (ctx->sys_state == FAN_STATE_POWER_OFF) {
                uint32_t elapsed = now - s_power_off_time_ms;
                uint32_t remain_s = (elapsed < 10000U) ? ((10000U - elapsed + 999U) / 1000U) : 0;
                snprintf(desc_buf, sizeof(desc_buf), "Sleep in %lus...", (unsigned long)remain_s);
                display_desc = desc_buf;
            }

            ssd1306_show_status(mode_str, ctx->current_temperature, ctx->current_humidity,
                                ctx->actual_speed, servo_str, display_desc);
        }

        /* 9. 心跳 LED 翻转 (每 500 ms 一次) */
        if (now - last_led_ms >= 500U) {
            last_led_ms = now;
            HAL_GPIO_TogglePin(LED_GPIO_Port, LED_Pin);
        }
    }
}

static void SystemClock_Config(void)
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};

    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState = RCC_HSE_ON;
    osc.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
    osc.PLL.PLLState = RCC_PLL_ON;
    osc.PLL.PLLSource = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLMUL = RCC_PLL_MUL9; /* 8MHz x 9 = 72MHz */
    if (HAL_RCC_OscConfig(&osc) != HAL_OK) {
        Error_Handler();
    }

    clk.ClockType = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                    RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV2; /* APB1 = 36 MHz (TIM2/3/4 x2 = 72 MHz) */
    clk.APB2CLKDivider = RCC_HCLK_DIV1; /* APB2 = 72 MHz */
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2) != HAL_OK) {
        Error_Handler();
    }
}

static void GPIO_Init(void)
{
    GPIO_InitTypeDef gpio = {0};

    __HAL_RCC_AFIO_CLK_ENABLE();
    __HAL_AFIO_REMAP_SWJ_NOJTAG(); /* 禁用 JTAG 保留 SWD (PA13/PA14)，防止调试接口被意外占用 */

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();

    /* 心跳 LED (PC13) */
    HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_SET);
    gpio.Pin = LED_Pin;
    gpio.Mode = GPIO_MODE_OUTPUT_PP;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_GPIO_Port, &gpio);
}

static void UART1_Init(void)
{
    GPIO_InitTypeDef gpio = {0};

    __HAL_RCC_USART1_CLK_ENABLE();

    /* PA9: TX, PA10: RX */
    gpio.Pin = GPIO_PIN_9;
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &gpio);

    gpio.Pin = GPIO_PIN_10;
    gpio.Mode = GPIO_MODE_INPUT;
    gpio.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &gpio);

    g_uart1.Instance = USART1;
    g_uart1.Init.BaudRate = 115200;
    g_uart1.Init.WordLength = UART_WORDLENGTH_8B;
    g_uart1.Init.StopBits = UART_STOPBITS_1;
    g_uart1.Init.Parity = UART_PARITY_NONE;
    g_uart1.Init.Mode = UART_MODE_TX_RX;
    g_uart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    g_uart1.Init.OverSampling = UART_OVERSAMPLING_16;
    if (HAL_UART_Init(&g_uart1) != HAL_OK) {
        Error_Handler();
    }

    HAL_NVIC_SetPriority(USART1_IRQn, 3, 0);
    HAL_NVIC_EnableIRQ(USART1_IRQn);
    HAL_UART_Receive_IT(&g_uart1, &g_cli_rx_byte, 1);
}

static void log_printf(const char *fmt, ...)
{
    char buf[160];
    va_list ap;

    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);

    HAL_UART_Transmit(&g_uart1, (uint8_t *)buf, (uint16_t)strlen(buf), 200);
}

void Error_Handler(void)
{
    __disable_irq();
    HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_RESET);
    while (1) {
    }
}
