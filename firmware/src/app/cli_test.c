/**
 * @file cli_test.c
 * @brief 面包板逐模块独立测试控制台实现
 */
#include "cli_test.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>

#include "stm32f1xx_hal.h"
#include "config/pins.h"
#include "config/version.h"

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

extern UART_HandleTypeDef g_uart1;
extern uint8_t g_cli_rx_byte;

#define CLI_CMD_BUF_LEN 64
static char g_cli_buf[CLI_CMD_BUF_LEN];
static uint8_t g_cli_idx = 0;

static void cli_send(const char *str)
{
    if (str == NULL) return;
    HAL_UART_Transmit(&g_uart1, (const uint8_t *)str, (uint16_t)strlen(str), 200);
}

void cli_print_banner(void)
{
    cli_send("\r\n========================================\r\n");
    cli_send("  Smart Fan Modular Breadboard Console  \r\n");
    cli_send("  Firmware: v" FW_VERSION " (STM32F103C8T6)    \r\n");
    cli_send("  Clock: HSE 8MHz -> 72MHz, APB1: 36MHz \r\n");
    cli_send("  Type 'help' for test commands list.   \r\n");
    cli_send("========================================\r\nCMD> ");
}

static void cmd_help(void)
{
    cli_send("\r\nAvailable Test Commands:\r\n");
    cli_send("  status              - Print current sensors and actuator states\r\n");
    cli_send("  safe                - Emergency stop all actuators (STBY=0, PWM=0, Servo=0)\r\n");
    cli_send("  key1                - Simulate pressing KEY1 (Power ON/OFF)\r\n");
    cli_send("  key2                - Simulate pressing KEY2 (Swing ON/OFF)\r\n");
    cli_send("  mode / knob         - Simulate pressing Knob (Manual / AutoTemp)\r\n");
    cli_send("  test led [on|off]   - Control PC13 heartbeat LED\r\n");
    cli_send("  test buz [on|off|beep] - Control PB15 active buzzer\r\n");
    cli_send("  test key            - Read PB13 (KEY1) and PB14 (KEY2) pins\r\n");
    cli_send("  test enc            - Read EC11 PA6/PA7 encoder delta and total ticks\r\n");
    cli_send("  test dht            - Trigger PB9 DHT11 temperature & humidity read\r\n");
    cli_send("  test i2c            - Scan PB6/PB7 I2C bus and run bus recovery\r\n");
    cli_send("  test oled           - Test SSD1306 OLED display text\r\n");
    cli_send("  test gest           - Read PAJ7620 gesture registers & PA4 INT pin\r\n");
    cli_send("  test voice <cmd>    - Inject ASR-PRO command (FON, FOFF, F+, FMAX, etc.)\r\n");
    cli_send("  test motor <0-100> [fwd|rev] - Safe manual DC motor speed test\r\n");
    cli_send("  test servo [swing|stop|cw|ccw|us <val>] - Test MG90S 360 deg servo\r\n");
    cli_send("  servo [on|off|cw <us>|ccw <us>|time <ms>|trim <us>] - Tune MG90S 90-deg swing\r\n");
}

static void cmd_status(void)
{
    const fan_fsm_ctx_t *ctx = app_fsm_get_context();
    char buf[128];

    cli_send("\r\n--- System Status ---\r\n");
    snprintf(buf, sizeof(buf), "State: %s, Target Speed: %d%%, Actual Speed: %d%%\r\n",
             (ctx->sys_state == FAN_STATE_POWER_OFF) ? "POWER_OFF (SAFE)" :
             (ctx->sys_state == FAN_STATE_MANUAL_RUN) ? "MANUAL_RUN" :
             (ctx->sys_state == FAN_STATE_AUTO_TEMP) ? "AUTO_TEMP" : "TEST_MODE",
             ctx->target_speed, ctx->actual_speed);
    cli_send(buf);

    snprintf(buf, sizeof(buf), "Motor: STBY=%d, Speed=%d%%, Active=%s\r\n",
             HAL_GPIO_ReadPin(TB_STBY_Port, TB_STBY_Pin),
             motor_get_speed(),
             motor_is_active() ? "YES" : "NO");
    cli_send(buf);

    snprintf(buf, sizeof(buf), "Servo: Swing=%s, Angle=%.1f deg, Active=%s\r\n",
             servo_is_swing_enabled() ? "ENABLED (30~150 deg)" : "OFF",
             servo_get_current_angle(),
             servo_is_active() ? "YES" : "NO");
    cli_send(buf);

    int t_int = (int)ctx->current_temperature;
    int t_dec = (int)((ctx->current_temperature - (float)t_int) * 10.0f);
    if (t_dec < 0) t_dec = -t_dec;
    int h_int = (int)ctx->current_humidity;
    int h_dec = (int)((ctx->current_humidity - (float)h_int) * 10.0f);
    if (h_dec < 0) h_dec = -h_dec;

    snprintf(buf, sizeof(buf), "Sensors: T=%d.%d C, H=%d.%d %%, GestConnected=%s\r\n",
             t_int, t_dec, h_int, h_dec,
             paj7620_is_connected() ? "YES" : "NO");
    cli_send(buf);

    snprintf(buf, sizeof(buf), "Last Event: %s\r\n", ctx->last_event_desc);
    cli_send(buf);
}

static void cmd_safe(void)
{
    fan_event_t evt = {EVENT_TYPE_EMERGENCY_STOP, 0, 0.0f, "CLI_SAFE"};
    app_fsm_post_event(&evt);
    motor_emergency_stop();
    servo_stop();
    buzzer_set(false);
    cli_send("\r\n[SAFE] All actuators stopped immediately! STBY=LOW, PWM=0%.\r\n");
}

static bool cli_test_pop_rx_byte(uint8_t *byte);

static void execute_cli_command(char *cmd_line)
{
    /* 去除前后空白 */
    while (*cmd_line && isspace((unsigned char)*cmd_line)) cmd_line++;
    if (*cmd_line == '\0') return;

    char *arg1 = strtok(cmd_line, " ");
    char *arg2 = strtok(NULL, " ");
    char *arg3 = strtok(NULL, " ");
    char *arg4 = strtok(NULL, " ");

    if (strcmp(arg1, "help") == 0) {
        cmd_help();
    } else if (strcmp(arg1, "status") == 0) {
        cmd_status();
    } else if (strcmp(arg1, "safe") == 0) {
        cmd_safe();
    } else if (strcmp(arg1, "test") == 0) {
        if (arg2 == NULL) {
            cli_send("\r\nError: 'test' requires a module name. Type 'help' for syntax.\r\n");
            return;
        }

        if (strcmp(arg2, "led") == 0) {
            if (arg3 && strcmp(arg3, "on") == 0) {
                HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_RESET); /* 蓝板低有效点亮 */
                cli_send("\r\nLED (PC13) set ON (LOW)\r\n");
            } else if (arg3 && strcmp(arg3, "off") == 0) {
                HAL_GPIO_WritePin(LED_GPIO_Port, LED_Pin, GPIO_PIN_SET);
                cli_send("\r\nLED (PC13) set OFF (HIGH)\r\n");
            } else {
                HAL_GPIO_TogglePin(LED_GPIO_Port, LED_Pin);
                cli_send("\r\nLED (PC13) toggled\r\n");
            }
        } else if (strcmp(arg2, "buz") == 0) {
            if (arg3 && strcmp(arg3, "on") == 0) {
                buzzer_set(true);
                cli_send("\r\nBuzzer (PB15) set ON (HIGH)\r\n");
            } else if (arg3 && strcmp(arg3, "off") == 0) {
                buzzer_set(false);
                cli_send("\r\nBuzzer (PB15) set OFF (LOW)\r\n");
            } else {
                buzzer_beep_pattern(2, 80, 50);
                cli_send("\r\nBuzzer double-beep triggered\r\n");
            }
        } else if (strcmp(arg2, "key") == 0) {
            char buf[128];
            uint8_t k1 = (HAL_GPIO_ReadPin(KEY1_POWER_Port, KEY1_POWER_Pin) == GPIO_PIN_RESET) ? 1 : 0;
            uint8_t k2 = (HAL_GPIO_ReadPin(KEY2_SWING_Port, KEY2_SWING_Pin) == GPIO_PIN_RESET) ? 1 : 0;
            uint8_t ksw = (HAL_GPIO_ReadPin(ENC_SW_Port, ENC_SW_Pin) == GPIO_PIN_RESET) ? 1 : 0;
            snprintf(buf, sizeof(buf), "\r\nButtons: KEY1_POWER(PB13)=%s, KEY2_SWING(PB14)=%s, ENC_SW_MODE(PB12)=%s\r\n",
                     k1 ? "PRESSED" : "RELEASED",
                     k2 ? "PRESSED" : "RELEASED",
                     ksw ? "PRESSED" : "RELEASED");
            cli_send(buf);
        } else if (strcmp(arg2, "enc") == 0) {
            char buf[64];
            int16_t delta = encoder_get_delta();
            int32_t total = encoder_get_total_count();
            snprintf(buf, sizeof(buf), "\r\nEncoder: Delta=%d, TotalTicks=%ld\r\n", delta, (long)total);
            cli_send(buf);
        } else if (strcmp(arg2, "dht") == 0) {
            float t = 0.0f, h = 0.0f;
            cli_send("\r\nReading DHT11 on PB9...\r\n");
            if (dht11_read(&t, &h)) {
                int ti = (int)t, td = (int)((t - (float)ti) * 10.0f);
                if (td < 0) td = -td;
                int hi = (int)h, hd = (int)((h - (float)hi) * 10.0f);
                if (hd < 0) hd = -hd;
                char buf[64];
                snprintf(buf, sizeof(buf), "DHT11 OK: Temperature=%d.%d C, Humidity=%d.%d %%\r\n", ti, td, hi, hd);
                cli_send(buf);
            } else {
                cli_send("DHT11 Read FAILED! Check 3.3V, GND, and PB9 wiring.\r\n");
            }
        } else if (strcmp(arg2, "i2c") == 0) {
            cli_send("\r\nRecovering I2C bus...\r\n");
            i2c_bus_recover();
            i2c_bus_scan();
        } else if (strcmp(arg2, "oled") == 0) {
            cli_send("\r\nTesting SSD1306 OLED (0x3C)...\r\n");
            if (ssd1306_init()) {
                ssd1306_show_status("TEST MODE", 26.5f, 52.0f, 30, "CW", "CLI_TEST");
                cli_send("SSD1306 OLED initialized and updated OK.\r\n");
            } else {
                cli_send("SSD1306 OLED NOT detected at 0x3C! Check wiring (GND, 3.3V, SCL, SDA).\r\n");
            }
        } else if (strcmp(arg2, "gest") == 0) {
            if (arg3 && strcmp(arg3, "init") == 0) {
                cli_send("\r\nRe-initializing PAJ7620 sensor...\r\n");
                bool ok = paj7620_init();
                char buf[64];
                snprintf(buf, sizeof(buf), "PAJ7620 Init: %s (Address 0x73, INT: PA4)\r\n", ok ? "SUCCESS" : "FAILED");
                cli_send(buf);
            } else if (arg3 && (strcmp(arg3, "live") == 0 || strcmp(arg3, "monitor") == 0)) {
                cli_send("\r\n=== PAJ7620 Live Monitor (15s, wave hand 5-15cm above sensor) ===\r\n");
                cli_send("Press any key to exit...\r\n");
                uint32_t start_ms = HAL_GetTick();
                uint8_t rx_dummy = 0;
                while (HAL_GetTick() - start_ms < 15000U) {
                    if (cli_test_pop_rx_byte(&rx_dummy)) {
                        break;
                    }
                    if (paj7620_has_interrupt() || ((HAL_GetTick() % 25) == 0)) {
                        uint16_t g = paj7620_read_gesture();
                        if (g != PAJ7620_GESTURE_NONE) {
                            buzzer_beep(30);
                            char gbuf[80];
                            snprintf(gbuf, sizeof(gbuf), ">> [%lu ms] GESTURE DETECTED: %s (0x%04X, INT: %s)\r\n",
                                     HAL_GetTick() - start_ms,
                                     paj7620_gesture_to_str(g), g,
                                     paj7620_has_interrupt() ? "LOW" : "HIGH");
                            cli_send(gbuf);
                            HAL_Delay(150);
                        }
                    }
                    HAL_Delay(10);
                }
                cli_send("=== Live Monitor Ended ===\r\n");
            } else {
                char buf[160];
                bool int_act = paj7620_has_interrupt();
                uint16_t g = paj7620_read_gesture();
                snprintf(buf, sizeof(buf), "\r\nGesture: Present=%s, INT(PA4)=%s, Code=0x%04X (%s)\r\n"
                                           "Tip: Use 'test gest monitor' or 'test gest init' for deep testing.\r\n",
                         paj7620_is_connected() ? "YES" : "NO",
                         int_act ? "ACTIVE (LOW)" : "HIGH",
                         g, paj7620_gesture_to_str(g));
                cli_send(buf);
            }
        } else if (strcmp(arg2, "voice") == 0) {
            if (arg3 == NULL) {
                cli_send("\r\nUsage: test voice <cmd> (e.g. FON, FOFF, F+, F-, FMAX, FAUTO, FMANU, SWON, SWOFF, SW+, SW-)\r\n");
                return;
            }
            voice_cmd_t cmd = voice_parse_command_line(arg3);
            char buf[64];
            snprintf(buf, sizeof(buf), "\r\nParsed Voice Command: %d for '%s'\r\n", (int)cmd, arg3);
            cli_send(buf);
            if (cmd == VOICE_CMD_FAN_ON) {
                fan_event_t evt = {EVENT_TYPE_SPEED_SET, 40, 0.0f, "VOICE:FON"};
                app_fsm_post_event(&evt);
                voice_asr_send_ack("Fyes\r\n");
                cli_send("Dispatched FAN_ON, sent ACK 'Fyes'\r\n");
            } else if (cmd == VOICE_CMD_FAN_OFF) {
                fan_event_t evt = {EVENT_TYPE_SPEED_SET, 0, 0.0f, "VOICE:FOFF"};
                app_fsm_post_event(&evt);
                voice_asr_send_ack("Foff\r\n");
                cli_send("Dispatched FAN_OFF, sent ACK 'Foff'\r\n");
            } else if (cmd == VOICE_CMD_SPEED_UP) {
                fan_event_t evt = {EVENT_TYPE_SPEED_STEP, 10, 0.0f, "VOICE:F+"};
                app_fsm_post_event(&evt);
                cli_send("Dispatched SPEED +10%\r\n");
            } else if (cmd == VOICE_CMD_SPEED_DOWN) {
                fan_event_t evt = {EVENT_TYPE_SPEED_STEP, -10, 0.0f, "VOICE:F-"};
                app_fsm_post_event(&evt);
                cli_send("Dispatched SPEED -10%\r\n");
            } else if (cmd == VOICE_CMD_MODE_AUTO) {
                fan_event_t evt = {EVENT_TYPE_MODE_SET, (int16_t)FAN_STATE_AUTO_TEMP, 0.0f, "VOICE:AUTO"};
                app_fsm_post_event(&evt);
                cli_send("Dispatched MODE: AUTO_TEMP\r\n");
            } else if (cmd == VOICE_CMD_MODE_MANUAL) {
                fan_event_t evt = {EVENT_TYPE_MODE_SET, (int16_t)FAN_STATE_MANUAL_RUN, 0.0f, "VOICE:MANU"};
                app_fsm_post_event(&evt);
                cli_send("Dispatched MODE: MANUAL\r\n");
            } else if (cmd == VOICE_CMD_SWING_ON) {
                fan_event_t evt = {EVENT_TYPE_SWING_SET, 1, 0.0f, "VOICE:SWON"};
                app_fsm_post_event(&evt);
                cli_send("Dispatched SWING: ON\r\n");
            } else if (cmd == VOICE_CMD_SWING_OFF) {
                fan_event_t evt = {EVENT_TYPE_SWING_SET, 0, 0.0f, "VOICE:SWOFF"};
                app_fsm_post_event(&evt);
                cli_send("Dispatched SWING: OFF\r\n");
            } else if (cmd == VOICE_CMD_SWING_SPEED_UP) {
                fan_event_t evt = {EVENT_TYPE_SWING_SPEED_STEP, 1, 0.0f, "VOICE:SW+"};
                app_fsm_post_event(&evt);
                cli_send("Dispatched SWING SPEED: +1\r\n");
            } else if (cmd == VOICE_CMD_SWING_SPEED_DOWN) {
                fan_event_t evt = {EVENT_TYPE_SWING_SPEED_STEP, -1, 0.0f, "VOICE:SW-"};
                app_fsm_post_event(&evt);
                cli_send("Dispatched SWING SPEED: -1\r\n");
            }
        } else if (strcmp(arg2, "motor") == 0) {
            if (arg3 == NULL) {
                cli_send("\r\nUsage: test motor <0-100> [fwd|rev]\r\n");
                return;
            }
            int spd = atoi(arg3);
            if (spd < 0) spd = 0;
            if (spd > 100) spd = 100;
            if (arg4 && strcmp(arg4, "rev") == 0) {
                spd = -spd;
            }
            char buf[64];
            snprintf(buf, sizeof(buf), "\r\nSetting motor speed to %d%% (25kHz PWM)...\r\n", spd);
            cli_send(buf);
            motor_set_speed((int8_t)spd);
            fan_event_t evt = {EVENT_TYPE_SPEED_SET, (int16_t)spd, 0.0f, "CLI_MOTOR"};
            app_fsm_post_event(&evt);
        } else if (strcmp(arg2, "servo") == 0) {
            if (arg3 == NULL) {
                cli_send("\r\nUsage: test servo <swing [on|off]|stop|cw|ccw|neutral <us>|period <ms>|offset <us>|speed <1-5>|us <us>>\r\n");
                return;
            }
            if (strcmp(arg3, "stop") == 0) {
                servo_set_swing_enabled(false);
                servo_stop();
                cli_send("\r\nServo stopped (PWM 0 duty, motor released)\r\n");
            } else if (strcmp(arg3, "neutral") == 0) {
                if (arg4) {
                    servo_set_neutral_us((uint16_t)atoi(arg4));
                }
                char buf[64];
                snprintf(buf, sizeof(buf), "\r\nServo neutral: %d us\r\n", servo_get_neutral_us());
                cli_send(buf);
            } else if (strcmp(arg3, "period") == 0 && arg4 != NULL) {
                servo_set_half_period_ms((uint32_t)atoi(arg4));
                char buf[64];
                snprintf(buf, sizeof(buf), "\r\nServo swing half-period: %lu ms\r\n", servo_get_half_period_ms());
                cli_send(buf);
            } else if (strcmp(arg3, "offset") == 0 && arg4 != NULL) {
                servo_set_pulse_offset((uint16_t)atoi(arg4));
                char buf[64];
                snprintf(buf, sizeof(buf), "\r\nServo swing pulse offset: %d us\r\n", servo_get_pulse_offset());
                cli_send(buf);
            } else if (strcmp(arg3, "center") == 0) {
                servo_set_swing_enabled(false);
                servo_set_pulse_us(servo_get_neutral_us());
                cli_send("\r\nServo neutral hold (1500us)\r\n");
            } else if (strcmp(arg3, "angle") == 0 && arg4 != NULL) {
                servo_set_swing_enabled(false);
                float deg = (float)atof(arg4);
                servo_set_angle(deg);
                char buf[64];
                snprintf(buf, sizeof(buf), "\r\nServo set: %.1f\r\n", deg);
                cli_send(buf);
            } else if (strcmp(arg3, "speed") == 0 && arg4 != NULL) {
                uint8_t spd = (uint8_t)atoi(arg4);
                servo_set_motion(SERVO_MOTION_CW, spd);
                char buf[80];
                snprintf(buf, sizeof(buf), "\r\nServo speed level: %d (offset: %dus, half-period: %lums)\r\n",
                         spd, servo_get_pulse_offset(), servo_get_half_period_ms());
                cli_send(buf);
            } else if (strcmp(arg3, "swing") == 0) {
                if (arg4 && strcmp(arg4, "off") == 0) {
                    servo_set_swing_enabled(false);
                    cli_send("\r\nServo 360 bounded swing DISABLED\r\n");
                } else {
                    servo_set_swing_enabled(true);
                    char buf[80];
                    snprintf(buf, sizeof(buf), "\r\nServo 360 bounded swing ENABLED (T_half: %lums, offset: %dus)\r\n",
                             servo_get_half_period_ms(), servo_get_pulse_offset());
                    cli_send(buf);
                }
            } else if (strcmp(arg3, "cw") == 0) {
                servo_set_swing_enabled(false);
                servo_set_pulse_us(servo_get_neutral_us() + servo_get_pulse_offset());
                cli_send("\r\nServo rotating CW (Right)\r\n");
            } else if (strcmp(arg3, "ccw") == 0) {
                servo_set_swing_enabled(false);
                servo_set_pulse_us(servo_get_neutral_us() - servo_get_pulse_offset());
                cli_send("\r\nServo rotating CCW (Left)\r\n");
            } else if (strcmp(arg3, "us") == 0 && arg4 != NULL) {
                int us = atoi(arg4);
                char buf[64];
                snprintf(buf, sizeof(buf), "\r\nServo direct pulse width: %d us\r\n", us);
                cli_send(buf);
                servo_set_pulse_us((uint16_t)us);
            }
        } else {
            cli_send("\r\nUnknown test module. Type 'help' for list.\r\n");
        }
    } else if (strcmp(arg1, "servo") == 0) {
        if (arg2 != NULL && strcmp(arg2, "cw") == 0 && arg3 != NULL) {
            int val = atoi(arg3);
            if (val > 0) servo_set_cw_offset((uint16_t)val);
            char buf[80];
            snprintf(buf, sizeof(buf), "\r\n[SERVO] CW offset set to %d us (CW pulse: %d us)\r\n",
                     servo_get_cw_offset(), servo_get_neutral_us() + servo_get_cw_offset());
            cli_send(buf);
        } else if (arg2 != NULL && strcmp(arg2, "ccw") == 0 && arg3 != NULL) {
            int val = atoi(arg3);
            if (val > 0) servo_set_ccw_offset((uint16_t)val);
            char buf[80];
            snprintf(buf, sizeof(buf), "\r\n[SERVO] CCW offset set to %d us (CCW pulse: %d us)\r\n",
                     servo_get_ccw_offset(), servo_get_neutral_us() - servo_get_ccw_offset());
            cli_send(buf);
        } else if (arg2 != NULL && (strcmp(arg2, "trim") == 0 || strcmp(arg2, "drift") == 0) && arg3 != NULL) {
            int val = atoi(arg3);
            servo_set_drift_trim((int8_t)val);
            char buf[80];
            snprintf(buf, sizeof(buf), "\r\n[SERVO] Drift trim set to %d us (CW pulse = neutral + CW + %d)\r\n", val, val);
            cli_send(buf);
        } else if (arg2 != NULL && (strcmp(arg2, "offset") == 0 || strcmp(arg2, "speed") == 0) && arg3 != NULL) {
            int val = atoi(arg3);
            if (val > 0) servo_set_pulse_offset((uint16_t)val);
            char buf[80];
            snprintf(buf, sizeof(buf), "\r\n[SERVO] Pulse offset set to %d us (CW: %dus, CCW: %dus)\r\n",
                     val, servo_get_cw_offset(), servo_get_ccw_offset());
            cli_send(buf);
        } else if (arg2 != NULL && (strcmp(arg2, "time") == 0 || strcmp(arg2, "period") == 0) && arg3 != NULL) {
            int val = atoi(arg3);
            if (val > 0) servo_set_half_period_ms((uint32_t)val);
            char buf[80];
            snprintf(buf, sizeof(buf), "\r\n[SERVO] Half-period set to %lu ms (90-deg stroke timing)\r\n", (unsigned long)servo_get_half_period_ms());
            cli_send(buf);
        } else if (arg2 != NULL && strcmp(arg2, "on") == 0) {
            fan_event_t evt = {EVENT_TYPE_SWING_SET, 1, 0.0f, "CLI:SW_ON"};
            app_fsm_post_event(&evt);
            cli_send("\r\n[SERVO] Swing started (90-deg reciprocating)\r\n");
        } else if (arg2 != NULL && strcmp(arg2, "off") == 0) {
            fan_event_t evt = {EVENT_TYPE_SWING_SET, 0, 0.0f, "CLI:SW_OFF"};
            app_fsm_post_event(&evt);
            cli_send("\r\n[SERVO] Swing stopped\r\n");
        } else {
            char buf[512];
            snprintf(buf, sizeof(buf),
                     "\r\n[SERVO STATUS] Neutral: %d us | CW: %d us | CCW: %d us | Half-Period: %lu ms (90 deg) | Trim: %d us\r\n"
                     "Commands:\r\n"
                     "  servo cw <us>       - Adjust CW speed offset (default: 28)\r\n"
                     "  servo ccw <us>      - Adjust CCW speed offset (default: 34)\r\n"
                     "  servo time <ms>     - Adjust 90-deg stroke time (default: 2000 ms)\r\n"
                     "  servo trim <-30~30> - Balance CW/CCW drift\r\n"
                     "  servo <on|off>      - Turn swing on/off\r\n",
                     servo_get_neutral_us(), servo_get_cw_offset(), servo_get_ccw_offset(),
                     (unsigned long)servo_get_half_period_ms(), servo_get_drift_trim());
            cli_send(buf);
        }
    } else if (strcmp(arg1, "key1") == 0) {
        buzzer_beep(40);
        fan_event_t evt = {EVENT_TYPE_POWER_TOGGLE, 0, 0.0f, "CLI:KEY1"};
        app_fsm_post_event(&evt);
        cli_send("\r\n[KEY1] Dispatched POWER_TOGGLE\r\n");
    } else if (strcmp(arg1, "key2") == 0 || strcmp(arg1, "key2_short") == 0) {
        buzzer_beep(40);
        fan_event_t evt = {EVENT_TYPE_SWING_TOGGLE, 0, 0.0f, "CLI:KEY2_SHORT"};
        app_fsm_post_event(&evt);
        cli_send("\r\n[KEY2 Short] Dispatched SWING_TOGGLE\r\n");
    } else if (strcmp(arg1, "key2_long") == 0 || strcmp(arg1, "mode") == 0 || strcmp(arg1, "knob") == 0) {
        buzzer_beep_pattern(2, 50, 40);
        fan_event_t evt = {EVENT_TYPE_MODE_TOGGLE, 0, 0.0f, "CLI:KEY2_LONG"};
        app_fsm_post_event(&evt);
        cli_send("\r\n[KEY2 Long / MODE] Dispatched MODE_TOGGLE\r\n");
    } else if (strcmp(arg1, "reboot") == 0 || strcmp(arg1, "reset") == 0) {
        cli_send("\r\nSystem rebooting via software...\r\n");
        HAL_Delay(50);
        NVIC_SystemReset();
    } else {
        cli_send("\r\nUnknown command. Type 'help' for list.\r\n");
    }

    cli_send("\r\nCMD> ");
}

#define CLI_RX_RING_SIZE 128
static volatile uint8_t g_cli_rx_ring[CLI_RX_RING_SIZE];
static volatile uint16_t g_cli_rx_head = 0;
static volatile uint16_t g_cli_rx_tail = 0;

void cli_test_push_rx_byte(uint8_t byte)
{
    uint16_t next = (uint16_t)((g_cli_rx_head + 1) % CLI_RX_RING_SIZE);
    if (next != g_cli_rx_tail) {
        g_cli_rx_ring[g_cli_rx_head] = byte;
        g_cli_rx_head = next;
    }
}

static bool cli_test_pop_rx_byte(uint8_t *byte)
{
    if (g_cli_rx_head == g_cli_rx_tail) return false;
    *byte = g_cli_rx_ring[g_cli_rx_tail];
    g_cli_rx_tail = (uint16_t)((g_cli_rx_tail + 1) % CLI_RX_RING_SIZE);
    return true;
}

void cli_test_init(void)
{
    g_cli_idx = 0;
    g_cli_rx_head = 0;
    g_cli_rx_tail = 0;
    memset(g_cli_buf, 0, sizeof(g_cli_buf));
}

void cli_test_poll(void)
{
    /* 若因总线错误或热插拔退出中断接收态，立即自愈重启接收 */
    if (g_uart1.RxState == HAL_UART_STATE_READY) {
        HAL_UART_Receive_IT(&g_uart1, &g_cli_rx_byte, 1);
    }

    uint8_t ch = 0;
    while (cli_test_pop_rx_byte(&ch)) {
        if (ch == '\r' || ch == '\n') {
            if (g_cli_idx > 0) {
                g_cli_buf[g_cli_idx] = '\0';
                execute_cli_command(g_cli_buf);
                g_cli_idx = 0;
            } else {
                cli_send("\r\nCMD> ");
            }
        } else if (ch == '\b' || ch == 127) { /* Backspace */
            if (g_cli_idx > 0) {
                g_cli_idx--;
                cli_send("\b \b");
            }
        } else if (g_cli_idx < (CLI_CMD_BUF_LEN - 1)) {
            if (isprint(ch)) {
                g_cli_buf[g_cli_idx++] = (char)ch;
                /* 回显字符 */
                char echo[2] = {(char)ch, '\0'};
                cli_send(echo);
            }
        }
    }
}
