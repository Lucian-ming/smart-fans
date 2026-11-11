/**
 * @file cli_test.h
 * @brief 面包板逐模块独立测试控制台 (USART1 115200 8N1)
 *
 * 核心目标：
 * - 允许工程师在面包板上插拔各独立模块并单独测试，不自动触发任何电机运转
 * - 提供随时可执行的 emergency safe 急停命令
 */
#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

void cli_test_init(void);
void cli_test_poll(void);
void cli_print_banner(void);
void cli_test_push_rx_byte(uint8_t byte);

#ifdef __cplusplus
}
#endif
