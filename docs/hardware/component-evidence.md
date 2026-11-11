# 关键元器件证据与采购限制

核查日期：2026-11-04。独立研究，不修改电路主脚本。型号真实性、封装匹配、电气适用性与实时库存分别判断。

## 最终建议

**追加核实：C3/C_VM不限制Lelon后，优先选择Rubycon 16ZLH220MEFC6.3X11 / C338177。** [立创官方商城](https://item.szlcsc.com/315974.html)明确给出品牌、完整MPN、C338177、220µF±20%/16V、D6.3×L11mm/P2.5、540mA@100kHz、6000h@105℃。实时库存仍未核实。

[红宝石原厂ZLH手册](https://www.rubycon.co.jp/wp-content/uploads/catalog-aluminum/ZLH.pdf)，已保存[本地原厂PDF](<D:/smart_fans/docs/hardware/sources/Rubycon-ZLH.pdf>)：

- 物理第1页（印刷77页）标题：`105℃ 6000～10000 hours, Miniaturized, Long Life, Low Impedance`；D≤6.3mm寿命6000h，在105℃施加额定电压及额定纹波的耐久条件。
- 物理第2页尺寸图：D6.3mm对应脚距F=2.5±0.5mm，线径d=0.5mm；长度标称11mm，图纸L≤16mm时α=1.5mm，故**标称11mm满足名义≤12mm，但实体最大长度L+α可达12.5mm**。若≤12mm是硬性装配上限而非名义长度筛选，本型号不能保证满足，应重新筛选。
- 同页16V/220µF行：D6.3×11mm，额定纹波540mArms（105℃、100kHz），**阻抗最大0.094Ω（20℃、100kHz）**，-10℃时0.35Ω。商城把94mΩ列在ESR字段，原厂实际列的是Impedance，文档以原厂定义为准。
- 容差±20%（20℃、120Hz），工作温度-40～+105℃。

这是比RGA更合适的低阻抗开关电源候选，料号、尺寸和原厂电气参数证据闭合；不等于整机稳定性/温升/电机尖峰验证已经通过。找到此明确证据后停止扩搜。下表RGA保留为历史对照而非首选。

| 用途 | Lelon MPN | 立创编号 | 参数证据 | 库存与限制 |
|---|---|---|---|---|
| C1优先低ESR候选 | RZW101M1EBK-0611 | C134665 | 100µF±20%/25V，直插D6.3×L11mm/P2.5；商城列340mA@100kHz、220mΩ@100kHz、4000h@105℃ | 库存未核实；输入RMS纹波是否合格仍须计算 |
| C1普通系列备选 | RGA101M1ESA-0611G | C311685 | 100µF±20%/25V，D6.3×L11mm/P2.5，2000h@105℃ | 库存未核实；不得标为低ESR |
| C3/C_VM尺寸匹配候选 | RGA221M1CSA-0611GACS | C881928 | 220µF±20%/16V，D6.3×L11mm；系列手册补证P2.5 | 库存未核实；不是已验证的XL1509低ESR输出方案 |
| 暂缓采用 | RXW221M1CCC-0611P | C916211 | 商城称220µF/16V/D6.3×11/7000h | 与关联目录存在尺寸、寿命冲突，不直接采用 |

原C106552的搜索索引指向AISHI（艾华）ERJ1EM101D12OT，不能标为Lelon。C151817索引指向DIODES MMBZ5254B-7-F齐纳二极管，不是电解电容。直接页面获取未成功，故旧SKU纠错证据为官方站点搜索索引交叉核对，等级低于以下实际读取的商城商品页。

## 1. XL1509-5.0E1：4脚低电平开启

[芯龙官方产品表](https://www.xlsemi.com/products_DC_DC_buck_mv.html)链接[原厂XL1509 Rev2.6数据手册](https://www.xlsemi.com/datasheet/XL1509-EN.pdf)，已存[本地副本](<D:/smart_fans/docs/hardware/sources/XL1509-EN.pdf>)。

- 第2页Pin Description，pin4名称EN，原文：
  > Enable Pin. Drive EN pin low to turn on the device, drive it high to turn it off. Floating is default low.
- 第4页订购表明确列出XL1509-5.0E1。
- 第6页EN Pin Threshold：High (Regulator OFF) = 1.4V；Low (Regulator ON) = 0.8V。**两者均在Typ列**，不可写成跨工艺/温度保证的上下限。
- 结论：**低开、高关；常开可将4脚接GND。**“<0.8V开启”可用于说明逻辑方向，但应说明0.8V是手册典型表值，不能伪造保证阈值。

[立创XL1509-5.0E1/C61063](https://item.szlcsc.com/62115.html)关联[旧版Rev2.0手册](https://atta.szlcsc.com/upload/public/pdf/source/20151126/1457707596805.pdf)，[本地副本](<D:/smart_fans/docs/hardware/sources/XL1509-LCSC-20151126.pdf>)第2页将pin4称为ON/OFF，同样低开高关。新EN和旧ON/OFF是同一引脚，不应误解成高有效使能。

## 2. C1真实Lelon料号

### 优先C134665：低ESR同尺寸候选

[立创官方商城RZW101M1EBK-0611](https://item.szlcsc.com/145975.html)明确显示品牌Lelon、MPN、C134665、100µF±20%25V、D6.3×L11mm、P2.5mm、340mA@100kHz、ESR220mΩ@100kHz、4000hrs@105℃；描述含“低等效串联电阻(ESR),适用于开关电源”。

[关联PDF](https://atta.szlcsc.com/upload/public/pdf/source/20181024/C316460_85D45B7084B2C9F0A8E78A5D81F5F048.pdf)已保存为[本地RZW手册](<D:/smart_fans/docs/hardware/sources/Lelon-RZW-C134665.pdf>)。该PDF为扫描件，当前模型图像接口不支持输入，未逐页独立核验；以上数字明确归属于商城参数，不冒称已经核对原厂表格。商城ESR字段是否来自原厂阻抗表，采购前宜复核，不无条件混同阻抗和ESR。

### 普通系列C311685

[立创官方商城RGA101M1ESA-0611G](https://item.szlcsc.com/294648.html?from=search)直接显示Lelon、C311685、100µF±20%25V、D6.3×L11mm、P2.5mm、2000hrs@105℃，满足指定品牌/容量/电压/外形，但不能作为低ESR电容宣传。RGA系列表100µF/25V纹波为142mA（120Hz、105℃），不能与100kHz额定值直接比较。

## 3. C881928脚距与非低ESR限制

[立创官方商城RGA221M1CSA-0611GACS](https://item.szlcsc.com/945600.html)直接显示Lelon、C881928、220µF±20%16V、D6.3×L11mm、2000h@105℃。商品页脚间距为“-”，不能声称网页直接给出P2.5。

[商品关联RGA CAT.2025E3手册](https://atta.szlcsc.com/upload/public/pdf/source/20250114/B13CD52585F9ECA2168D5F5192565A28.pdf)，[本地副本](<D:/smart_fans/docs/hardware/sources/Lelon-RGA-C881928.pdf>)：

- 印刷第140页（物理第1页）尺寸表：φD6.3mm→P2.5mm、φd0.5mm。因此P2.5由关联的系列手册补证；ACS特殊后缀完整承认图宜在量产前核实。
- 印刷第141页（物理第2页）220µF/16V/D6.3×11：纹波190mA，条件120Hz、105℃。
- 第140页原文：
  > If there is any requirement on ESR, it's suggested to use low ESR series instead of RGA.

**RGA不能标为低ESR。** 若C3是XL1509输出电容，应验证稳定性、纹波、温升和负载瞬态，或改选证据完整的低ESR系列。C_VM若跨电机电源，应另核对启动、堵转、换相纹波及母线尖峰；不能仅凭标称母线电压批准16V耐压。

## 4. RXW替代候选冲突

[RXW221M1CCC-0611P/C916211商城](https://item.szlcsc.com/990410.html)称220µF/16V/D6.3×11/7000h@105℃，脚距、ESR与纹波未给。

但[该页关联的CAT.2020C1目录](https://atta.szlcsc.com/upload/public/pdf/source/20201014/C881918_26EC4CF8CBD213C884BBEF20808279C3.pdf)，[本地副本](<D:/smart_fans/docs/hardware/sources/Lelon-RXW-C916211.pdf>)第147页注明RXW低ESR适用于开关电源，D≤6.3mm仅4000h，D≥12.5mm才7000h；尺寸表D6.3→P2.5。第148页220µF/16V通用表列**D8×11.5mm、阻抗最大0.117Ω（100kHz、20℃）、纹波555mA（100kHz、105℃）**，与商品D6.3×11冲突。

不能将D8的电气参数套到D6.3商品，也不能确定是特殊料、新旧版本还是商城录入错误。须取得完整MPN承认书后再采用。本研究在限Lelon阶段未找到证据完整且库存可验证的同尺寸低ESR220µF/16V替代；放宽品牌后已核实上文Rubycon C338177，但库存仍未核实。

## 5. 库存与电气门槛

所有候选商品的可读HTML均未返回SKU实时可售数量。商城通用“海量现货”“81万+种现货SKU”不构成具体物料现货证据。因此C134665、C311685、C881928、C916211全部标为**库存未核实**，既不宣称有货，也不宣称缺货。下单前应由采购保存具体SKU、数量、仓库及时间的页面截图或订单确认。

XL1509 Rev2.6第7页要求输出电容LOW ESR、SHORT LEADS。第10页12V→5V/2A应用例使用L68µH、CIN470µF/35V、COUT180µF/35V；该例不能证明任意100µF输入/220µF普通输出都合格，也不能单凭例图断言其他容量必然不合格。C1需核算实际RMS纹波；340mA额定值不一定覆盖最大负载，必要时加大尺寸、纹波等级或重新评估并联。

## Sources

1. [原厂产品索引](https://www.xlsemi.com/products_DC_DC_buck_mv.html)、[XL1509 Rev2.6 PDF](https://www.xlsemi.com/datasheet/XL1509-EN.pdf)：pin4、阈值、型号及电容要求。
2. [XL1509商城](https://item.szlcsc.com/62115.html)、[Rev2.0 PDF](https://atta.szlcsc.com/upload/public/pdf/source/20151126/1457707596805.pdf)：旧ON/OFF名称对照。
3. [C134665商城](https://item.szlcsc.com/145975.html)：低ESR C1候选完整参数。
4. [C311685商城](https://item.szlcsc.com/294648.html?from=search)：普通C1尺寸匹配。
5. [C881928商城](https://item.szlcsc.com/945600.html)、[RGA手册](https://atta.szlcsc.com/upload/public/pdf/source/20250114/B13CD52585F9ECA2168D5F5192565A28.pdf)：C3/C_VM身份、脚距、ESR限制。
6. [C916211商城](https://item.szlcsc.com/990410.html)、[RXW目录](https://atta.szlcsc.com/upload/public/pdf/source/20201014/C881918_26EC4CF8CBD213C884BBEF20808279C3.pdf)：待解决冲突。
7. [C106552/AISHI索引](https://jlcpcb.com/partdetail/ERJ1EM101D12OT/C106552)、[C151817/DIODES索引](https://jlcpcb.com/partdetail/DiodesIncorporated-MMBZ5254B_7F/C151817)、[LCSC C151817](https://www.lcsc.com/product-detail/C151817.html)：仅搜索索引交叉核对，完整商品页未成功读取。

方法限制：先尝试browser lane，未取得可用页面，new-tab因工具参数校验冲突失败；未操纵无关用户窗口。之后按任务授权使用web search/fetch，公开PDF下载后抽取文本。扫描PDF及库存未核实之处已明确标注。
