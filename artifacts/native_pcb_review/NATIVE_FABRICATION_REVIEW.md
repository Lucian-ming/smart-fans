# 原生制造几何审计接手记录

## 脚本与范围

`tools/verify_revb_native_fabrication.py` 参数：`--pcb --gerber-dir --report`。
审计九层：F/B.Cu、F/B.Paste、F/B.Mask、F/B.SilkS、Edge.Cuts；另读取独立 PTH/NPTH Excellon。附属 gbrjob 和钻孔文字报告是元数据，不作物理图形层。每份已解析制造文件和 PCB 都记录 SHA256。

- 支持 KiCad 旧数字网号映射和新直接网名，焊盘/过孔/走线/zone 使用相同解析；未知网号拒绝。
- 导出坐标固定 X=x、Y=-y，不拟合平移或镜像。
- 原生 region 由 strict_copper_geometry 的 Ucamco 孔桥解析器解释；不调用 buffer(0) 或 make_valid。
- 矩形/圆形焊盘、圆孔及已支持图元；未知图元/孔槽/英寸输入失败关闭。
- 检查覆铜对非地铜、异网铜、孔对铜、真实孔坐标/孔径/孔间、铜与孔对板边、mask几何/开窗间距/开窗对异网铜、丝印对mask/板边，以及两面焊膏几何。
- 不是任意PCB填充等价性证明，必须同时通过原生 DRC/ERC/parity；不是装配或热认证。

## 修复审计实现而非降低门限

1. 原189行版本只读取七层；已加入焊膏两层解析和焊盘开口对照。
2. 原网解析直接取末字段会将旧 zone 数字网号与 pad 名称分裂；已统一映射，并覆盖真实解析器的数字字符串类型。
3. KiCad 矩形mask开窗是正margin等距圆角扩张，并非扩大方形框。通过真实R_SDA的21顶点mask contour验证；按这个真实几何语义建立预期。正margin的buffer是设计偏移运算，不是修补畸形输入。
4. 原生工程默认 `m_MaxError=5000nm` 使mask圆逼近约0.0048mm，超过既有0.003mm比对门限。经父代理授权使用真实pcbnew API在隔离工程设为1000nm，原生SaveProject后另起进程读回验证。没有降低任何门限。已合入 converter，采用min(原值,1000)，仅保存输出工程。
5. Excellon单位实际位于import_settings.unit而不是文件直接unit属性；初测试因此失败，已按实际API修复。
6. 多个离散开窗按严格一一连通分量比较Hausdorff，仍使用0.003mm；圆孔间隙和孔到铜使用解析中心距减半径，减少多边形近似和计算开销。

## 正反例

`tools/test_revb_native_fabrication.py` 已在 `artifacts/native_pcb_review/native_fabrication_tests_precision_fixed` 完成：
- baseline：通过。
- GND region侵入Q1焊盘：拒绝，plane_clearance、different_net_clearance、hole_copper_clearance、mask_to_foreign_copper。
- 一钻孔偏移0.20mm：拒绝，drill_mismatch。
- F.Cu整体Y错误镜像：拒绝，track_mismatch、pad_via_aperture_mismatch、copper_board_edge。

三负例必须被对应语义检测拒绝；单纯解析异常不算测试成功。运行时重连丢失的一次旧测试已确认无残留Python进程，不计作通过；后续完整测试exit0。

旧基线精度样本：铜到板边0.999970871mm，最小孔间0.605538514mm，顶丝印到mask0.160mm；208 PTH，0 NPTH，九层均解析。Gerbonara对原生Excellon的G90位于header之后发SyntaxWarning，日志保留，所有孔逐坐标/孔径匹配未被跳过。

## 最终TI版本

最终输入目录 `artifacts/native_pcb_review/candidate_tlv1117` 的max_error已独立原生读回1000nm。最终 `final_fabrication_audit.json` 已PASS，errors=[]，命令exit0。PCB SHA256为3341183e1b76a875c8ae71b7134a121bded68481aa67c9ad78303b58f91eaf3a。九层和两钻孔文件均解析并记录哈希；211 PTH、0 NPTH，最小孔间0.308276253mm，双面铜到板边0.999970871mm，正面mask桥0.570mm/背面0.701714mm，顶丝印到mask0.160mm。正面焊膏46图形、71.823mm²，背面空层已检验。没有用旧U3样本代替最终板验证。
