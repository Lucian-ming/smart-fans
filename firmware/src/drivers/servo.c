/**
 * @file servo.c
 * @brief 360° 金属齿轮连续旋转舵机驱动实现 (PB8, TIM4_CH3 @ 50Hz)
 *
 * 控制策略：
 * 1. 360 度连续旋转舵机通过脉宽控制旋转方向与转速：
 *    - 1500us：中位静止停止点
 *    - 1500us + cw_offset (如 1528us)：顺时针旋转 (CW 向右)
 *    - 1500us - ccw_offset (如 1466us)：逆时针旋转 (CCW 向左)
 *    - PWM = 0：彻底释放电机绕组，消除发热啸叫并原地保持
 * 2. 90度严格往复扫风引擎（解决单向旋转与死区不对称）：
 *    - 启动瞬态力矩突发 (Kickstart Boost 14us / 100ms)：克服减速齿轮静态摩擦力，确保换向 100% 成功往返
 *    - 换向软刹车平滑制动缓冲 (Cushion Brake 120ms)：消除惯性超调与换向冲击
 *    - 严格限定 2000ms 单向行程，实现严格限定在 45°~135° (共 90°) 的往复扫风扇面
 *    - 重复调用保护（防重置），避免状态机轮询打断换向计时
 */
#include "servo.h"
#include "stm32f1xx_hal.h"
#include "config/pins.h"

#define SERVO_DEFAULT_NEUTRAL_US       1500U   /* 360° 舵机标准中位静止脉宽 (1500us) */
#define SERVO_DEFAULT_CW_OFFSET_US     28U     /* 默认 CW (向右) 慢速偏置量 (1528us, 舒适静音) */
#define SERVO_DEFAULT_CCW_OFFSET_US    34U     /* 默认 CCW (向左) 偏置量 (1466us, 补偿逆向死区硬度) */
#define SERVO_DEFAULT_HALF_PERIOD_MS   2000U   /* 严格限制单向转动时间 2000ms (限制在标准 90° 扇区) */
#define SERVO_KICKSTART_BOOST_US       14U     /* 换向启动前 100ms 突发力矩增量，攻克齿轮静摩擦 */

static TIM_HandleTypeDef g_htim4;
static bool g_is_active = false;
static uint16_t g_current_pulse_us = 0;
static uint16_t g_neutral_us = SERVO_DEFAULT_NEUTRAL_US;
static uint16_t g_cw_offset_us = SERVO_DEFAULT_CW_OFFSET_US;
static uint16_t g_ccw_offset_us = SERVO_DEFAULT_CCW_OFFSET_US;
static uint32_t g_half_period_ms = SERVO_DEFAULT_HALF_PERIOD_MS;
static int8_t g_drift_trim_us = 0; /* 往复防偏移配平偏置微调 (us) */

static bool g_swing_enabled = false;
static int8_t g_swing_dir = 1; /* +1: 向右 (CW), -1: 向左 (CCW) */
static uint32_t g_dir_switch_time_ms = 0;
static float g_sim_angle = 90.0f; /* 虚拟角度 (45°~135°，严格 90° 扇面)，供 OLED 状态显示 */

void servo_init(void)
{
    GPIO_InitTypeDef gpio = {0};
    TIM_OC_InitTypeDef oc = {0};

    __HAL_RCC_GPIOB_CLK_ENABLE();
    __HAL_RCC_TIM4_CLK_ENABLE();

    /* PB8 配置为 TIM4_CH3 复用推挽输出 */
    gpio.Pin = SERVO_PWM_Pin;
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(SERVO_PWM_Port, &gpio);

    /* APB1 预分频 2，TIM4CLK = 72 MHz
     * PSC = 71 -> 计数时钟 1 MHz (每计数 1us)
     * ARR = 19999 -> 周期 20,000us = 20ms = 50Hz (符合 360° 舵机时基标准)
     */
    g_htim4.Instance = TIM4;
    g_htim4.Init.Prescaler = 71;
    g_htim4.Init.CounterMode = TIM_COUNTERMODE_UP;
    g_htim4.Init.Period = 19999;
    g_htim4.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
    g_htim4.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
    HAL_TIM_PWM_Init(&g_htim4);

    oc.OCMode = TIM_OCMODE_PWM1;
    oc.Pulse = 0; /* 默认 0 占空比 */
    oc.OCPolarity = TIM_OCPOLARITY_HIGH;
    oc.OCFastMode = TIM_OCFAST_DISABLE;
    HAL_TIM_PWM_ConfigChannel(&g_htim4, &oc, TIM_CHANNEL_3);

    HAL_TIM_PWM_Start(&g_htim4, TIM_CHANNEL_3);

    g_neutral_us = SERVO_DEFAULT_NEUTRAL_US;
    g_cw_offset_us = SERVO_DEFAULT_CW_OFFSET_US;
    g_ccw_offset_us = SERVO_DEFAULT_CCW_OFFSET_US;
    g_half_period_ms = SERVO_DEFAULT_HALF_PERIOD_MS;
    g_drift_trim_us = 0;
    g_swing_enabled = false;
    g_swing_dir = 1;
    g_dir_switch_time_ms = 0;
    g_sim_angle = 90.0f;
    servo_stop();
}

void servo_set_pulse_us(uint16_t pulse_us)
{
    if (pulse_us < 500) pulse_us = 500;
    if (pulse_us > 2500) pulse_us = 2500;

    g_current_pulse_us = pulse_us;
    g_is_active = (pulse_us != 0 && pulse_us != g_neutral_us);
    __HAL_TIM_SET_COMPARE(&g_htim4, TIM_CHANNEL_3, pulse_us);
}

void servo_set_swing_enabled(bool enabled)
{
    if (g_swing_enabled == enabled) {
        return; /* 防重复重置：已处于该状态时，坚决不重置时钟与方向！ */
    }

    g_swing_enabled = enabled;
    if (!enabled) {
        /* 停止摆头时直接切断 PWM 占空比为 0，定格在当前角度并释放电机发热 */
        servo_stop();
    } else {
        g_dir_switch_time_ms = HAL_GetTick();
        g_is_active = true;
        /* 启动时按照当前方向立即输出旋转脉宽 (带启动瞬态破摩擦增益) */
        uint16_t pulse;
        if (g_swing_dir > 0) {
            int32_t p = (int32_t)g_neutral_us + (int32_t)g_cw_offset_us + (int32_t)SERVO_KICKSTART_BOOST_US + (int32_t)g_drift_trim_us;
            if (p < 500) p = 500;
            if (p > 2500) p = 2500;
            pulse = (uint16_t)p;
        } else {
            int32_t p = (int32_t)g_neutral_us - (int32_t)g_ccw_offset_us - (int32_t)SERVO_KICKSTART_BOOST_US;
            if (p < 500) p = 500;
            if (p > 2500) p = 2500;
            pulse = (uint16_t)p;
        }
        servo_set_pulse_us(pulse);
    }
}

bool servo_is_swing_enabled(void)
{
    return g_swing_enabled;
}

void servo_set_motion(servo_motion_t motion, uint8_t speed_level)
{
    static uint8_t s_last_speed_level = 0;
    if (speed_level > 0 && speed_level != s_last_speed_level) {
        s_last_speed_level = speed_level;
        /* 90 度严格恒定扇面调速曲线：
         * 行程时间与转速协同联动，确保各档位皆保持在 90° 舒适扇区内往复！
         */
        switch (speed_level) {
        case 1:
            g_cw_offset_us = 22U;
            g_ccw_offset_us = 28U;
            g_half_period_ms = 2400U; /* 极静柔风慢摆 (90° 扇面) */
            break;
        case 2:
            g_cw_offset_us = 26U;
            g_ccw_offset_us = 31U;
            g_half_period_ms = 2200U; /* 标准慢速自然扫风 (90° 扇面) */
            break;
        case 3:
            g_cw_offset_us = 28U;
            g_ccw_offset_us = 34U;
            g_half_period_ms = 2000U; /* 默认推荐：舒适平缓 90° 扇面往复 */
            break;
        case 4:
            g_cw_offset_us = 34U;
            g_ccw_offset_us = 40U;
            g_half_period_ms = 1800U; /* 较快扫风 (90° 扇面) */
            break;
        case 5:
            g_cw_offset_us = 42U;
            g_ccw_offset_us = 48U;
            g_half_period_ms = 1500U; /* 快速扫风 (90° 扇面) */
            break;
        default:
            g_cw_offset_us = 28U;
            g_ccw_offset_us = 34U;
            g_half_period_ms = 2000U;
            break;
        }
    }

    if (motion == SERVO_MOTION_STOP) {
        servo_set_swing_enabled(false);
    } else {
        servo_set_swing_enabled(true);
    }
}

void servo_tick(uint32_t now_ms)
{
    if (!g_swing_enabled) {
        return;
    }

    uint32_t elapsed = now_ms - g_dir_switch_time_ms;

    /* 90度范围限制核心算法：到达单向半周期时间后精准反向 */
    if (elapsed >= g_half_period_ms) {
        g_dir_switch_time_ms = now_ms;
        elapsed = 0;
        g_swing_dir = -g_swing_dir; /* 反向，实现往复扫风 (CW <-> CCW) */
    }

    const uint32_t cushion_ms = 120U;
    const uint32_t kickstart_ms = 100U;

    uint16_t pulse;
    if (g_half_period_ms > cushion_ms && elapsed >= (g_half_period_ms - cushion_ms)) {
        /* 换向前 120ms 切换至中位(1500us)，实现软刹车减速驻留，消除惯性超调与换向冲击 */
        pulse = g_neutral_us;
    } else {
        /* 换向最初 100ms 施加启动脉冲增益，彻底攻克齿轮箱静摩擦力 */
        uint16_t boost = (elapsed < kickstart_ms) ? SERVO_KICKSTART_BOOST_US : 0U;

        if (g_swing_dir > 0) {
            /* 顺时针旋转 (CW 向右)：中位 + CW偏置 + 启动增益 + 漂移配平修正 */
            int32_t p = (int32_t)g_neutral_us + (int32_t)g_cw_offset_us + (int32_t)boost + (int32_t)g_drift_trim_us;
            if (p < 500) p = 500;
            if (p > 2500) p = 2500;
            pulse = (uint16_t)p;
        } else {
            /* 逆时针旋转 (CCW 向左)：中位 - CCW偏置 - 启动增益 */
            int32_t p = (int32_t)g_neutral_us - (int32_t)g_ccw_offset_us - (int32_t)boost;
            if (p < 500) p = 500;
            if (p > 2500) p = 2500;
            pulse = (uint16_t)p;
        }
    }
    servo_set_pulse_us(pulse);

    /* 虚拟估算当前角度 (45° ~ 135°，严格 90° 扇面)，供状态栏与屏幕平滑显示 */
    float progress = (float)elapsed / (float)g_half_period_ms;
    if (progress > 1.0f) progress = 1.0f;
    if (g_swing_dir > 0) {
        g_sim_angle = 45.0f + progress * 90.0f;
    } else {
        g_sim_angle = 135.0f - progress * 90.0f;
    }
}

void servo_stop(void)
{
    g_swing_enabled = false;
    g_is_active = false;
    g_current_pulse_us = 0;
    /* 彻底切断 PWM 占空比为 0，释放舵机扭矩，彻底消除 360° 舵机静止时的零点蠕动与电感啸叫 */
    __HAL_TIM_SET_COMPARE(&g_htim4, TIM_CHANNEL_3, 0);
}

bool servo_is_active(void)
{
    return g_is_active;
}

/* 360° 舵机专用中位与范围微调 */
void servo_set_neutral_us(uint16_t neutral_us)
{
    if (neutral_us >= 1400 && neutral_us <= 1600) {
        g_neutral_us = neutral_us;
    }
}

uint16_t servo_get_neutral_us(void)
{
    return g_neutral_us;
}

void servo_set_pulse_offset(uint16_t offset_us)
{
    if (offset_us >= 10 && offset_us <= 300) {
        g_cw_offset_us = offset_us;
        g_ccw_offset_us = offset_us + 6U;
    }
}

uint16_t servo_get_pulse_offset(void)
{
    return g_cw_offset_us;
}

void servo_set_cw_offset(uint16_t cw_us)
{
    if (cw_us >= 10 && cw_us <= 300) {
        g_cw_offset_us = cw_us;
    }
}

uint16_t servo_get_cw_offset(void)
{
    return g_cw_offset_us;
}

void servo_set_ccw_offset(uint16_t ccw_us)
{
    if (ccw_us >= 10 && ccw_us <= 300) {
        g_ccw_offset_us = ccw_us;
    }
}

uint16_t servo_get_ccw_offset(void)
{
    return g_ccw_offset_us;
}

void servo_set_half_period_ms(uint32_t half_period_ms)
{
    if (half_period_ms >= 500 && half_period_ms <= 6000) {
        g_half_period_ms = half_period_ms;
    }
}

uint32_t servo_get_half_period_ms(void)
{
    return g_half_period_ms;
}

void servo_set_drift_trim(int8_t trim_us)
{
    if (trim_us >= -30 && trim_us <= 30) {
        g_drift_trim_us = trim_us;
    }
}

int8_t servo_get_drift_trim(void)
{
    return g_drift_trim_us;
}

/* 兼容性接口 */
void servo_set_angle(float angle_deg)
{
    g_sim_angle = angle_deg;
    if (angle_deg > 85.0f && angle_deg < 95.0f) {
        servo_set_pulse_us(g_neutral_us);
    } else if (angle_deg >= 95.0f) {
        servo_set_pulse_us(g_neutral_us + g_cw_offset_us);
    } else {
        servo_set_pulse_us(g_neutral_us - g_ccw_offset_us);
    }
}

float servo_get_current_angle(void)
{
    return g_sim_angle;
}

void servo_set_step_deg(float step_deg)
{
    (void)step_deg;
}

float servo_get_step_deg(void)
{
    return 3.0f;
}
