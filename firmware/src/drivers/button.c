/**
 * @file button.c
 * @brief 独立按键消抖与长短按状态机实现
 */
#include "button.h"
#include <string.h>

#ifndef HOST_UNIT_TEST
#include "stm32f1xx_hal.h"
#include "config/pins.h"
#endif

/* 环形事件队列 (中断/主线程无锁环形队列) */
#define BTN_QUEUE_CAPACITY 8
static button_event_t g_btn_queue[BTN_QUEUE_CAPACITY];
static volatile uint8_t g_queue_head = 0;
static volatile uint8_t g_queue_tail = 0;
static volatile bool g_button_initialized = false;

#ifndef HOST_UNIT_TEST
static button_tracker_t g_tracker_key1 = {0};
static button_tracker_t g_tracker_key2 = {0};
static button_tracker_t g_tracker_enc_sw = {0};

static void push_event(button_event_t evt)
{
    if (evt == BTN_EVT_NONE) return;
    uint8_t next_head = (g_queue_head + 1) % BTN_QUEUE_CAPACITY;
    if (next_head != g_queue_tail) {
        g_btn_queue[g_queue_head] = evt;
        g_queue_head = next_head;
    }
}
#endif

button_event_t button_pop_event(void)
{
    if (g_queue_tail == g_queue_head) {
        return BTN_EVT_NONE;
    }
    button_event_t evt = g_btn_queue[g_queue_tail];
    g_queue_tail = (g_queue_tail + 1) % BTN_QUEUE_CAPACITY;
    return evt;
}

button_event_t button_fsm_update(button_tracker_t *tracker,
                                 bool is_pressed_raw,
                                 uint32_t now_ms,
                                 button_event_t short_evt,
                                 button_event_t long_evt)
{
    button_event_t generated = BTN_EVT_NONE;

    switch (tracker->state) {
    case BTN_STATE_RELEASED:
        if (is_pressed_raw) {
            tracker->state = BTN_STATE_DEBOUNCE_PRESS;
            tracker->last_transition_ms = now_ms;
            tracker->long_press_fired = false;
        }
        break;

    case BTN_STATE_DEBOUNCE_PRESS:
        if (!is_pressed_raw) {
            /* 抖动毛刺，退回释放态 */
            tracker->state = BTN_STATE_RELEASED;
        } else if ((now_ms - tracker->last_transition_ms) >= BTN_DEBOUNCE_MS) {
            /* 确认按下 */
            tracker->state = BTN_STATE_PRESSED;
            tracker->press_start_ms = now_ms;
            tracker->long_press_fired = false;
            if (long_evt == BTN_EVT_NONE) {
                /* 单功能按键（如KEY1开关机）：按下瞬间消抖完毕即触发，提供零延迟实体按键响应 */
                generated = short_evt;
            }
        }
        break;

    case BTN_STATE_PRESSED:
        if (!is_pressed_raw) {
            /* 抬起进入释放消抖 */
            tracker->state = BTN_STATE_DEBOUNCE_RELEASE;
            tracker->last_transition_ms = now_ms;
        } else if (long_evt != BTN_EVT_NONE) {
            /* 双功能按键：持续按住达到长按阈值，立即触发长按事件 */
            if ((now_ms - tracker->press_start_ms) >= BTN_LONG_PRESS_MS) {
                tracker->state = BTN_STATE_LONG_HELD;
                tracker->long_press_fired = true;
                generated = long_evt;
            }
        }
        break;

    case BTN_STATE_LONG_HELD:
        if (!is_pressed_raw) {
            /* 长按保持后抬起进入释放消抖 */
            tracker->state = BTN_STATE_DEBOUNCE_RELEASE;
            tracker->last_transition_ms = now_ms;
        }
        break;

    case BTN_STATE_DEBOUNCE_RELEASE:
        if (is_pressed_raw) {
            /* 释放过程再次变低（接触弹跳），回到对应按下态，不重复产生事件 */
            tracker->state = tracker->long_press_fired ? BTN_STATE_LONG_HELD : BTN_STATE_PRESSED;
        } else if ((now_ms - tracker->last_transition_ms) >= BTN_DEBOUNCE_MS) {
            /* 稳定释放超过消抖时间，完全复位为释放态 */
            tracker->state = BTN_STATE_RELEASED;
            if (long_evt != BTN_EVT_NONE && !tracker->long_press_fired) {
                /* 双功能按键（如KEY2短按摇头）：未触发长按即抬起，触发短按事件 */
                generated = short_evt;
            }
        }
        break;

    default:
        tracker->state = BTN_STATE_RELEASED;
        tracker->long_press_fired = false;
        break;
    }

    return generated;
}

#ifndef HOST_UNIT_TEST

void button_init(void)
{
    GPIO_InitTypeDef gpio = {0};

    __HAL_RCC_GPIOB_CLK_ENABLE();

    /* RevB PCB 独立大按键配置：
     * KEY1_POWER (PB13 开关机), KEY2_SWING (PB14 摇头/模式复用按键)
     * 注：RevB PCB采用5脚编码器无按键引脚，PB12严格悬空不启用 */
    gpio.Pin = KEY1_POWER_Pin | KEY2_SWING_Pin;
    gpio.Mode = GPIO_MODE_INPUT;
    gpio.Pull = GPIO_PULLUP;
    gpio.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOB, &gpio);

    memset(&g_tracker_key1, 0, sizeof(g_tracker_key1));
    memset(&g_tracker_key2, 0, sizeof(g_tracker_key2));
    memset(&g_tracker_enc_sw, 0, sizeof(g_tracker_enc_sw));
    g_queue_head = 0;
    g_queue_tail = 0;
    g_button_initialized = true;
}

void button_poll(uint32_t now_ms)
{
    if (!g_button_initialized) return;

    /* 读取当前引脚电平：低电平为按下 (true) */
    bool key1_pressed = (HAL_GPIO_ReadPin(KEY1_POWER_Port, KEY1_POWER_Pin) == GPIO_PIN_RESET);
    bool key2_pressed = (HAL_GPIO_ReadPin(KEY2_SWING_Port, KEY2_SWING_Pin) == GPIO_PIN_RESET);

    /* KEY1: 电源启停，单功能瞬时触发 (long_evt = BTN_EVT_NONE 提供零延迟手感) */
    button_event_t e1 = button_fsm_update(&g_tracker_key1, key1_pressed, now_ms,
                                          BTN_EVT_KEY1_SHORT, BTN_EVT_NONE);
    if (e1 != BTN_EVT_NONE) {
        push_event(e1);
    }

    /* KEY2: 双功能合并按键，短按摇头 (KEY2_SHORT) / 长按模式切换 (KEY2_LONG) */
    button_event_t e2 = button_fsm_update(&g_tracker_key2, key2_pressed, now_ms,
                                          BTN_EVT_KEY2_SHORT, BTN_EVT_KEY2_LONG);
    if (e2 != BTN_EVT_NONE) {
        push_event(e2);
    }
}

#endif
