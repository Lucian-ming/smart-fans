# EC11 2+3接口网上证据检索

2026-11-04。用户已确认实物为2+3版本；本次只研究，未改主文件。**尚未找到能唯一绑定该江协/江科协套件实物的PCB源码、带孔中心坐标的机械图或明确SKU，因此不能据网上相似EC11填入直插封装。**

## 可确认与仍未知

|项目|结果|证据强度|
|---|---|---|
|接口分组|2针电源与3针信号|用户直接确认，结合本地说明OCR，强|
|信号身份|本地说明为VCC/GND及A/B/C(GND)|本地OCR两次一致；C接地，不作SW|
|单组针距|未取得同款可追踪数值|未知，不能借另一产品2.54mm作证明|
|两组相对xy/板框/轴心|未取得；本地24mm不能可靠绑定轴向|未知|
|按压输出|此五个已命名端口不含独立SW；不能实现现有假定的SW输入|接口功能结论；不等于裸EC11内部绝无按压触点|
|3.3V供电|未取得同款模块原理图/额定范围或实测|未知；不能用一般无源编码器知识替代载板电路|

## 已实读来源及排除理由

1. [幼智汇/Krduino旋转编码器模块](https://wiki.stemedu.cc/G/M/Encoder.html)，HTTP200全文。明确接口G/V/SW/DT/CLK，板50×24mm、接口2.54、额定4.5–5.5V、带按压输出。**与用户2P电源+3P A/B/C不一致，排除为同款**；24mm这个共同尺寸并不能绑定产品。该页甚至按压高/松开低，说明泛用教程电路也存在差异。
2. [2015 Arduino编码器实测文章](https://www.cnblogs.com/conexpress/p/4984802.html)，HTTP200全文。明确VCC/GND/SW/CLK/DT，五针且SW按下接地。**单排带SW型，排除**；不借其针距/电气行为。
3. [EC11的中断实验——NVIC&EXTI](https://www.cnblogs.com/FBsharl/p/18185147)，HTTP200全文。介绍裸器件A/B/C公共端与D/E按压端，及有/无上拉的不同电路。可作一般原理背景：C是公共端，DE才是按压触点；**不是本模块原理图，不能证明用户板按压端引出或3.3V供电**。
4. [立创开源EC11编码器模块](https://oshwhub.com/laobainb/ec11-bian-ma-qi-mo-kuai)，HTTP200但抓取只有标题，没有取得PCB、原理图、版本和尺寸；**仅候选，不可用于设计数值**。
5. [京东公共资源旋转编码器PDF](https://storage.360buyimg.com/ivc-img/1721442501800.pdf)，公开HTTP下载成功，8页，pypdf全文均为空。它可能是图像说明，但模型不可读图，未取得可校验文字/尺寸，**不宣称匹配本地说明图**。
6. [立创梁山派EC11教程](https://wiki.lckfb.com/zh-hans/lspi/module/sensor/ec11.html)，web_fetch失败TypeError；未读取，不引用其内容作为证据。
7. [江科大/江协STM32 P19笔记候选](https://www.ppmy.cn/embedded/92728.html)，403；[旋转编码器原理候选](https://blog.csdn.net/qq_74083494/article/details/135830647)，521。搜索摘要不能代替全文原理图。
8. [RoboticsBD 360 Potentiometer候选](https://store.roboticsbd.com/keypad-touch-switch-potentiometer-human-interface/2411-360-potentiometer-knob-rotary-encoder-module-robotics-bangladesh.html)，403 Cloudflare；未绕过。另一个商品候选返回404，不能作为现货SKU。

检索覆盖江协/江科协、GitHub教程仓库、EC11+A/B/C/VCC/GND、2P/3P、24mm、中文商品和英文rotary encoder module等组合；未得到同款源工程。不能把“未搜到”写成“网上不存在”。

## 可执行最小方案（需父代理/用户选择，不在本次实施）

- **要求直接插装：**必须得到实际板对应的机械尺寸/孔中心坐标或测量；公开资料缺口未闭环，不能猜2.54/24×某值。
- **希望不再等待尺寸而继续母板：**改母板为明确线束端口，2P VCC/GND及3P A/B/GND，丝印写端点功能而非假称同款机械封装。端子位置是母板设计选择，不是声称复刻模块孔位；采用可拆逐线杜邦线可避开模块两组间相对坐标要求。连接前仍核实每根丝印，不把C接SW。
- 独立ENC_SW不应由此模块凭空提供；删除对它的功能依赖，或保留单独两针开关接口给实际按键，需用户确认功能替代。
- 3.3V：若模块确为A/B触点拉地+电阻上拉到VCC，3.3V会产生匹配电平；但这只是条件分析，不是本模块已证电路。未知载板不应直接用5V上拉信号送3.3V MCU；上电前以原理图、万用表/示波器或限流低压试验确认。

本地来源：[说明PNG](<E:/桌面/原理图/11-旋转编码器/旋转编码器模块使用说明.png>)、[原OCR](<D:/smart_fans/artifacts/user_module_sources/ocr.json>)、[旋转OCR](<D:/smart_fans/artifacts/user_module_sources/ocr_rotated.json>)。当前模型图片输入不可用，未伪称已视觉核对商品照片。
