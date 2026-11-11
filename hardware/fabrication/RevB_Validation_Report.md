# fan_ctrl_revB 修复与交付验收报告

日期：2026-11-04。结论：**本报告列出的独立自动几何/连通性检查通过；不等同于完整量产签核。**

## 1. 修复范围

- [电气生成器](<D:/smart_fans/tools/build_perfect_revB_v3.py>)：THT/安装孔按铜外径圆形避让，clearance=0.30 mm，64分段；SMD按实际宽高避让。PCB、Gerber采用一致焊盘尺寸。
- DC1优先使用三端`Connector:Barrel_Jack`缓存符号；按库引脚位置及实例坐标变换生成导线，修复Y方向与半栅格偏移；补合法UUID/实例信息及字符串转义。SCH版本20231120（KiCad 8），PCB版本20221018（KiCad 7标准，可由8读取），模型变量为`${KICAD8_3DMODEL_DIR}`。未宣称缓存图形与官方库逐字相同。
- 原固定L形布线额外检出398处异网铜交叠、481项净距违反。已由[双层避障路由器](<D:/smart_fans/tools/obstacle_router.py>)替代，保持器件位置、焊盘和网络不变；最终1947段走线、64过孔，全部32网包含GND显式连接。信号宽0.25 mm、电源/GND等0.5 mm，载流与热性能仍须工程复核。
- Gerber补全47个器件/安装孔的位号图形及边框；真实焊盘/走线/过孔光圈；纠正外框圆弧；Excellon采用显式小数毫米。
- [机械生成器](<D:/smart_fans/tools/build_authentic_smartfan_cad.py>)：按用户批准改为下壳、可拆盖、支架三件；内腔Z2～30、顶板Z30～32；25°斜面及指定OLED/EC11开孔；按键局部台面；开盖可装入裸95×95 mm PCB。

## 2. 独立自动验收

| 检查 | 实测 | 判定 |
|---|---:|---|
| 非地焊盘 | 126个，218个跨层检查 | 全部检测 |
| X / Y最小覆铜间隙 | 0.300000 / 0.300000 mm | ≥0.25，通过 |
| PCB全边界最小覆铜间隙 | 0.298290 mm | 通过；多边形圆弦误差已计入 |
| 覆铜侵入焊盘 | 0 | 通过 |
| 其他异网铜交叠 / 0.25 mm净距违规 | 0 / 0 | 通过 |
| 断网（含铺铜 / 不依赖铺铜） | 0 / 0 | 通过 |
| 原理图 | 43个符号，166个引脚 | 141个有网引脚+25个明确NC |
| 有网引脚到对应wire起点最大误差 | 0.000000 mm | 141/141通过，错网/悬空0 |
| 顶层丝印位号及框线 | 47/47 | 真实绘图，不是注释代替图形 |
| Gerber焊盘/过孔/1947走线与PCB几何 | 一致 | 通过 |
| Gerber最小覆铜间隙 | 0.298312078 mm | 通过 |
| Excellon钻孔命中 | 184 | 解析及尺寸/坐标对应通过 |
| 外壳三件总体积 | 68.970915595 cm³ | ≤70，通过 |
| STL网格 | 三件单壳、水密、正体积、绕向一致 | 坏边/同向重复边/退化面均0 |
| 平顶厚度 / 平顶内腔高度 | 2.000 / 28.000 mm | 通过 |
| 主坡角 / 法向厚度 | 25.000001° / 1.999999 mm | 通过 |
| OLED—EC11孔沿最短距离 | 13.731074197 mm | ≥13通过；不是16 |
| 裸板装入扫掠、闭盖、壳盖实体重叠 | 各0 mm³ | 仅裸板与限定包络 |
| 按键孔中心处竖直露出量 | 条件计算1.35 mm | 见安装条件，非实物装配测量 |

原要求165引脚来自DC1误用两针LED的旧统计；修正为三针后应为166。25个NC保持明确未连接标记，不伪造导线来凑数。

自动检查依据：[统一汇总及SHA256](<D:/smart_fans/hardware/fabrication/validation/validation_summary.json>)、[PCB铜审计](<D:/smart_fans/hardware/fabrication/validation/copper_audit.json>)、[原理图验收](<D:/smart_fans/artifacts/revB_schematic_validation.json>)、[Gerber验收](<D:/smart_fans/artifacts/revB_gerber_geometry.json>)、[机械实测](<D:/smart_fans/mechanical/P2_mechanical_verification.json>)。

## 3. 机械安装约束与未关闭事项

| 打印件 | 包络mm | 材积cm³ |
|---|---|---:|
| 下壳 | 99×99×9 | 24.369847394 |
| 可拆盖 | 99×99×23.9（装配坐标Z8.1～32） | 27.979158745 |
| 风扇支架 | 84×30×24 | 16.621909456 |

- 裸PCB放置XY=2～97、Z=6.5～8.1 mm；拆盖接缝Z=9 mm，实际净宽95.800002 mm。三件保留装配坐标，切片软件打印前应分别落到底板并选择适当方向/支撑。
- OLED中心XY=(80.5,64)，EC11=(73,88)，保持指定坐标。由于窗口28×16.5 mm、编码器孔径9 mm，沿25°面间距为13.7311 mm；若必须16 mm且保持OLED中心，EC11的Y至少90.05635 mm，当前未擅自移动。
- 用户提供模块PCB底到帽顶15 mm。**必须将模块PCB底安装在Z=8.1 mm且高度沿竖直Z轴**，帽顶才为Z=23.1 mm；局部台面孔中心Z=21.75 mm，形成1.35 mm中心处竖直露出。真实帽直径、顶面形状、按钮行程、安装支撑和倾斜轴向均未提供，因此不能保证全帽周缘露出量，也不能声称真实装配已验证。
- 螺钉建议M2.5：后排30 mm、前排12 mm，头径≤4.5 mm、不使用大垫片；盖孔2.8 mm、下壳攻丝预孔2.1 mm，先做打印攻丝试片。右前螺钉头投影到MIC孔最小净距约0.617 mm。共用PCB安装孔，需核实实物板孔与器件keepout。
- C3/C_VM按D6.3、最大长度12.5 mm限定圆柱包络检验，顶部到屋顶净高9.4 mm、与壳盖实体交叠0；C1按名义D6.3×11 mm检验。未包含直径容差、引脚及离板装配高度。
- **assembly_release=false**：未完成所有模块、线束、OLED/EC11实体、按钮帽形/行程、舵机花键、电机固定和完整填装板的装配验证。支架鞍座3 mm、翼底2 mm，舵盘槽残底0.5 mm，尚无强度/振动定级。打印收缩、支撑与材料强度必须打样确认。
- 截面图由STL算法生成；当前模型不支持图片输入，未声称人工视觉审阅。

## 4. 采购与电源证据

| 位号 | 最终料号 | 制造商型号 | 参数 |
|---|---|---|---|
| C1 | C134665 | Lelon RZW101M1EBK-0611 | 100µF/25V，D6.3×11、P2.5，低阻抗系列 |
| C3 / C_VM | C338177 | Rubycon 16ZLH220MEFC6.3X11 | 220µF/16V，D6.3×11、P2.5，ZLH低阻抗系列 |

C3/C_VM原厂额定纹波540mArms@105℃/100kHz，最大阻抗94mΩ@20℃/100kHz；此阻抗不是独立保证的ESR。标称L11 mm，容差最大12.5 mm。C1商城列340mA@100kHz，必须结合实际输入纹波复核。型号与供应商编号已修正，**实时库存未核实**，不能承诺现货。

XL1509 pin4 EN/ON-OFF低电平开启、高电平关闭，常开接GND有原厂支持；0.8V开启/1.4V关闭在手册表中为Typ，不作为保证极限。证据：[XLsemi原厂手册](https://www.xlsemi.com/datasheet/XL1509-EN.pdf)、[C1商品页](https://item.szlcsc.com/145975.html)、[C3/C_VM商品页](https://item.szlcsc.com/315974.html)、[Rubycon原厂ZLH手册](https://www.rubycon.co.jp/wp-content/uploads/catalog-aluminum/ZLH.pdf)、[项目证据记录](<D:/smart_fans/docs/hardware/component-evidence.md>)。

## 5. 六个交付文件

1. [PCB](<D:/下载/fan_ctrl_revB.kicad_pcb>)
2. [原理图](<D:/下载/fan_ctrl_revB.kicad_sch>)
3. [Gerber及钻孔包](<D:/下载/Gerber_fan_ctrl_revB_2026-11-04.zip>)
4. [BOM](<D:/下载/BOM_SmartFan_RevB.xlsx>)
5. [三件STL打印包](<D:/下载/SmartFan_Sanweihou_3D_Print_Kit_2026-11-04.zip>)
6. [本报告](<D:/下载/RevB_Validation_Report.md>)

请以新三件ZIP为准，下载目录中遗留的旧独立两件STL不再适用；未擅自删除用户旧文件。同步过程保留被替换文件备份，并用SHA256核对源/目标完全一致，记录在[交付清单](<D:/smart_fans/hardware/fabrication/validation/delivery_manifest.json>)。

## 6. 复现与生产前复核

在项目目录运行：
```text
python tools/build_perfect_revB_v3.py
python tools/build_authentic_smartfan_cad.py
python tools/validate_revb_all.py
```

已执行两生成器和全部独立验收，均退出0。当前没有嘉立创EDA MCP和可用kicad-cli，因此未执行KiCad原生DRC/ERC/网表导出，也未将自写解析器等同于原生验证。BOM由已有生成器的同一元件清单输出；Univer导入接口因docType参数约束拒绝XLSX，本次未完成该工具的独立工作簿回读。

生产前还需：KiCad原生打开/DRC/ERC、额定及堵转电流下的铜厚/线宽/温升检查、降压环路与纹波测试、器件封装对实物核验、完整机械装配及打印强度试验。本报告不为这些尚未执行项目签核。
