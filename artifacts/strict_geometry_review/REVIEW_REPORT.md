# 严格铜形读取审查：禁止自动修形后假通过

## 规则依据

实读 [Ucamco Gerber Format Specification Revision 2019.06](https://www.ucamco.com/files/downloads/file/81/the-gerber-layer-format-specification_en.pdf)，本地证据为 [原始PDF](gerber_spec.pdf) 与 [提取正文](gerber_spec.txt)。

- §4.12.1，PDF p99：每条 D02 分隔的 contour 独立填充，多个 contour 的结果做并集；不能对整个图层或多个 Region 做全局奇偶异或。
- §4.12.3，PDF p101–102：合法 simple cut-in 由一对完全重合、方向相反的直线组成；必须水平或竖直，同一 contour 内方向一致；不能在非端点处穿越其他边。其它自交没有规定解释。
- 同节：合法 contour 内 winding 恒为 +1 或恒为 -1，外部为0；轮廓方向不重要。不是所有弱简单多边形都合法。
- PDF p102明确警告 sloppy cut-in 是平面漏净距的重要原因，不能把其自动修成一个看似合理的 polygon。

KiCad [板格式说明](https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/)本次未给出足以证明任意 filled_polygon 弱简单轮廓填充语义的依据。因此 **PCB checker 仍只接受无歧义简单正向单环；带孔桥或负向单环暂报 unsupported，不将 Gerber 规则擅自套到 PCB。** 该限制可能拒绝合法原生 PCB，不构成其存在短路的证明。

## 实现

共享读取器 `tools/strict_copper_geometry.py`，三调用者是 `tools/verify_revb_copper.py`、`tools/validate_revB_gerber_geometry.py` 和 `tools/verify_revb_manufacturing.py`。

- 删除三处 `Polygon(...).buffer(0)`；不使用 make_valid、正向 winding 过滤、删除小岛等修形。
- Gerber 先验证边拓扑、完整反向桥对、方向和交点限制，再对 noded 线网执行 polygonize_full。
- 对每个面取内部代表点，向未经修改的原始有向边做射线奇偶测试，选择填充面并 union。验证 winding 与标准一致；桥线不能产生面。
- 独立负向 Region 是铜，不被丢弃；独立重叠 Region 用 union，不按层级猜成孔。
- 任意真实交叉、部分重叠、斜桥、多重 winding、内部正负 winding 混杂、region 圆弧、clear polarity 组合均保守拒绝并记录 unsupported_or_ambiguous_geometry，不将其报告为已经证明短路。
- 制造 checker 的 GKO polygonize 改为 polygonize_full，并确认没有丢弃悬线/切边/非法环或重复重叠边。
- 铜 checker 增加 --pcb/--report，所有路径（成功及失败）均遵守指定输出路径。

## 回归结果

`python tools/test_revb_strict_geometry.py`：8/8 PASS。

正例：简单矩形、标准洞桥正反绕向几何相同（面积15且孔中心不覆盖）、负绕向独立铜岛、多岛并集、嵌入的独立 contour 不误成孔。负例：蝴蝶自交、斜桥、未支持 PCB 弱简单和负向轮廓；当前冻结坏基线三个 checker 全部 exit1。

冻结坏基线：PCB F.Cu 原始 signed area 4903.171102759996 mm²，在 (194,182.5) 弱简单自交，拒绝；Gerber GTL 被更完整解析后检测到同一 contour 内部 winding 正负混杂，拒绝，**不会通过删除负向岛输出PASS**。结果和stdout/stderr在本目录对应三个JSON/log，未覆盖历史基线PASS证据。

`python tools/probe_native_gerber_regions.py`：读取 `artifacts/native_pcb_review/solid_native_gerbers` 当前副本，F.Cu 10个 Region、B.Cu 2个 Region，共12个全部可由标准cut-in子集解析。详见 [原生区域探测结果](native_region_probe.json)。这仅证明所列Region解析，不等于全PCB/Gerber制造验收或DRC通过；其它native格式/API兼容性仍未证明。

额外回归：盖油6/6、丝印4/4通过。生产生成器、PCB/SCH/Gerber交付基线未修改，未重新构建或发布。
