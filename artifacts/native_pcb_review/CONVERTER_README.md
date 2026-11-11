# 隔离原生工程转换入口

## 用途与边界

把已可被 KiCad 10 原生解析的 RevB 输入 PCB/SCH 转为项目自带库、原生覆铜、ERC/DRC/parity 可复现的隔离候选。不是发布工具；输出只允许位于本工程 artifacts 下，禁止输入位于输出目录。不得据旧版候选替代后续 U3 改版验证。

## 调用

```bash
D:/dev_tools/Python/python artifacts/native_pcb_review/run_candidate_conversion.py --pcb hardware/kicad/fan_ctrl_revB.kicad_pcb --sch artifacts/native_sch_review/fan_ctrl_revB.kicad_sch --out artifacts/native_pcb_review/candidate
```

最终新 U3 完成路由后，将 `--sch` 指向对应新原理图，并建议指定新的 `--out` 目录。输入须已经修好库 child symbol owner prefix 等原生解析语法；本入口不会隐藏原生解析错误。

需要 KiCad 10.0 安装中的 kicad-cli.exe、pcbnew Python，以及 D:/dev_tools/Python/python 的 sexpdata。路径在驱动内显式声明。

## 十步严格执行

1. 输入原理图导出原生 baseline.net。
2. 转换符号库为项目自带 RevB_Symbols；符号组整体平移到 1.27mm 栅格；标签改全局；加官方 +5V/GND PWR_FLAG（声明已有外部供电，不是修改真实芯片引脚类型）。
3. 转换后原理图导出原生 native.net。
4. 比较所有实际 ref.pin 连接，不硬编码数量；仅规范根路径斜线和 NC 独立网名称，连接集合不允许改变。
5. PCB 同步原生 NC 网、字段、库 ID；机械孔 board_only；保留真实焊盘/布局/走线；区连接改实心。复制现有输入 .kicad_pro 和 .kicad_dru，不降低既有规则；没有项目文件时创建最小工程使本地库可解析。随后仅重载输出工程，将 `m_MaxError` 收紧到 `min(现值,1000nm)` 并用原生 `SaveProject` 持久化，记录 `precision_change.json`；不更改间距或错误严重性门限。
6. 原生 ERC，全 severity，违规导致失败。
7. 原生 DRC，全 severity/all-track-errors/schematic-parity，原生 refill 并保存，违规导致失败。
8. pcbnew 独立几何不变检查：元件位置/焊盘、所有走线/过孔及网名、Edge.Cuts 不变；覆铜与 NC 名称/元数据是预期变化。
9. 从已保存原生候选 PCB 导出 9 层真实 Gerber，关闭 aperture macros 便于独立解析。
10. 同一 PCB 导出毫米显式小数 Excellon，PTH/NPTH 分离及钻孔报告。

任何步骤非零即停止；源输入和生产 PCB/SCH 的 SHA256 前后必须一致。每步独立日志及命令保存在 run_summary.json，记录输出文件 SHA256，release_authorized 永远 false。重新运行失败时不要使用目录中旧输出，只认本次完整 all_steps_pass。

## 已完成基线回归

冻结旧 PCB SHA256：c9cb106cdc48e9b3e44ff9b6d379062e31b24f2d6fec1b29f22d64fc3b3264a1。
- 原理图实际 168 pin 转换前后连接集合相同，不是强行要求未来版本 168。
- 48 footprint 与 2810 track/via 的几何和网保持不变。
- 原生 ERC、DRC/parity 均零违规，未连接零。
- 真实 9 层 Gerber 和 PTH/NPTH 钻孔已导出。
- 首次不变性检查触发 KiCad 10 `PCB_VIA::GetWidth called without a layer argument` 原生断言；已改逐层 GetWidth(layer)，随后完整回归通过。保留失败记录，不冒充首次即成功。

## 不覆盖的验证

快照库不是独立封装尺寸认证；实心地增加焊接热负荷；没有实测 2A 温升、整机机械装配、物料库存或仪器测试。原生检查零违规不能替代这些。当前报告基线仍是旧 U3，后续 TLV1117LV33DCYR 必须用新输入重新执行，不能复用旧哈希。
