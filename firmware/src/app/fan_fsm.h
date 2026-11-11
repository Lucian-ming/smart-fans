/**
 * @file fan_fsm.h
 * @brief 智能风扇中央事件与安全控制状态机
 *
 * 设计目标：
 * - 统一接收来自按键、旋钮、手势、语音、串口命令的所有输入事件
 * - 严格裁决状态转换，彻底杜绝多个外设驱动直接争抢/直接写入 PWM 寄存器
 * - 状态机核心逻辑与 HAL 解耦，支持宿主机进行完整的自动化单元测试
 */
#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    FAN_STATE_POWER_OFF = 0, /* 安全待机：STBY低、PWM 0%、舵机停止 */
    FAN_STATE_MANUAL_RUN,    /* 手动调速运行 */
    FAN_STATE_AUTO_TEMP,     /* 温控自动调速模式 */
    FAN_STATE_TEST_MODE      /* 独立模块测试模式 (执行器由调试命令显式触发) */
} fan_system_state_t;

typedef enum {
    FAN_SWING_OFF = 0,
    FAN_SWING_CW,
    FAN_SWING_CCW
} fan_swing_mode_t;

typedef enum {
    EVENT_TYPE_NONE = 0,
    EVENT_TYPE_POWER_TOGGLE,
    EVENT_TYPE_MODE_TOGGLE,
    EVENT_TYPE_MODE_SET,     /* int16_t param: 目标模式 (FAN_STATE_MANUAL_RUN / FAN_STATE_AUTO_TEMP) */
    EVENT_TYPE_SWING_TOGGLE,
    EVENT_TYPE_SWING_SET,    /* int16_t param: 1(开启) / 0(关闭) */
    EVENT_TYPE_SWING_SPEED_STEP, /* int16_t param: +1(加速) / -1(减速) */
    EVENT_TYPE_SPEED_STEP,   /* int8_t param: 步进百分比 (+10, -10等) */
    EVENT_TYPE_SPEED_SET,    /* int8_t param: 绝对速度 (0~100) */
    EVENT_TYPE_EMERGENCY_STOP,
    EVENT_TYPE_TEMP_UPDATE   /* float param: 当前温度 */
} fan_event_type_t;

typedef struct {
    fan_event_type_t type;
    int16_t param;
    float float_param;
    const char *source;
} fan_event_t;

typedef struct {
    fan_system_state_t sys_state;
    int8_t target_speed;     /* 0 ~ 100% */
    int8_t actual_speed;     /* 平滑渐变当前速度 */
    fan_swing_mode_t swing_mode;
    uint8_t swing_speed_level; /* 1 ~ 5 */
    float current_temperature;
    float current_humidity;
    char last_event_desc[24];
} fan_fsm_ctx_t;

/* 核心状态机逻辑处理（宿主机单元测试共享） */
void fan_fsm_init(fan_fsm_ctx_t *ctx);
void fan_fsm_dispatch_event(fan_fsm_ctx_t *ctx, const fan_event_t *evt);
void fan_fsm_update_auto_temp(fan_fsm_ctx_t *ctx, float temp);

/* 目标板运行时控制接口 */
void app_fsm_init(void);
void app_fsm_post_event(const fan_event_t *evt);
void app_fsm_set_humidity(float humi);
void app_fsm_tick(uint32_t now_ms);
const fan_fsm_ctx_t* app_fsm_get_context(void);

#ifdef __cplusplus
}
#endif
