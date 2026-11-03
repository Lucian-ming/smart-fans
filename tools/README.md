# tools/

辅助脚本。原则：只做"人容易做错或重复做"的事，不替代 KiCad / 切片软件本身。

## 计划中的脚本

| 脚本 | 作用 | 何时需要 |
| --- | --- | --- |
| `bom_check.py` | 校验 BOM：位号重复/缺失、封装与原理图一致性、数量汇总 | 投板前 |
| `gerber_check.py` | 检查 Gerber 层是否齐全、板框是否闭合、钻孔与板框间距 | 投板前 |
| `fw_release.sh` | 注入 git commit 到固件版本、编译、归档 bin | 发版 |
| `log_parse.py` | 解析串口日志，提取温度/转速曲线用于调参 | 调温控 |
| `pinmap_check.py` | 比对 `pins.h` 与 `docs/hardware/pinmap.md`，提示不一致 | 硬件改版后 |

## 约定

- Python 脚本用标准库 + `pyserial`/`matplotlib`（仅在需要时），运行环境写进脚本头部注释
- 所有脚本支持 `--help`，默认行为为**只检查不修改**
- 输出用中文，问题按 `[ERROR] / [WARN]` 前缀，便于 grep
