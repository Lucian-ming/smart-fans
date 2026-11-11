# RevB PCB 下单前封装与制造只读复核

**结论：暂不放行下单。** 新制造门禁实跑完成，exit 1（预期拒绝，不是程序异常），扫描184钻击的16836个配对；6个失败门禁为GTL/GBL板边、钻孔间距、GTS/GBS阻焊桥、丝印开窗净距。门禁更高细分精度结果：铜边0.171572500mm，丝印开窗交叠7.827167297mm²；下文早期审计的7.826599195mm²来自较低圆形/线端离散精度，不影响失败结论。

先前铜间距/连通性通过，不能覆盖真实元件封装和同网钻孔制造约束。本次未修改生成器、PCB或Gerber，只新增审计和证据。机械按当前任务暂停。

## 依据与复现

- 被审源：[生成器](../tools/build_perfect_revB_v3.py)，被审成品：[PCB](../hardware/kicad/fan_ctrl_revB.kicad_pcb)、[Gerber目录](../hardware/fabrication/gerber_revB)。
- 只读计算脚本：[audit_footprint_release.py](audit_footprint_release.py)，执行 `python artifacts/audit_footprint_release.py`（exit 0表示计算完成，不表示设计合格）。
- 新增生产门禁：[verify_revb_manufacturing.py](../tools/verify_revb_manufacturing.py)，执行 `python tools/verify_revb_manufacturing.py`；从实际GKO圆弧中心线重建轮廓，扫描全部钻孔对（包括同网）。默认铜边/孔间净距0.25mm、阻焊桥0.10mm、丝印至开窗0.10mm。输出[manufacturing_audit.json](../hardware/fabrication/validation/manufacturing_audit.json)，任一违反则exit 1。同网合并开窗也先作为待工艺明确豁免的失败，不冒充电气短路。槽孔暂不支持会显式报错，后续槽孔修复时需扩展该门禁，不能静默漏检。
- 全量数值：[pcb_release_footprint_metrics.json](pcb_release_footprint_metrics.json)。计算直接解析已序列化PCB、GTL/GBL/GTS/GBS/GTO，Shapely计算真实光圈面积及距离；未import会执行构建的生成器。
- 官方KiCad封装通过GitHub API下载并保存于[参考目录](footprint_reference)，JSON记录源URL和Git blob SHA。它们证明当前焊盘不符合所标库封装；**通用KiCad库不能代替特定采购型号厂家机械图**，更不能仅凭通用名称认定DC插座可替换。

## 下单阻断项

### 1. 两个普通圆钻发生实际重叠——确定失败

PCB的via9中心(137.2,123.9)、via19中心(137.3,124.0)，均为Ø0.3mm钻孔、Ø0.6mm铜环。两中心距0.141421356mm，小于孔径0.3mm，孔边有 **-0.158578644mm** 净距。它们同为net 4，故异网铜距检查不会发现。普通Excellon两个相交钻击不能当作受控槽孔设计，存在钻头偏移、孔壁/电镀可靠性问题。

**必须合并/移开via并重布线，独立检查所有钻孔对，不分网络。** 不可仅在Gerber删除一个钻击：PCB/布线/孔铜连接必须同步一致。

### 2. U3 SOT-223 自绘尺寸严重不符——确定不符合标称库

源[156–164行](../tools/build_perfect_revB_v3.py#L156-L164)标 `Package_TO_SOT_SMD:SOT-223-3_TabPin2`，但三小脚中心y=+1.5，tab中心y=-1.5，两排中心距只有 **3.0mm**；小脚0.9×1.5，tab3.2×1.5mm。

[KiCad官方SOT-223-3_TabPin2](https://github.com/KiCad/kicad-footprints/blob/master/Package_TO_SOT_SMD.pretty/SOT-223-3_TabPin2.kicad_mod)两排中心±3.15，即 **6.3mm**；转成当前朝向后小脚1.5×2.0、tab3.8×2.0，脚间距2.3。当前不是仅旋转/平移差异，不能按标称SOT-223焊装。参考blob `28ac67f6eb19e6c53b74061cf3ab014f2920ecaa`。

此外标准TabPin2的tab和中脚均为编号2；当前tab编号4，虽然接同一+3.3V，故不能称已经短接错网，但符号/封装语义不一致。应选择真实厂商AMS1117推荐land pattern，将两铜焊盘共享pin2（或明确使用合法4脚自定义符号/封装），重跑引脚数量及连接验收，不机械坚持旧166计数。

### 3. DC1 无槽孔、脚位与所标BarrelJack库不符——未取得采购机械图前禁止放行

源[93–96行](../tools/build_perfect_revB_v3.py#L93-L96)指定C16214 / XKB DC-005-5A-2.0，实际仅三个Ø1.2圆孔、Ø2.2铜盘，中心(0,3),(-3,0),(3,0)。导出器[750–757行](../tools/build_perfect_revB_v3.py#L750-L757)、[1187–1229行](../tools/build_perfect_revB_v3.py#L1187-L1229)只支持标量圆钻，无槽孔路径。

所标[官方BarrelJack_Horizontal](https://github.com/KiCad/kicad-footprints/blob/master/Connector_BarrelJack.pretty/BarrelJack_Horizontal.kicad_mod)为三扁脚槽：(0,0)1×3、(-6,0)1×3、(-3,4.7)3×1mm，铜3.5×3.5/3×3.5，不是当前布局的刚性旋转/平移。blob `e95351650ef8ea5b5848d13a87360ffa5e27abb2`。

**需锁定采购料号原厂尺寸与pin1中心/套筒/断开触点定义，按实物建槽孔。** 本次没有拿到该SKU机械图，不能断言通用库的所有尺寸就是这颗DC-005尺寸，也不能声明Ø1.2圆孔一定能装；当前无证据足以放行。PCB、铜区避让、Gerber、PTH槽文件与独立验证器都须支持真实椭圆/槽几何。

### 4. SMA / SOD-123 自绘焊盘不等于标称标准封装——需要纠正和料号图审核

| 器件 | 当前 | 所标KiCad参考 | 判断 |
|---|---|---|---|
| D1/D2 SMA | 中心±1.8，1.5×2.0 | 中心±2.0，2.5×1.8 | 当前内外焊接长度明显不同，未做具体SS24厂家推荐焊盘审核 |
| D3 SOD-123 | 中心±1.2，0.9×1.1 | 中心±1.65，0.9×1.2 | 中心距2.4而参考3.3mm，明显压缩0.9mm；必须修正 |

来源：[官方D_SMA](https://github.com/KiCad/kicad-footprints/blob/master/Diode_SMD.pretty/D_SMA.kicad_mod) blob `c71caaa1b9a90d7eb2d069b5c8ebf7ee362817e7`；[官方D_SOD-123](https://github.com/KiCad/kicad-footprints/blob/master/Diode_SMD.pretty/D_SOD-123.kicad_mod) blob `804e6bf82d28b8c7ba6bf902eb9601714d3b63be`。生成器[99–102](../tools/build_perfect_revB_v3.py#L99-L102)、[132–135](../tools/build_perfect_revB_v3.py#L132-L135)、[237–240](../tools/build_perfect_revB_v3.py#L237-L240)。

**特别注意极性映射：** 当前自定义二极管/LED符号[887–888](../tools/build_perfect_revB_v3.py#L887-L888)、[901–902](../tools/build_perfect_revB_v3.py#L901-L902)、[915–916](../tools/build_perfect_revB_v3.py#L915-L916)定义A=1/K=2，不能盲换惯例K=1的标准符号/封装并保留原网。D1必须A=GND、K=SW；D2必须A=12V_RAW、K=12V_IN；D3必须A=BUZ_DRV、K=5V。当前按自定义A/K逻辑并非反向，问题是标准库名称/编号语义及缺少明确阴极装配标记会造成装反。

### 5. 圆角区域铜距板边仅0.171572mm——达不到0.25mm审查门槛

真实板是100..195mm、R3圆角，铜区却由[635行](../tools/build_perfect_revB_v3.py#L635)101..194方框生成。圆角处最近距离为 `3 - sqrt(2)*2 = 0.171572875mm`，数值多边形计算0.171572068mm（近似差约0.000001mm）。上下铜层相同，铜未超出板，但**并非宣称的1mm退让**。应以真实圆角板轮廓向内偏置（建议至少0.3mm，最终按工厂工艺）裁切铜区并重验；本报告不把特定工厂未确认的加工能力当作通过。

### 6. GTO真实丝印压阻焊开窗——确定失败

按0.15mm实际线宽重建GTO，而非只看中心线：GTO与顶阻焊开窗交叠 **7.826599195mm²**，**484个丝印线对象**碰到开窗，影响40个开窗（包含via；不是484个元件）。例：Q1.3重叠0.901171mm²、C_VM.1为0.885144、SPK1.2为0.441097，C5/C6及R10/R_SDA也受影响。

源[1343–1346行](../tools/build_perfect_revB_v3.py#L1343-L1346)只按自身pad包围盒加边框，未裁去其它器件和via开窗；文字也未做全局避让。应按所有开窗外扩厂商要求净距后裁切/搬移丝印，并增加清晰pin1/极性标记。不能仅依赖板厂CAM自动删丝印（会丢位号/装配方向）。当前PCB本身只输出Ref没有这些边框，手写GTO和原生再出图不等价。

## 其它计算结果与限制

- 184个钻击（含64via）。最小钻径0.30mm。普通焊盘最小名义环宽0.30mm；via名义环宽0.15mm。**这些是理想同心尺寸，不含钻偏/成品孔径/电镀公差，且不消除上述孔重叠。** 工厂需确认0.15mm是否按其保证环宽规则可接受。
- H1–H4实际是Ø3.2mm **PTH接地孔**，Ø6铜环、名义环宽1.4mm、阻焊开窗Ø6.1。不是NPTH，不应让板厂误当非金属机械孔；所标`_Pad_Via`未生成外围via阵列（不能称完整复制库）。若螺钉需接机壳地请明确；若需绝缘应改NPTH并铜禁布，不能只改网名。螺钉头/垫圈外径和与临近焊盘的机械净距尚未核实。
- 顶阻焊234开窗，底184；最小阻焊桥为0（存在相交开窗），顶5对、底2对。顶分别C6.2/via2、R10.1/via53、R_STBY.1/via31、via8/via13、via9/via19，均同网。**这不是异网短路证明**，但SMD与未盖油via相邻会吸锡，需按装配工艺移via或盖油；最后一对同时有严重钻孔重叠。其余独立开窗间未发现0<gap<0.1mm。开窗最小板边距1.95mm，无开窗越板。
- 丝印最小板边距0.321504mm，无越板。GT(L/B)均无越板铜。
- 没有验证全部采购料号真实性/厂商机械图、模块插针方向、courtyard元件体积相撞、完整负载热设计或原生KiCad DRC/ERC。命名为标准封装不能当作已加载标准库：当前生成器只按手写pads输出，未读取该库。

## 建议修复顺序与放行条件

1. 锁定DC1/AMS1117/二极管具体采购机械图和极性；替换真实land pattern，保留功能网络而非盲保pin号。
2. 扩展槽孔数据/导出/验证；删除重叠钻孔根因，路由器把钻孔和同网制造约束独立建模。
3. 按真实板轮廓裁铜，重新布线；全部pad/via/slot都参与精确铜距、孔距、环宽和板边检查。
4. 全局丝印避让并输出极性，确认via盖油/开窗策略。
5. 再生成并核对PCB与全部制造层；原先合格报告必须失效重跑。取得工厂对应板厚/铜厚/孔公差的DFM反馈后，再称下单可接受。本报告**不批准现有Gerber投产**。
