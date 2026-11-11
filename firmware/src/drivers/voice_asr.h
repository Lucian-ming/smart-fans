/**
 * @file voice_asr.h
 * @brief ASR-PRO 离线语音模块驱动 (USART2: PA2 TX, PA3 RX @ 115200 8N1)
 *
 * 协议依据：
 * - 结合 references/01_bishe_voice_fan/智能语音风扇.hd 提取的标准指令集：
 *   接收指令: "FON\r\n", "FOFF\r\n", "F+\r\n", "F-\r\n", "FMAX\r\n", "FMOD\r\n", "FMIN\r\n", "INIT\r\n"
 *   应答反馈: "Fyes\r\n" (风扇开启), "Foff\r\n" (风扇关闭)
 * - 完备环形缓冲与硬件异常状态恢复 (ORE/NE/FE 清标志)
 * - 核心帧解析函数可独立在宿主机进行单元测试
 */
#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    VOICE_CMD_NONE = 0,
    VOICE_CMD_WAKEUP,          /* "INIT" */
    VOICE_CMD_FAN_ON,          /* "FON" */
    VOICE_CMD_FAN_OFF,         /* "FOFF" */
    VOICE_CMD_SPEED_UP,        /* "F+" */
    VOICE_CMD_SPEED_DOWN,      /* "F-" */
    VOICE_CMD_SPEED_MAX,       /* "FMAX" */
    VOICE_CMD_SPEED_MED,       /* "FMOD" */
    VOICE_CMD_SPEED_MIN,       /* "FMIN" */
    VOICE_CMD_MODE_TOGGLE,     /* "FMODE" */
    VOICE_CMD_MODE_AUTO,       /* "FAUTO" */
    VOICE_CMD_MODE_MANUAL,     /* "FMANU" / "FMANUAL" */
    VOICE_CMD_SWING_ON,        /* "SWON" */
    VOICE_CMD_SWING_OFF,       /* "SWOFF" */
    VOICE_CMD_SWING_TOGGLE,    /* "SWTOG" */
    VOICE_CMD_SWING_SPEED_UP,  /* "SW+" */
    VOICE_CMD_SWING_SPEED_DOWN,/* "SW-" */
    VOICE_CMD_LIGHT_ON,        /* "LON" */
    VOICE_CMD_LIGHT_OFF,       /* "LOFF" */
    VOICE_CMD_SLEEP,           /* "FSLEEP" - 睡眠微风模式 */
    VOICE_CMD_QUERY_TEMP,      /* "QTEMP" - 查询温湿度 */
    VOICE_CMD_QUERY_STATUS     /* "QSTAT" - 查询运行状态 */
} voice_cmd_t;

#define VOICE_RING_BUF_SIZE 128

typedef struct {
    uint8_t buffer[VOICE_RING_BUF_SIZE];
    volatile uint16_t head;
    volatile uint16_t tail;
    volatile uint32_t rx_overflow_count;
} voice_ring_buf_t;

/* 帧解析核心逻辑（供驱动及单元测试共用） */
voice_cmd_t voice_parse_command_line(const char *line);
bool voice_ring_push(voice_ring_buf_t *rb, uint8_t byte);
bool voice_ring_pop(voice_ring_buf_t *rb, uint8_t *byte);
bool voice_extract_line(voice_ring_buf_t *rb, char *out_line, uint16_t max_len);

void voice_asr_init(void);
void voice_asr_poll(void);
voice_cmd_t voice_asr_pop_command(void);
void voice_asr_send_ack(const char *ack_str);

#ifdef __cplusplus
}
#endif
