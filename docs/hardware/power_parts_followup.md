# 电源与连接器补证（2026-11-04）

仅研究，未改主文件或构建。

## DC1
[授权分销Proax](https://proax.ca/en/product/174065/phx1729128)实读：1729128准确型号MKDSN 1,5/ 2-5,08（旧MKDS漏N）；pitch5.08mm、推荐孔1.3mm、pin标称0.5×1mm、脚长3.5mm、壳宽10.16×深8.15×板上高10mm，总高13.5mm。电流17.5A须遵守降额。当前孔距/孔径一致；旧MKDS库外形10.16×9.8不是本型号准确包络。pin最大公差及针排相对壳体偏置未核，标称矩形对角1.118mm不能作最大公差验收。
[RS1](https://docs.rs-online.com/cb9e/0900766b817142b8.pdf)、[RS2](https://docs.rs-online.com/f261/0900766b8171564d.pdf)、Phoenix及Marutsu均403，未成功下载原厂尺寸PDF。

## F1
[Brevan](https://www.brevan.com/0451003-mrl/)正文实读：0451003.MRL，3A、125VAC/VDC、Breaking Capacity @ Rated Voltage 50A。其链接原厂451/453 PDF未取得可提取正文；原厂推荐pad、I²t/时间电流和温度降额仍未闭环。先前KiCad库pad1.96×3.15mm、中心±2.455mm不能升级为原厂双证据PASS。50A分断不代表5V适配器故障保护协调通过。

## XH-2PA
[精确绘图](https://atta.szlcsc.com/upload/public/pdf/source/20221111/941C48A64A881023E1ECD9BB647261A0.pdf)HTTP200+pypdf实读：2P表A7.5/B2.5，pitch2.5，pin0.6±0.02mm；未注公差±.15/角±1.5°；文本含高7/深5.7。文本未提取到推荐孔径，不能宣称图纸给出1.0mm钻孔。若为方针，最大边长.62、对角.8768mm，1mm成品孔仅.1232mm直径余量，尚未减孔公差/位置误差；须视觉复核图纸孔位与实物。

## C2081 / 2N3904
[精确商品](https://item.szlcsc.com/2438.html)绑定[PDF](https://atta.szlcsc.com/upload/public/pdf/source/20141125/1457707246937.pdf)200实读：JIANGSU CHANGJIANG ELECTRONICS，2N3904 B.Mar2012，TO92；1.EMITTER/2.BASE/3.COLLECTOR；hFE Y档200–300。IC连续.2A，VCEO40V；VCEsat≤.3V于IC50mA/IB5mA。该PDF2页无机械表，±2.54mm外脚须明确wide/成形，不可声称普通直脚间距。可取的JSCJ AD-2N3904是不同车规AD版本，不能代替非AD精确料号尺寸。
