/**
 * @file test_runner.c
 * @brief 智能风扇固件核心逻辑宿主机单元测试套件
 *
 * 覆盖测试：
 * 1. ASR-PRO 串口环形缓冲、换行帧截取、词条解析、噪声容错与环形回绕
 * 2. 独立按键状态机：毛刺消抖、短按识别、长按识别、长按释放防抖
 * 3. 中央控制状态机：上电安全默认态、启停切换、急停保护、速度限幅、温控分级曲线
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <stdbool.h>

#define HOST_UNIT_TEST 1

#include "drivers/voice_asr.h"
#include "drivers/button.h"
#include "app/fan_fsm.h"

/* 编译引入无硬件依赖的 C 源码 */
#include "drivers/voice_asr.c"
#include "drivers/button.c"
#include "app/fan_fsm.c"

static int g_tests_run = 0;
static int g_tests_passed = 0;
static int g_tests_failed = 0;

#define TEST_ASSERT(cond, msg) do { \
    g_tests_run++; \
    if (cond) { \
        g_tests_passed++; \
        printf("  [PASS] %s\n", msg); \
    } else { \
        g_tests_failed++; \
        printf("  [FAIL] %s (Line %d: %s)\n", msg, __LINE__, #cond); \
    } \
} while(0)

/* =========================================================================
 * 1. 语音协议解析与环形缓冲测试
 * ========================================================================= */
static void run_voice_protocol_tests(void)
{
    printf("\n=== 1. Voice Protocol & Ring Buffer Unit Tests ===\n");

    /* 词条解析测试 */
    TEST_ASSERT(voice_parse_command_line("INIT") == VOICE_CMD_WAKEUP, "Parse 'INIT' wakeup");
    TEST_ASSERT(voice_parse_command_line("FON") == VOICE_CMD_FAN_ON, "Parse 'FON' fan on");
    TEST_ASSERT(voice_parse_command_line("FOFF") == VOICE_CMD_FAN_OFF, "Parse 'FOFF' fan off");
    TEST_ASSERT(voice_parse_command_line("F+") == VOICE_CMD_SPEED_UP, "Parse 'F+' speed up");
    TEST_ASSERT(voice_parse_command_line("F-") == VOICE_CMD_SPEED_DOWN, "Parse 'F-' speed down");
    TEST_ASSERT(voice_parse_command_line("FMAX") == VOICE_CMD_SPEED_MAX, "Parse 'FMAX' max speed");
    TEST_ASSERT(voice_parse_command_line("FMOD") == VOICE_CMD_SPEED_MED, "Parse 'FMOD' med speed");
    TEST_ASSERT(voice_parse_command_line("FMIN") == VOICE_CMD_SPEED_MIN, "Parse 'FMIN' min speed");
    TEST_ASSERT(voice_parse_command_line("FMODE") == VOICE_CMD_MODE_TOGGLE, "Parse 'FMODE' mode toggle");
    TEST_ASSERT(voice_parse_command_line("FAUTO") == VOICE_CMD_MODE_AUTO, "Parse 'FAUTO' auto mode");
    TEST_ASSERT(voice_parse_command_line("FMANU") == VOICE_CMD_MODE_MANUAL, "Parse 'FMANU' manual mode");
    TEST_ASSERT(voice_parse_command_line("SWON") == VOICE_CMD_SWING_ON, "Parse 'SWON' swing on");
    TEST_ASSERT(voice_parse_command_line("SWOFF") == VOICE_CMD_SWING_OFF, "Parse 'SWOFF' swing off");
    TEST_ASSERT(voice_parse_command_line("SW+") == VOICE_CMD_SWING_SPEED_UP, "Parse 'SW+' swing speed up");
    TEST_ASSERT(voice_parse_command_line("SW-") == VOICE_CMD_SWING_SPEED_DOWN, "Parse 'SW-' swing speed down");
    TEST_ASSERT(voice_parse_command_line("LON") == VOICE_CMD_LIGHT_ON, "Parse 'LON' light on");
    TEST_ASSERT(voice_parse_command_line("LOFF") == VOICE_CMD_LIGHT_OFF, "Parse 'LOFF' light off");
    TEST_ASSERT(voice_parse_command_line("FSLEEP") == VOICE_CMD_SLEEP, "Parse 'FSLEEP' sleep mode");
    TEST_ASSERT(voice_parse_command_line("QTEMP") == VOICE_CMD_QUERY_TEMP, "Parse 'QTEMP' query temp");
    TEST_ASSERT(voice_parse_command_line("QSTAT") == VOICE_CMD_QUERY_STATUS, "Parse 'QSTAT' query status");
    TEST_ASSERT(voice_parse_command_line("INVALID") == VOICE_CMD_NONE, "Parse unknown command as NONE");

    /* 环形缓冲单帧截取测试 */
    voice_ring_buf_t rb = {{0}, 0, 0, 0};
    const char *stream1 = "FON\r\n";
    for (size_t i = 0; i < strlen(stream1); i++) {
        voice_ring_push(&rb, (uint8_t)stream1[i]);
    }
    char line[32];
    bool extracted = voice_extract_line(&rb, line, sizeof(line));
    TEST_ASSERT(extracted && strcmp(line, "FON") == 0, "Extract line 'FON' from buffer");
    TEST_ASSERT(voice_parse_command_line(line) == VOICE_CMD_FAN_ON, "Parsed extracted line as FAN_ON");

    /* 连续多帧提取测试 */
    const char *stream2 = "F+\r\nFOFF\r\n";
    for (size_t i = 0; i < strlen(stream2); i++) {
        voice_ring_push(&rb, (uint8_t)stream2[i]);
    }
    TEST_ASSERT(voice_extract_line(&rb, line, sizeof(line)) && strcmp(line, "F+") == 0, "Extract first multi-frame 'F+'");
    TEST_ASSERT(voice_extract_line(&rb, line, sizeof(line)) && strcmp(line, "FOFF") == 0, "Extract second multi-frame 'FOFF'");
    TEST_ASSERT(!voice_extract_line(&rb, line, sizeof(line)), "Ring buffer now empty");

    /* 环形缓冲回绕边界 (Wraparound) 测试 */
    rb.head = VOICE_RING_BUF_SIZE - 2;
    rb.tail = VOICE_RING_BUF_SIZE - 2;
    const char *wrap_str = "FMAX\r\n";
    for (size_t i = 0; i < strlen(wrap_str); i++) {
        voice_ring_push(&rb, (uint8_t)wrap_str[i]);
    }
    TEST_ASSERT(voice_extract_line(&rb, line, sizeof(line)) && strcmp(line, "FMAX") == 0,
                "Ring buffer wraparound extracts 'FMAX' cleanly");
}

/* =========================================================================
 * 2. 独立按键消抖与长短按状态机测试
 * ========================================================================= */
static void run_button_fsm_tests(void)
{
    printf("\n=== 2. Button Debounce & State Machine Unit Tests ===\n");

    button_tracker_t tracker = {BTN_STATE_RELEASED, 0, 0, false};
    button_event_t evt;

    /* 测试 1：毛刺抖动抑制 (持续 10ms，小于 15ms 消抖阈值) */
    evt = button_fsm_update(&tracker, true, 100, BTN_EVT_KEY1_SHORT, BTN_EVT_NONE);
    TEST_ASSERT(evt == BTN_EVT_NONE && tracker.state == BTN_STATE_DEBOUNCE_PRESS, "Button enters debounce state");
    /* 10ms 后释放 (抖动消失) */
    evt = button_fsm_update(&tracker, false, 110, BTN_EVT_KEY1_SHORT, BTN_EVT_NONE);
    TEST_ASSERT(evt == BTN_EVT_NONE && tracker.state == BTN_STATE_RELEASED, "Glitch rejected, returned to RELEASED");

    /* 测试 2：正常按下 (15ms 消抖后即刻触发，零延迟实体按键手感) */
    button_fsm_update(&tracker, true, 200, BTN_EVT_KEY1_SHORT, BTN_EVT_NONE);
    evt = button_fsm_update(&tracker, true, 220, BTN_EVT_KEY1_SHORT, BTN_EVT_NONE); /* 20ms > 15ms debounce */
    TEST_ASSERT(evt == BTN_EVT_KEY1_SHORT && tracker.state == BTN_STATE_PRESSED, "Short press event triggered immediately upon press confirmation");

    /* 测试 3：持续按住不应重复产生事件 */
    evt = button_fsm_update(&tracker, true, 500, BTN_EVT_KEY1_SHORT, BTN_EVT_NONE);
    TEST_ASSERT(evt == BTN_EVT_NONE, "No duplicate events while holding button");

    /* 测试 4：释放过程进入释放消抖，不产生额外事件 */
    evt = button_fsm_update(&tracker, false, 600, BTN_EVT_KEY1_SHORT, BTN_EVT_NONE);
    TEST_ASSERT(evt == BTN_EVT_NONE && tracker.state == BTN_STATE_DEBOUNCE_RELEASE, "Button enters release debounce on release");

    /* 测试 5：释放消抖完成，恢复 RELEASED 态 */
    evt = button_fsm_update(&tracker, false, 620, BTN_EVT_KEY1_SHORT, BTN_EVT_NONE);
    TEST_ASSERT(evt == BTN_EVT_NONE && tracker.state == BTN_STATE_RELEASED, "Button returned to RELEASED ready for next press");

    /* 测试 6：再次单次按下，立即触发第二次动作 (彻底消除需按两次的缺陷) */
    button_fsm_update(&tracker, true, 700, BTN_EVT_KEY1_SHORT, BTN_EVT_NONE);
    evt = button_fsm_update(&tracker, true, 720, BTN_EVT_KEY1_SHORT, BTN_EVT_NONE);
    TEST_ASSERT(evt == BTN_EVT_KEY1_SHORT && tracker.state == BTN_STATE_PRESSED, "Second single press immediately triggers cleanly");

    /* 测试 7：KEY2 双功能按键 - 短按测试 (按下 < 800ms 松手，抬起消抖后产生 KEY2_SHORT) */
    button_tracker_t tracker2 = {BTN_STATE_RELEASED, 0, 0, false};
    button_fsm_update(&tracker2, true, 1000, BTN_EVT_KEY2_SHORT, BTN_EVT_KEY2_LONG);
    evt = button_fsm_update(&tracker2, true, 1020, BTN_EVT_KEY2_SHORT, BTN_EVT_KEY2_LONG);
    TEST_ASSERT(evt == BTN_EVT_NONE && tracker2.state == BTN_STATE_PRESSED, "Dual-function button holds event pending on press");
    evt = button_fsm_update(&tracker2, false, 1220, BTN_EVT_KEY2_SHORT, BTN_EVT_KEY2_LONG);
    TEST_ASSERT(evt == BTN_EVT_NONE && tracker2.state == BTN_STATE_DEBOUNCE_RELEASE, "Enters release debounce on keyup");
    evt = button_fsm_update(&tracker2, false, 1240, BTN_EVT_KEY2_SHORT, BTN_EVT_KEY2_LONG);
    TEST_ASSERT(evt == BTN_EVT_KEY2_SHORT && tracker2.state == BTN_STATE_RELEASED, "Short press event fired cleanly upon release");

    /* 测试 8：KEY2 双功能按键 - 长按测试 (按住达到 800ms 阈值瞬时触发 KEY2_LONG) */
    button_fsm_update(&tracker2, true, 2000, BTN_EVT_KEY2_SHORT, BTN_EVT_KEY2_LONG);
    button_fsm_update(&tracker2, true, 2020, BTN_EVT_KEY2_SHORT, BTN_EVT_KEY2_LONG);
    evt = button_fsm_update(&tracker2, true, 2750, BTN_EVT_KEY2_SHORT, BTN_EVT_KEY2_LONG);
    TEST_ASSERT(evt == BTN_EVT_NONE && tracker2.state == BTN_STATE_PRESSED, "No long press before 800ms threshold");
    evt = button_fsm_update(&tracker2, true, 2825, BTN_EVT_KEY2_SHORT, BTN_EVT_KEY2_LONG);
    TEST_ASSERT(evt == BTN_EVT_KEY2_LONG && tracker2.state == BTN_STATE_LONG_HELD, "Long press event fired immediately when 800ms threshold reached");
    evt = button_fsm_update(&tracker2, true, 3200, BTN_EVT_KEY2_SHORT, BTN_EVT_KEY2_LONG);
    TEST_ASSERT(evt == BTN_EVT_NONE && tracker2.state == BTN_STATE_LONG_HELD, "No repeated events while continuing to hold");
    button_fsm_update(&tracker2, false, 3300, BTN_EVT_KEY2_SHORT, BTN_EVT_KEY2_LONG);
    evt = button_fsm_update(&tracker2, false, 3320, BTN_EVT_KEY2_SHORT, BTN_EVT_KEY2_LONG);
    TEST_ASSERT(evt == BTN_EVT_NONE && tracker2.state == BTN_STATE_RELEASED, "Release after long-press produces NO false short event");
}

/* =========================================================================
 * 3. 中央控制状态机与安全逻辑测试
 * ========================================================================= */
static void run_fan_fsm_tests(void)
{
    printf("\n=== 3. Central Control & Safety State Machine Unit Tests ===\n");

    fan_fsm_ctx_t ctx;
    fan_fsm_init(&ctx);

    /* 测试 1：初始默认直接运行状态 */
    TEST_ASSERT(ctx.sys_state == FAN_STATE_MANUAL_RUN, "Default operational state is MANUAL_RUN");
    TEST_ASSERT(ctx.target_speed == 40, "Default target speed is 40%");
    TEST_ASSERT(ctx.swing_mode == FAN_SWING_OFF, "Default swing is OFF");

    /* 测试 2：电源启停切换 */
    fan_event_t pwr_evt = {EVENT_TYPE_POWER_TOGGLE, 0, 0.0f, "TEST_PWR"};
    fan_fsm_dispatch_event(&ctx, &pwr_evt);
    TEST_ASSERT(ctx.sys_state == FAN_STATE_POWER_OFF, "First power toggle switches to POWER_OFF");
    TEST_ASSERT(ctx.target_speed == 0, "Speed drops to 0% on power off");

    fan_fsm_dispatch_event(&ctx, &pwr_evt);
    TEST_ASSERT(ctx.sys_state == FAN_STATE_MANUAL_RUN, "Second power toggle returns to MANUAL_RUN");
    TEST_ASSERT(ctx.target_speed == 40, "Speed resumes to 40%");

    /* 测试 3：急停保护优先权 */
    fan_event_t swing_evt = {EVENT_TYPE_SWING_TOGGLE, 0, 0.0f, "TEST_SWING"};
    fan_fsm_dispatch_event(&ctx, &swing_evt);
    TEST_ASSERT(ctx.swing_mode == FAN_SWING_CW, "Swing enabled CW");

    fan_event_t emg_evt = {EVENT_TYPE_EMERGENCY_STOP, 0, 0.0f, "TEST_EMG"};
    fan_fsm_dispatch_event(&ctx, &emg_evt);
    TEST_ASSERT(ctx.sys_state == FAN_STATE_POWER_OFF, "Emergency stop forces POWER_OFF");
    TEST_ASSERT(ctx.target_speed == 0, "Emergency stop forces speed 0%");
    TEST_ASSERT(ctx.swing_mode == FAN_SWING_OFF, "Emergency stop forces swing OFF");

    /* 测试 4：速度调节与边界限幅 */
    fan_fsm_dispatch_event(&ctx, &pwr_evt); /* 开机 40% */
    fan_event_t step_up = {EVENT_TYPE_SPEED_STEP, 50, 0.0f, "STEP_UP"};
    fan_fsm_dispatch_event(&ctx, &step_up);
    TEST_ASSERT(ctx.target_speed == 90, "Speed increased to 90%");

    fan_fsm_dispatch_event(&ctx, &step_up);
    TEST_ASSERT(ctx.target_speed == 100, "Speed clamped to maximum 100%");

    fan_event_t step_down = {EVENT_TYPE_SPEED_STEP, -120, 0.0f, "STEP_DOWN"};
    fan_fsm_dispatch_event(&ctx, &step_down);
    TEST_ASSERT(ctx.target_speed == 0, "Speed clamped to 0%");
    TEST_ASSERT(ctx.sys_state == FAN_STATE_POWER_OFF, "Speed 0% automatically enters POWER_OFF");

    /* 测试 5：温控自动调速模式曲线 */
    fan_fsm_dispatch_event(&ctx, &pwr_evt); /* 开机 */
    fan_event_t mode_evt = {EVENT_TYPE_MODE_TOGGLE, 0, 0.0f, "MODE_TOGGLE"};
    fan_fsm_dispatch_event(&ctx, &mode_evt);
    TEST_ASSERT(ctx.sys_state == FAN_STATE_AUTO_TEMP, "Entered AUTO_TEMP mode");

    fan_fsm_update_auto_temp(&ctx, 22.0f);
    TEST_ASSERT(ctx.target_speed == 0, "Temp 22C (<24C): Fan STOP (0%)");

    fan_fsm_update_auto_temp(&ctx, 25.0f);
    TEST_ASSERT(ctx.target_speed == 30, "Temp 25C (24-26C): Low speed (30%)");

    fan_fsm_update_auto_temp(&ctx, 27.0f);
    TEST_ASSERT(ctx.target_speed == 50, "Temp 27C (26-28C): Med speed (50%)");

    fan_fsm_update_auto_temp(&ctx, 29.0f);
    TEST_ASSERT(ctx.target_speed == 75, "Temp 29C (28-30C): High speed (75%)");

    fan_fsm_update_auto_temp(&ctx, 32.5f);
    TEST_ASSERT(ctx.target_speed == 100, "Temp 32.5C (>30C): Max speed (100%)");

    /* 测试 6：显式设置模式与摆头控制 */
    fan_event_t set_manu = {EVENT_TYPE_MODE_SET, (int16_t)FAN_STATE_MANUAL_RUN, 0.0f, "SET_MANU"};
    fan_fsm_dispatch_event(&ctx, &set_manu);
    TEST_ASSERT(ctx.sys_state == FAN_STATE_MANUAL_RUN, "Explicitly set to MANUAL_RUN");

    fan_event_t set_sw_off = {EVENT_TYPE_SWING_SET, 0, 0.0f, "SET_SW_OFF"};
    fan_fsm_dispatch_event(&ctx, &set_sw_off);
    TEST_ASSERT(ctx.swing_mode == FAN_SWING_OFF, "Explicitly set swing OFF");

    fan_event_t set_sw_on = {EVENT_TYPE_SWING_SET, 1, 0.0f, "SET_SW_ON"};
    fan_fsm_dispatch_event(&ctx, &set_sw_on);
    TEST_ASSERT(ctx.swing_mode == FAN_SWING_CW, "Explicitly set swing ON");

    uint8_t old_sw_spd = ctx.swing_speed_level;
    fan_event_t sw_spd_up = {EVENT_TYPE_SWING_SPEED_STEP, 1, 0.0f, "SW_SPD_UP"};
    fan_fsm_dispatch_event(&ctx, &sw_spd_up);
    TEST_ASSERT(ctx.swing_speed_level == old_sw_spd + 1, "Swing speed level incremented");
}

int main(void)
{
    printf("====================================================\n");
    printf("  Smart Fan Firmware Host Unit Test Suite           \n");
    printf("====================================================\n");

    run_voice_protocol_tests();
    run_button_fsm_tests();
    run_fan_fsm_tests();

    printf("\n====================================================\n");
    printf("  Test Summary: %d Run, %d Passed, %d Failed        \n",
           g_tests_run, g_tests_passed, g_tests_failed);
    printf("====================================================\n");

    return (g_tests_failed == 0) ? 0 : 1;
}
