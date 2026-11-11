# 单5V RevB：真实求解器与模型清单

核验时间：2026-11-04。范围仅为求解器发现、准确型号模型可用性与独立RC冒烟测试；不替代整板审核，不修改生产生成器、交付文件或用户EDA会话。

## 1. 可用求解器：已实际运行

- **LTspice 26.1.1 for Windows**：[程序](<C:/Users/Lucian/AppData/Local/Programs/ADI/LTspice/LTspice.exe>)，70,571,120 bytes，SHA256 `3c144a2b3ec6a30baac6761c502d99b95aaa40b947ff5eca25b8fbd80d68af72`。
- 版本证据是本次[运行日志](<D:/smart_fans/artifacts/simulation_review/rc_solver_baseline.log>)首行，不是安装目录最新变更日志（该文件写26.1.2，但实际执行程序报告26.1.1）。
- [本地官方CLI帮助](<C:/Users/Lucian/AppData/Local/Programs/ADI/LTspice/LTspiceHelp/commandlineswitches.htm#L61-L62>)确认`-b`批处理，结果写同名raw；`-ini <path>`可指定隔离配置，`-ascii`可输出文本波形但影响性能。

实际执行（exit 0，未打开或修改用户EDA工程）：

```text
C:/Users/Lucian/AppData/Local/Programs/ADI/LTspice/LTspice.exe -b D:/smart_fans/artifacts/simulation_review/rc_solver_baseline.cir
```

[基准网表](<D:/smart_fans/artifacts/simulation_review/rc_solver_baseline.cir>)为1kΩ、1µF、1V阶跃，时间常数1ms；[日志](<D:/smart_fans/artifacts/simulation_review/rc_solver_baseline.log>)及[原始波形](<D:/smart_fans/artifacts/simulation_review/rc_solver_baseline.raw>)已生成。内部数学一致性检查：1τ电压0.632120367773V（理论0.632120558829V），5τ为0.993262052536V（理论0.993262053001V）。**仅证明本机真实求解器可运行，与RevB电源/功能是否通过无关。** 不将此内部自检作公开第三方求解器性能比较。

许可证为[ADI本地许可PDF](<C:/Users/Lucian/AppData/Local/Programs/ADI/LTspice/License.pdf>)，标识20230822-LTS-CTSLA：§1允许内部使用及general circuit simulation；§4禁止向第三方分发程序，并对半导体制造商使用作额外限制；§5约束向第三方发布benchmark/comparison。仅使用已有安装，不将exe/模型库复制进用户交付包。此处不是法律意见。

## 2. 其他工具发现及边界

- [KiCad随附ngspice.dll](<C:/Users/Lucian/AppData/Local/Programs/KiCad/10.0/bin/ngspice.dll>)实际存在，7,220,576 bytes，SHA256 `eb4c19c53278a8dfd823396c894a7b87c0985dff8becd07f1ce80689c7c686f8`。它是共享库，不是已验证可直接执行的CLI；本任务没有载入调用或判定其版本。已经通知父代理核实新的KiCad安装状态，旧“未安装”摘要不再代表当前文件系统。
- PATH未发现ngspice/spice命令；递归检查D:/dev_tools、D:/lceda-pro没有ngspice/ltspice求解器命名文件。D:/dev_tools/Python/Lib/site-packages/ltspice为Python **1.0.6波形读取包，不是SPICE求解器**。
- 不绕过嘉立创外部脚本权限，不操作用户GUI工程，无需下载安装大型软件。若后续确需独立ngspice，可从[官方下载页](https://ngspice.sourceforge.io/download.html)选择Windows包，届时核版本、平台、许可证与发布校验值；目前已有可运行LTspice，未下载该候选，也未声称任何未下载文件校验通过。

## 3. 当前BOM准确型号与模型状态

| 位号 | 当前器件证据 | 准确厂商模型状态 | 能与不能做的仿真 |
|---|---|---|---|
| Q_PWR | [生成器119–120行](<D:/smart_fans/tools/build_perfect_revB_v3.py#L119-L120>)：Alpha & Omega Semiconductor **AO4409**，不是AO4407A也不是别厂同名芯片 | 本地准确模型未找到；尚未取得可追溯AOS厂商SPICE模型 | 可用原厂数据手册参数构建**明确标注的工程近似模型/敏感性扫描**，不能称厂商模型。简单开关+Rds+体二极管只能审拓扑/稳态压降，不能认证浪涌、Qgd/Miller、反向恢复、雪崩或结温 |
| U3 | [生成器152–153行](<D:/smart_fans/tools/build_perfect_revB_v3.py#L152-L153>)及[当前BOM](<D:/smart_fans/docs/hardware/bom.md#L50>)：Advanced Monolithic Systems **AMS1117-3.3，C6186**；[LCSC料号页](https://item.szlcsc.com/6652.html)实际确认厂家/MPN/SOT-223 | 本地准确模型未找到；尚未取得AMS原厂对应SPICE模型 | 可用电压源+压差/限流的行为模型审静态预算，但**不能验证当前10µF陶瓷输出电容的闭环稳定性、PSRR、输出阻抗、启动/短路热保护**；不能把ADI LT1117、TI LM1117或其他厂1117模型冒充准确器件 |

引脚必须由器件/网表对应，不依赖同名模型默认顺序：AO4409实体S=1/2/3、G=4、D=5/6/7/8；三端MOS模型常用D/G/S（需逐模型核实）。AMS1117 SOT223实体1=GND、2/Tab=OUT、3=IN；宏模型接口顺序若取得需读.SUBCKT首行，不按物理脚号猜。

### 查询覆盖与证据

- 本地检查：LTspice展开库standard.mos和lib/sub全文搜索、安装lib.zip中的.mos/.lib/.sub/.cir/.mod全文搜索，均无`AO4409`或`AMS1117`命中。检查项目及D:/lceda-pro相关扩展名未发现这两器件模型。只说明**已检范围未找到**，不保证整个磁盘或网络不存在。
- [AOS原厂AO4409数据手册](https://www.aosmd.com/sites/default/files/res/datasheets/AO4409.pdf)由此前审计取得，记录于[电源资料](<D:/smart_fans/docs/hardware/power_5v_revision.md#L30>)；数据手册不是SPICE模型。保证Rds(on)条件和热条件必须保留，不能把典型曲线拟合当最坏值保证。
- 本次尝试AOS旧资源风格的`https://www.aosmd.com/sites/default/files/res/spice_models/AO4409.lib`及同名.zip均HTTP404，猜测产品路径返回页面内404。搜索未找到可验证厂商模型，不使用第三方/其他厂同名AO4409模型替代。
- [LCSC C6186资料PDF](https://atta.szlcsc.com/upload/public/pdf/source/20180727/C6186_7A095716F0823C02F1997A905E26C086.pdf)从当前料号页取得链接；它是数据手册，不是模型。网上搜索中出现其他厂相似型号及非厂家生成内容，均未收作准确模型。

## 4. 仿真结果分级要求

1. **理想元件测试**：RC上升时间等，可与解析公式相互核验；负载和寄生参数未知时只能报告参数扫描与条件边界。
2. **工程近似/行为模型**：必须保存模型定义、来源参数、假设和未建模项，不能写“厂家模型通过”。
3. **准确厂商模型**：须保存来源、模型版本/哈希、许可、接口脚序及求解器兼容性；即使收敛，也不等于该批物料、PCB寄生与热设计已实测。
4. **无模型/超模型范围**：AMS环路稳定性、MCU固件、ASR识别、真实电机堵转/再生、连续舵机限角、线束装配及保险分断协调不在本RC验证范围。不得把网表能运行扩展为整机通过。

## 5. 可复核文件

- [只读库存脚本](<D:/smart_fans/artifacts/simulation_review/inspect_solver_inventory.py>)：提取程序/证据哈希、许可证PDF、扫描安装模型zip。
- RC网表SHA256：`94e16fe3fb15395ac7ed5c74030aaa71e539af5975fbd807352e43a82da2a02f`
- RC日志SHA256：`5519c2fb1eddb105396dc1d768e669569bbac2549b09830462842571b62d0dcf`
- RC波形SHA256：`a78d2a6895e26407ff56fc6093c68fef00c9fc5b6772d9d18920701958fe2850`

本任务无后台作业，无未收取进程；没有重新跑整板验收、没有安装软件、没有改变放行状态。
