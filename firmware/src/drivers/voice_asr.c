/**
 * @file voice_asr.c
 * @brief ASR-PRO 离线语音模块驱动与协议解析实现
 */
#include "voice_asr.h"
#include <string.h>
#include <ctype.h>

#ifndef HOST_UNIT_TEST
#include "stm32f1xx_hal.h"
#include "config/pins.h"
#include "app/cli_test.h"
extern UART_HandleTypeDef g_uart1;
extern uint8_t g_cli_rx_byte;
#endif

/* 环形缓冲区通用函数 */
bool voice_ring_push(voice_ring_buf_t *rb, uint8_t byte)
{
    uint16_t next = (rb->head + 1) % VOICE_RING_BUF_SIZE;
    if (next == rb->tail) {
        rb->rx_overflow_count++;
        return false; /* 缓冲区满溢出 */
    }
    rb->buffer[rb->head] = byte;
    rb->head = next;
    return true;
}

bool voice_ring_pop(voice_ring_buf_t *rb, uint8_t *byte)
{
    if (rb->head == rb->tail) {
        return false; /* 空 */
    }
    *byte = rb->buffer[rb->tail];
    rb->tail = (rb->tail + 1) % VOICE_RING_BUF_SIZE;
    return true;
}

bool voice_extract_line(voice_ring_buf_t *rb, char *out_line, uint16_t max_len)
{
    if (rb->head == rb->tail || max_len < 2) return false;

    /* 先检查环形缓冲区中是否存在换行符 '\n' */
    uint16_t idx = rb->tail;
    bool found_newline = false;
    uint16_t length = 0;

    while (idx != rb->head) {
        if (rb->buffer[idx] == '\n') {
            found_newline = true;
            length++;
            break;
        }
        length++;
        idx = (idx + 1) % VOICE_RING_BUF_SIZE;
        if (length >= (max_len - 1)) {
            /* 超长但无换行，丢弃一个字节防止死锁 */
            uint8_t dummy;
            voice_ring_pop(rb, &dummy);
            return false;
        }
    }

    if (!found_newline) return false;

    /* 逐字节取出直到包含 '\n' */
    uint16_t out_idx = 0;
    while (rb->tail != rb->head && out_idx < (max_len - 1)) {
        uint8_t b = 0;
        if (!voice_ring_pop(rb, &b)) break;
        if (b == '\r') continue; /* 忽略回车 */
        if (b == '\n') break;
        out_line[out_idx++] = (char)b;
    }
    out_line[out_idx] = '\0';
    return true;
}

voice_cmd_t voice_parse_command_line(const char *line)
{
    if (line == NULL || *line == '\0') return VOICE_CMD_NONE;

    /* 跳过前导空白符 */
    while (*line && isspace((unsigned char)*line)) line++;

    if (strcmp(line, "INIT") == 0) return VOICE_CMD_WAKEUP;
    if (strcmp(line, "FON") == 0)  return VOICE_CMD_FAN_ON;
    if (strcmp(line, "FOFF") == 0) return VOICE_CMD_FAN_OFF;
    if (strcmp(line, "F+") == 0)   return VOICE_CMD_SPEED_UP;
    if (strcmp(line, "F-") == 0)   return VOICE_CMD_SPEED_DOWN;
    if (strcmp(line, "FMAX") == 0) return VOICE_CMD_SPEED_MAX;
    if (strcmp(line, "FMOD") == 0) return VOICE_CMD_SPEED_MED;
    if (strcmp(line, "FMIN") == 0) return VOICE_CMD_SPEED_MIN;
    if (strcmp(line, "FMODE") == 0) return VOICE_CMD_MODE_TOGGLE;
    if (strcmp(line, "FAUTO") == 0) return VOICE_CMD_MODE_AUTO;
    if (strcmp(line, "FMANU") == 0 || strcmp(line, "FMANUAL") == 0) return VOICE_CMD_MODE_MANUAL;
    if (strcmp(line, "SWON") == 0)  return VOICE_CMD_SWING_ON;
    if (strcmp(line, "SWOFF") == 0) return VOICE_CMD_SWING_OFF;
    if (strcmp(line, "SWTOG") == 0) return VOICE_CMD_SWING_TOGGLE;
    if (strcmp(line, "SW+") == 0)   return VOICE_CMD_SWING_SPEED_UP;
    if (strcmp(line, "SW-") == 0)   return VOICE_CMD_SWING_SPEED_DOWN;
    if (strcmp(line, "LON") == 0)  return VOICE_CMD_LIGHT_ON;
    if (strcmp(line, "LOFF") == 0) return VOICE_CMD_LIGHT_OFF;
    if (strcmp(line, "FSLEEP") == 0) return VOICE_CMD_SLEEP;
    if (strcmp(line, "QTEMP") == 0)  return VOICE_CMD_QUERY_TEMP;
    if (strcmp(line, "QSTAT") == 0)  return VOICE_CMD_QUERY_STATUS;

    return VOICE_CMD_NONE;
}

#ifndef HOST_UNIT_TEST

static UART_HandleTypeDef g_huart2;
static voice_ring_buf_t g_voice_rb = {{0}, 0, 0, 0};
static uint8_t g_rx_byte = 0;
static voice_cmd_t g_last_cmd = VOICE_CMD_NONE;

void voice_asr_init(void)
{
    GPIO_InitTypeDef gpio = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_USART2_CLK_ENABLE();

    /* PA2: USART2_TX (复用推挽) */
    gpio.Pin = VOICE_TX_Pin;
    gpio.Mode = GPIO_MODE_AF_PP;
    gpio.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(VOICE_Port, &gpio);

    /* PA3: USART2_RX (浮空或上拉输入) */
    gpio.Pin = VOICE_RX_Pin;
    gpio.Mode = GPIO_MODE_INPUT;
    gpio.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(VOICE_Port, &gpio);

    g_huart2.Instance = USART2;
    g_huart2.Init.BaudRate = 115200;
    g_huart2.Init.WordLength = UART_WORDLENGTH_8B;
    g_huart2.Init.StopBits = UART_STOPBITS_1;
    g_huart2.Init.Parity = UART_PARITY_NONE;
    g_huart2.Init.Mode = UART_MODE_TX_RX;
    g_huart2.Init.HwFlowCtl = UART_HWCONTROL_NONE;
    g_huart2.Init.OverSampling = UART_OVERSAMPLING_16;

    HAL_UART_Init(&g_huart2);

    /* 配置 NVIC 并使能 USART2 中断 */
    HAL_NVIC_SetPriority(USART2_IRQn, 2, 0);
    HAL_NVIC_EnableIRQ(USART2_IRQn);

    /* 启动中断接收单字节 */
    HAL_UART_Receive_IT(&g_huart2, &g_rx_byte, 1);
}

void USART2_IRQHandler(void)
{
    HAL_UART_IRQHandler(&g_huart2);
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART2) {
        voice_ring_push(&g_voice_rb, g_rx_byte);
        /* 继续触发下一次单字节接收 */
        HAL_UART_Receive_IT(&g_huart2, &g_rx_byte, 1);
    } else if (huart->Instance == USART1) {
        cli_test_push_rx_byte(g_cli_rx_byte);
        /* 继续触发下一次单字节接收 */
        HAL_UART_Receive_IT(&g_uart1, &g_cli_rx_byte, 1);
    }
}

void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart)
{
    /* 发生溢出(ORE)或噪声(NE/FE)时自动恢复接收，防止串口控制台无响应 */
    if (huart->Instance == USART1) {
        volatile uint32_t dummy = USART1->DR;
        (void)dummy;
        HAL_UART_Receive_IT(&g_uart1, &g_cli_rx_byte, 1);
    } else if (huart->Instance == USART2) {
        volatile uint32_t dummy = USART2->DR;
        (void)dummy;
        HAL_UART_Receive_IT(&g_huart2, &g_rx_byte, 1);
    }
}

void voice_asr_poll(void)
{
    char line_buf[32];
    if (voice_extract_line(&g_voice_rb, line_buf, sizeof(line_buf))) {
        voice_cmd_t cmd = voice_parse_command_line(line_buf);
        if (cmd != VOICE_CMD_NONE) {
            g_last_cmd = cmd;
        }
    }
}

voice_cmd_t voice_asr_pop_command(void)
{
    voice_cmd_t cmd = g_last_cmd;
    g_last_cmd = VOICE_CMD_NONE;
    return cmd;
}

void voice_asr_send_ack(const char *ack_str)
{
    if (ack_str == NULL) return;
    HAL_UART_Transmit(&g_huart2, (const uint8_t *)ack_str, (uint16_t)strlen(ack_str), 100);
}

#endif
