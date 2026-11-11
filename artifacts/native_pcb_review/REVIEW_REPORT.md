# RevB 原生PCB审计与隔离修复试验

日期：2026-11-04。状态：**冻结生产版不合格；不得投板。隔离副本验证了原生铺铜修复路线，但不等于整项目/整机签核。**

## 1. 基线与审计范围

只读生产基线 `hardware/kicad/fan_ctrl_revB.kicad_pcb`，SHA256：`c9cb106cdc48e9b3e44ff9b6d379062e31b24f2d6fec1b29f22d64fc3b3264a1`；审计结束仍一致。没有改生产、下载文件或主生成源码。以下修改与输出仅在 `artifacts/native_pcb_review/`。

使用 `C:/Users/Lucian/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe` 10.0.7。PCB检查参数 `pcb drc --format json --all-track-errors --severity-all --exit-code-violations`；未设置新增豁免、未降低任何设计阈值。KiCad报告中本身有5类默认ignored_checks，详JSON，不能将本次结果说成覆盖所有可能检查。

## 2. 91项原生违规分类

来源 `artifacts/revb_native_drc_board_only.json`：

|类别|数量|严重性|
|---|---:|---|
|clearance|23|error|
|hole_clearance|9|error|
|solder_mask_bridge|10|error|
|starved_thermal|1|error|
|lib_footprint_issues|48|warning|

未连线0。22处clearance为F.Cu GND填充对BUZ_BASE走线/焊盘、J_MCU_L第8至15脚NC铜皮的0间距。另一处为BUZZER_CTRL过孔(156.2,109.9)与B.Cu地的0.2329mm间距。孔间距9处不是钻孔对钻孔，而是钻孔对错误填充铜；阻焊10处也对应这些错误铜域，不能混淆为自检已覆盖的单一孔对孔或开窗对开窗指标。

## 3. 确认的生成与验收双重缺陷

`tools/build_perfect_revB_v3.py:676`只选第一个正面积外环；`:677`却收集全部负面积内孔，然后将这些孔拼接进该唯一外环。真实Manifold计算得到：F.Cu **58个外环、24个孔**；B.Cu **33个外环、45个孔**。因此位于被丢弃岛内的孔被错误拼接到主环，变为负绕向孤立域。

证据 `manifold_contours.json`：BUZ_BASE孔在被遗漏的138.388487939mm²外岛内；MCU NC8孔在被遗漏的557.737246095mm²外岛内。诊断脚本只提取计算函数并重算轮廓，没有执行生成器顶层。

基线F.Cu原始有向面积4903.171102760mm²，Shapely `buffer(0)`后变为4945.429331355mm²，改变42.258228595mm²。旧铜检查、Gerber检查及制造检查均调用`Polygon(...).buffer(0)`，无条件修复改变了填充语义。

不经过buffer修复，以原始边界射线奇偶和绕数检查：

|坐标/对象|F.Cu绕数|奇偶规则有铜|buffer(0)解释|
|---|---:|---|---|
|(134,119.5) Q1.2 BUZ_BASE|-1|是|无铜，距离5.025mm|
|(134.85,115) R10.2 BUZ_BASE|-1|是|无铜，距离4.48446mm|
|(139.88,146.35) MCU NC8|-1|是|无铜，距离10.31821mm|
|(139.88,128.57) MCU NC15|-1|是|无铜，距离2.17063mm|

因此旧14项自动PASS是**假阴性**，不能继续作为生产依据。原手工Gerber使用相同畸形边界；原生不refill导出也保留该边界。两者均不能视为无短路，不能仅凭重新解析后buffer(0)无交集就放行。

### 过孔0.2329mm的独立问题

过孔铜径0.6mm、钻径0.3mm。生成器`:661`实际切削圆是**12边**，不是16边。原始B.Cu边界到该过孔中心的最近距离为0.579544718mm，自检推得铜间距0.279544718mm，但原生DRC报告0.2329mm。单纯12边圆弦误差不足以完整解释此差异；原生DRC内部碰撞近似/畸形轮廓解释的精确数值机制尚未隔离确认，不冒称已证明。原生重铺铜后此违规消失。建议删除手工已填铜而非继续修补此路径。

## 4. 隔离副本原生修复试验

|副本/报告|处理|error|warning|未连|
|---|---|---:|---:|---:|
|refilled / refilled_drc.json|仅原生--refill-zones --save-board|4|48|0|
|solid_gnd / solid_gnd_drc.json|两GND区改ZONE_CONNECTION_FULL，再原生refill|0|48|0|
|solid_local / solid_local_drc.json|增加真实可解析项目封装库|0|0|0|

首次refill消除全部clearance、hole_clearance、solder_mask_bridge；剩热焊盘缺陷：J_MCU_L.2 B.Cu、J_MCU_R.20两面、J_GESTURE.2 F.Cu，分别是孤岛热辐条或不足两辐条。

实心GND连接不是忽略热焊盘错误：它实际改变铜连接几何、避免使用细热辐条。全板已有显式GND走线，原生检查仍未连0。**代价是手工焊接热负荷增大，需要装配工艺/焊台能力验证；不证明热性能、孔壁载流或2A连续能力。**

本地库由`create_local_lib.py`使用`pcbnew.PCB_IO_KICAD_SEXPR().FootprintSave`生成48个真实`.kicad_mod`，`fp-lib-table`通过`${KIPRJMOD}/RevB_Snapshot.pretty`引用。`local_library_manifest.json`保留原ID与新ID映射。它是**精确板载封装快照库，不是独立封装尺寸认证或官方标准库等价认证**。没有用DRC exclusion屏蔽库警告。生产集成时应将SCH/PCB footprint ID一并映射，不能只换PCB。

## 5. 原生SCH一致性仍未通过

复制父代理修复解析的原理图到`solid_gnd.kicad_sch`，与保持原封装ID的`solid_gnd.kicad_pcb`运行`--schematic-parity`。结果见`solid_gnd_parity.json`：217项parity warning，其中169 net_conflict、44 footprint_symbol_field_mismatch、4 extra_footprint。

具体：原理图局部label产生`/+5V`等路径前缀，而PCB为`+5V`；31 NC在原生网表有`unconnected-(...)`单脚网络而PCB为net0；字段Description/LCSC等不同；4安装孔没有对应原理图符号。需要统一网表、字段与纯机械件语义，不能忽略这些结果，也不能将board-only零违规称为整项目原生通过。

## 6. 推荐生产管线（待父代理集成）

1. 生成合法PCB对象、精确net/pad/track/via、仅区域外轮廓和铺铜参数；不再写手工`filled_polygon`，不再以手工keyhole导出铜光绘。
2. 与原生SCH网表统一网络名字、NC单脚网、字段和本地封装ID；机械件按正式语义处理。保留网络、几何、物料变更审计。
3. 原生refill保存最终PCB。明确选择GND实心连接及相应焊接工艺要求，或真正布局改动保证热辐条，不能豁免starved_thermal。
4. 原生DRC全severity/alltracks，加SCH parity；失败即停止。应保存原始报告、版本、规则/ignored_checks与哈希。
5. 仅从这份已保存并审核的PCB原生导出Gerber与Excellon。隔离目录`solid_native_gerbers/`已实际导出七层（铜/阻焊/丝印/板框）、PTH和NPTH两钻孔文件，命令exit0；只是修复方案样本，不可生产放行。
6. 更新独立几何审核器：不能对失效polygon无条件buffer(0)。原生Gerber也可能使用合法弱简单keyhole环，不能仅以`is_valid=false`一刀切；应对线网分面、按原始奇偶/绕数选择面并检查语义，或使用原生受验证三角分解。增加“丢父外环、保留孤岛孔”负例，以及原生弱简单正常环正例。
7. 制造检查需覆盖孔对铜、开窗对异网铜，不仅孔对孔/开窗对开窗；导出文件与最终原生板绑定哈希。

## 7. 证据与复现

本目录包含`compare_geometry.py`、`check_winding.py`、`inspect_contours.py`、`create_local_lib.py`及各JSON报告、隔离PCB、原生光绘。全部后台任务已收取。`FootprintSave`包装器自动插件检测返回空，改为明确的PCB_IO_KICAD_SEXPR插件后成功；这是绑定选择问题，不是忽略库错误。

结论：找到了能使**隔离PCB board-only原生DRC零违规**的最小路线，但生产基线仍有已证实的错误填铜，SCH parity及整项目签核尚未完成。不得恢复投板许可。
