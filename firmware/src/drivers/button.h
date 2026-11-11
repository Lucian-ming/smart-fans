/**
 * @file button.h
 * @brief 独立按键驱动 (PB13 KEY1电源, PB14 KEY2摇头)
 *
 * 特性：
 * - 纯非阻塞消抖状态机
 * - 独立识别短按与长按 (阈值可配)
 * - 核心状态机逻辑与底层解耦，支持宿主机单元测试
 * - 硬件锁定：PB13(KEY1), PB14(KEY2); PB12不启用
 */
#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    BTN_EVT_NONE = 0,
    BTN_EVT_KEY1_SHORT,
    BTN_EVT_KEY1_LONG,
    BTN_EVT_KEY2_SHORT,
    BTN_EVT_KEY2_LONG,
    BTN_EVT_ENC_SW_SHORT,
    BTN_EVT_ENC_SW_LONG
} button_event_t;

typedef enum {
    BTN_STATE_RELEASED = 0,
    BTN_STATE_DEBOUNCE_PRESS,
    BTN_STATE_PRESSED,
    BTN_STATE_LONG_HELD,
    BTN_STATE_DEBOUNCE_RELEASE
} btn_fsm_state_t;

typedef struct {
    btn_fsm_state_t state;
    uint32_t press_start_ms;
    uint32_t last_transition_ms;
    bool long_press_fired;
} button_tracker_t;

#define BTN_DEBOUNCE_MS     15U
#define BTN_LONG_PRESS_MS   800U

/* 状态机单步更新（供驱动及宿主机测试共用） */
button_event_t button_fsm_update(button_tracker_t *tracker,
                                 bool is_pressed_raw,
                                 uint32_t now_ms,
                                 button_event_t short_evt,
                                 button_event_t long_evt);

void button_init(void);
void button_poll(uint32_t now_ms);
button_event_t button_pop_event(void);

#ifdef __cplusplus
}
#endif
