# software/

PC 端调试工具（**可选**）。v1 不联网，设备只通过 UART1 提供文本命令，所以这里不需要 App，只需要一个顺手的串口工具。

## 建议形态

Python + `pyserial`，一个脚本完成：发命令、收事件、把温度/转速打成曲线。协议见 [shared/protocol/](../shared/protocol/)。

```
software/
└── serial_tool/
    ├── main.py           # 命令行：python main.py --port COM5 status
    ├── protocol.py       # 命令构造与应答解析（与 shared/protocol 同步）
    └── requirements.txt  # pyserial, matplotlib
```

## 典型用法

```bash
python main.py --port COM5 status          # 读一次状态
python main.py --port COM5 speed 60        # 手动调速
python main.py --port COM5 plot --seconds 60   # 采 60 s 温度/转速曲线
```

## 为什么先不做手机 App

- v1 没有无线，App 无法直接连设备
- 调温控参数用电脑看曲线最快
- 等 v2 确定联网方案（Wi-Fi 或 BLE）再决定 App 形态，避免返工

## 待补充

- [ ] 确定是否做这个工具（也可以直接用串口助手）
- [ ] 工具需求：批量测试脚本、参数扫频、日志归档
