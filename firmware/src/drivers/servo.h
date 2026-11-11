/**
 * @file servo.h
 * @brief 360° 金属齿轮连续旋转舵机驱动 (PB8, TIM4_CH3 @ 50Hz)
 *
 * 规格与控制原理：
 * - 控制周期：20ms (50Hz 时基)
 * - 脉宽控制转速与方向（连续旋转）：
 *   - 1500us：中位停止（电机不转）
 *   - > 1500us (如 1600us)：顺时针旋转 (CW / 向右摆头)，偏离越大转速越快
 *   - < 1500us (如 1400us)：逆时针旋转 (CCW / 向左摆头)，偏离越大转速越快
 *   - PWM 占空比 0：彻底释放电机绕组，消除啸叫发热并定点停格
 * - 角度范围限制（软件时序往复保护）：
 *   - 通过精准半周期定时器 (T_half) 严格限制单向旋转时间，实现 90°~120° 限制范围往复扫风
 *   - 彻底防止 360° 无限旋转导致风扇内部引线绞断
 */
#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    SERVO_MOTION_STOP = 0,
    SERVO_MOTION_CW,       /* 顺时针旋转 / 扫风 */
    SERVO_MOTION_CCW       /* 逆时针旋转 */
} servo_motion_t;

void servo_init(void);
void servo_set_pulse_us(uint16_t pulse_us);
void servo_set_swing_enabled(bool enabled);
bool servo_is_swing_enabled(void);
void servo_set_motion(servo_motion_t motion, uint8_t speed_level);
void servo_tick(uint32_t now_ms);
void servo_stop(void);
bool servo_is_active(void);

/* 360° 舵机中位与范围限制参数微调接口 */
void servo_set_neutral_us(uint16_t neutral_us);
uint16_t servo_get_neutral_us(void);
void servo_set_pulse_offset(uint16_t offset_us);
uint16_t servo_get_pulse_offset(void);
void servo_set_cw_offset(uint16_t cw_us);
uint16_t servo_get_cw_offset(void);
void servo_set_ccw_offset(uint16_t ccw_us);
uint16_t servo_get_ccw_offset(void);
void servo_set_half_period_ms(uint32_t half_period_ms);
uint32_t servo_get_half_period_ms(void);
void servo_set_drift_trim(int8_t trim_us);
int8_t servo_get_drift_trim(void);

/* 兼容接口 */
void servo_set_angle(float angle_deg);
float servo_get_current_angle(void);
void servo_set_step_deg(float step_deg);
float servo_get_step_deg(void);

#ifdef __cplusplus
}
#endif
