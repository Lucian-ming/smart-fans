/**
 * @file fan_fsm.c
 * @brief 智能风扇中央事件与安全控制状态机实现
 */
#include "fan_fsm.h"
#include <string.h>
#include <stdio.h>

#ifndef HOST_UNIT_TEST
#include "drivers/motor.h"
#include "drivers/servo.h"
#include "drivers/buzzer.h"
#include "drivers/ssd1306.h"
#endif

void fan_fsm_init(fan_fsm_ctx_t *ctx)
{
    memset(ctx, 0, sizeof(*ctx));
    ctx->sys_state = FAN_STATE_MANUAL_RUN; /* 默认直接就绪运行 */
    ctx->target_speed = 40;                /* 默认起步柔和风速 40% */
    ctx->actual_speed = 0;                 /* 从 0 平滑渐增 */
    ctx->swing_mode = FAN_SWING_OFF;
    ctx->swing_speed_level = 3;            /* 默认采用快速扫风档位 (160°/s) */
    ctx->current_temperature = 25.0f;
    ctx->current_humidity = 50.0f;
    strncpy(ctx->last_event_desc, "POWER_ON", sizeof(ctx->last_event_desc) - 1);
}

void fan_fsm_update_auto_temp(fan_fsm_ctx_t *ctx, float temp)
{
    ctx->current_temperature = temp;
    if (ctx->sys_state != FAN_STATE_AUTO_TEMP) return;

    /* 温控温区分级曲线：
     * < 24°C: 停转 (0%)
     * 24 ~ 26°C: 低速微风 (30%)
     * 26 ~ 28°C: 中速柔风 (50%)
     * 28 ~ 30°C: 高速劲风 (75%)
     * > 30°C: 满载极速 (100%)
     */
    if (temp < 24.0f) {
        ctx->target_speed = 0;
    } else if (temp < 26.0f) {
        ctx->target_speed = 30;
    } else if (temp < 28.0f) {
        ctx->target_speed = 50;
    } else if (temp < 30.0f) {
        ctx->target_speed = 75;
    } else {
        ctx->target_speed = 100;
    }
}

void fan_fsm_dispatch_event(fan_fsm_ctx_t *ctx, const fan_event_t *evt)
{
    if (evt == NULL || evt->type == EVENT_TYPE_NONE) return;

    /* 只有用户操作或执行器动作才更新显示事件，背景传感器周期轮询(如DHT11)不覆盖用户交互显示 */
    if (evt->source && evt->type != EVENT_TYPE_TEMP_UPDATE) {
        snprintf(ctx->last_event_desc, sizeof(ctx->last_event_desc), "%s", evt->source);
    }

    switch (evt->type) {
    case EVENT_TYPE_EMERGENCY_STOP:
        ctx->sys_state = FAN_STATE_POWER_OFF;
        ctx->target_speed = 0;
        ctx->actual_speed = 0;
        ctx->swing_mode = FAN_SWING_OFF;
        break;

    case EVENT_TYPE_POWER_TOGGLE:
        if (ctx->sys_state == FAN_STATE_POWER_OFF) {
            ctx->sys_state = FAN_STATE_MANUAL_RUN;
            ctx->target_speed = 40; /* 默认启动开机档位 40% */
            snprintf(ctx->last_event_desc, sizeof(ctx->last_event_desc), "POWER ON (40%%)");
        } else {
            ctx->sys_state = FAN_STATE_POWER_OFF;
            ctx->target_speed = 0;
            ctx->swing_mode = FAN_SWING_OFF;
            snprintf(ctx->last_event_desc, sizeof(ctx->last_event_desc), "POWER OFF");
        }
        break;

    case EVENT_TYPE_MODE_TOGGLE:
        if (ctx->sys_state == FAN_STATE_POWER_OFF) {
            ctx->sys_state = FAN_STATE_AUTO_TEMP;
            fan_fsm_update_auto_temp(ctx, ctx->current_temperature);
            snprintf(ctx->last_event_desc, sizeof(ctx->last_event_desc), "MODE: AUTO_TEMP");
        } else if (ctx->sys_state == FAN_STATE_MANUAL_RUN) {
            ctx->sys_state = FAN_STATE_AUTO_TEMP;
            fan_fsm_update_auto_temp(ctx, ctx->current_temperature);
            snprintf(ctx->last_event_desc, sizeof(ctx->last_event_desc), "MODE: AUTO_TEMP");
        } else if (ctx->sys_state == FAN_STATE_AUTO_TEMP) {
            ctx->sys_state = FAN_STATE_MANUAL_RUN;
            if (ctx->target_speed == 0) {
                ctx->target_speed = 40; /* 切回手动模式时，若之前温控停转则恢复基础起步档位 40% */
            }
            snprintf(ctx->last_event_desc, sizeof(ctx->last_event_desc), "MODE: MANUAL");
        }
        break;

    case EVENT_TYPE_MODE_SET:
        if (evt->param == (int16_t)FAN_STATE_AUTO_TEMP) {
            ctx->sys_state = FAN_STATE_AUTO_TEMP;
            fan_fsm_update_auto_temp(ctx, ctx->current_temperature);
            snprintf(ctx->last_event_desc, sizeof(ctx->last_event_desc), "MODE: AUTO_TEMP");
        } else if (evt->param == (int16_t)FAN_STATE_MANUAL_RUN) {
            ctx->sys_state = FAN_STATE_MANUAL_RUN;
            if (ctx->target_speed == 0) {
                ctx->target_speed = 40;
            }
            snprintf(ctx->last_event_desc, sizeof(ctx->last_event_desc), "MODE: MANUAL");
        }
        break;

    case EVENT_TYPE_SWING_TOGGLE:
        if (ctx->sys_state == FAN_STATE_POWER_OFF) {
            /* 关机态下忽略摇头，保证安全 */
            break;
        }
        /* 单键单次切换：OFF <-> ON，彻底解决多档位需连击的迟滞体验 */
        if (ctx->swing_mode == FAN_SWING_OFF) {
            ctx->swing_mode = FAN_SWING_CW;
            snprintf(ctx->last_event_desc, sizeof(ctx->last_event_desc), "SWING: ON");
        } else {
            ctx->swing_mode = FAN_SWING_OFF;
            snprintf(ctx->last_event_desc, sizeof(ctx->last_event_desc), "SWING: OFF");
        }
        break;

    case EVENT_TYPE_SWING_SET:
        if (ctx->sys_state == FAN_STATE_POWER_OFF) {
            break;
        }
        if (evt->param > 0) {
            ctx->swing_mode = FAN_SWING_CW;
            snprintf(ctx->last_event_desc, sizeof(ctx->last_event_desc), "SWING: ON");
        } else {
            ctx->swing_mode = FAN_SWING_OFF;
            snprintf(ctx->last_event_desc, sizeof(ctx->last_event_desc), "SWING: OFF");
        }
        break;

    case EVENT_TYPE_SWING_SPEED_STEP:
        {
            int16_t lvl = (int16_t)ctx->swing_speed_level + evt->param;
            if (lvl < 1) lvl = 1;
            if (lvl > 5) lvl = 5;
            ctx->swing_speed_level = (uint8_t)lvl;
            snprintf(ctx->last_event_desc, sizeof(ctx->last_event_desc), "SW SPD: %d", ctx->swing_speed_level);
        }
        break;

    case EVENT_TYPE_SPEED_STEP:
        if (ctx->sys_state == FAN_STATE_POWER_OFF) {
            if (evt->param > 0) {
                ctx->sys_state = FAN_STATE_MANUAL_RUN;
                ctx->target_speed = (int8_t)evt->param;
                snprintf(ctx->last_event_desc, sizeof(ctx->last_event_desc), "SPEED: %d%%", ctx->target_speed);
            }
            break;
        }
        if (ctx->sys_state == FAN_STATE_AUTO_TEMP) {
            /* 人工调节速度自动切回手动模式 */
            ctx->sys_state = FAN_STATE_MANUAL_RUN;
        }
        {
            int16_t next = (int16_t)ctx->target_speed + evt->param;
            if (next > 100) next = 100;
            if (next < 0) next = 0;
            ctx->target_speed = (int8_t)next;
            snprintf(ctx->last_event_desc, sizeof(ctx->last_event_desc), "SPEED: %d%%", ctx->target_speed);
            if (ctx->target_speed == 0) {
                ctx->sys_state = FAN_STATE_POWER_OFF;
                ctx->swing_mode = FAN_SWING_OFF;
                snprintf(ctx->last_event_desc, sizeof(ctx->last_event_desc), "POWER OFF");
            }
        }
        break;

    case EVENT_TYPE_SPEED_SET:
        {
            int16_t val = evt->param;
            if (val > 100) val = 100;
            if (val < 0) val = 0;
            ctx->target_speed = (int8_t)val;
            if (ctx->target_speed > 0) {
                ctx->sys_state = FAN_STATE_MANUAL_RUN;
            } else {
                ctx->sys_state = FAN_STATE_POWER_OFF;
                ctx->swing_mode = FAN_SWING_OFF;
            }
        }
        break;

    case EVENT_TYPE_TEMP_UPDATE:
        ctx->current_temperature = evt->float_param;
        if (ctx->sys_state == FAN_STATE_AUTO_TEMP) {
            fan_fsm_update_auto_temp(ctx, ctx->current_temperature);
        }
        break;

    default:
        break;
    }
}

#ifndef HOST_UNIT_TEST

#define EVENT_QUEUE_SIZE 16
static fan_event_t g_event_queue[EVENT_QUEUE_SIZE];
static uint8_t g_q_head = 0;
static uint8_t g_q_tail = 0;

static fan_fsm_ctx_t g_app_ctx;
static uint32_t g_last_ramp_ms = 0;

void app_fsm_init(void)
{
    fan_fsm_init(&g_app_ctx);
    g_q_head = 0;
    g_q_tail = 0;
    g_last_ramp_ms = 0;

    /* 确保硬件执行器处于关断安全态 */
    motor_emergency_stop();
    servo_stop();
    buzzer_set(false);
}

void app_fsm_post_event(const fan_event_t *evt)
{
    if (evt == NULL || evt->type == EVENT_TYPE_NONE) return;

    uint8_t next = (g_q_head + 1) % EVENT_QUEUE_SIZE;
    if (next != g_q_tail) {
        g_event_queue[g_q_head] = *evt;
        g_q_head = next;
    }
}

void app_fsm_set_humidity(float humi)
{
    g_app_ctx.current_humidity = humi;
}

const fan_fsm_ctx_t* app_fsm_get_context(void)
{
    return &g_app_ctx;
}

void app_fsm_tick(uint32_t now_ms)
{
    /* 1. 处理队列中的事件 */
    while (g_q_tail != g_q_head) {
        fan_event_t evt = g_event_queue[g_q_tail];
        g_q_tail = (g_q_tail + 1) % EVENT_QUEUE_SIZE;
        fan_fsm_dispatch_event(&g_app_ctx, &evt);
    }

    /* 2. 平滑加减速斜坡 (每 20ms 渐变 2%)，防止瞬态电流冲击面包板供电 */
    if (now_ms - g_last_ramp_ms >= 20U) {
        g_last_ramp_ms = now_ms;
        if (g_app_ctx.actual_speed < g_app_ctx.target_speed) {
            int16_t next = (int16_t)g_app_ctx.actual_speed + 2;
            if (next > g_app_ctx.target_speed) next = g_app_ctx.target_speed;
            g_app_ctx.actual_speed = (int8_t)next;
        } else if (g_app_ctx.actual_speed > g_app_ctx.target_speed) {
            int16_t next = (int16_t)g_app_ctx.actual_speed - 2;
            if (next < g_app_ctx.target_speed) next = g_app_ctx.target_speed;
            g_app_ctx.actual_speed = (int8_t)next;
        }

        /* 3. 同步到底层硬件执行器 */
        if (g_app_ctx.sys_state == FAN_STATE_POWER_OFF && g_app_ctx.actual_speed == 0) {
            motor_emergency_stop();
        } else {
            motor_set_speed(g_app_ctx.actual_speed);
        }

        static fan_swing_mode_t s_last_swing_mode = FAN_SWING_OFF;
        static uint8_t s_last_swing_level = 0;
        if (g_app_ctx.swing_mode != s_last_swing_mode || g_app_ctx.swing_speed_level != s_last_swing_level) {
            s_last_swing_mode = g_app_ctx.swing_mode;
            s_last_swing_level = g_app_ctx.swing_speed_level;
            if (g_app_ctx.swing_mode == FAN_SWING_CW) {
                servo_set_motion(SERVO_MOTION_CW, g_app_ctx.swing_speed_level);
            } else if (g_app_ctx.swing_mode == FAN_SWING_CCW) {
                servo_set_motion(SERVO_MOTION_CCW, g_app_ctx.swing_speed_level);
            } else {
                servo_set_motion(SERVO_MOTION_STOP, 0);
            }
        }
    }
}

#endif
