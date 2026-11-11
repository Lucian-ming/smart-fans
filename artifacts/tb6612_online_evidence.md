# TB6612 双排模块网上证据审查

日期：2026-11-04。范围：只读研究江协/江科协 STM32 套件所用双1×8 TB6612 模块，未修改设计或生成器。

## 结论

**未找到足以把“排距15.24mm、针距2.54mm、指定顶视针序、板框”全部绑定到用户持有版本的公开证据，不能签核直插封装。** 双1×8和TB6612型号不是机械标准；有明确官方反例，其排距为12.70mm、板宽才是15.24mm。

用户本地图片的候选排列仍为：控制排PWMA/AIN2/AIN1/STBY/BIN1/BIN2/PWMB/GND；功率排VM/VCC/GND/AO1/AO2/BO2/BO1/GND。它没有在本次网上研究中提升为已确认实物顶视针序。尤其要确定芯片面朝上还是丝印面朝上，以及排针从哪一面焊出。

## 来源与证据等级

### 1. 与江协课程有关系，但属于第三方复刻，非原厂模块机械图

- [PID入门套件PCB板复刻](https://oshwhub.com/zanfi1010/pid-ru-men-tao-jian-pcb-ban-fu-ke-jiang-xie-ke-ji)。页面作者称基于江协科技PID入门PCB底板复刻修改；正文明确：“为方便看到TB6612模块的丝印，TB6612模块排针焊接时，须将芯片朝下、丝印朝上”。这是**安装视角风险的直接证据**，不是本用户模块排距证据。公开页面显示设计图未生成预览图、暂无BOM、暂无3D模型、暂无附件；未取得可核坐标的PCB。
- [PID电机控制底板_江协科技同款](https://oshwhub.com/id_shift/pid-dian-ji-kong-zhi-_-zai-xian)。作者自述根据江协公开原理图复刻底板，并指向江协官方淘宝整套套件。该页没有模块排距/板框尺寸文字；第三方复刻不自动等于用户实物。

本地保存页面正文：[复刻正文](<D:/smart_fans/artifacts/tb6612_web_sources/pid_clone.clean.txt>)、[同款底板正文](<D:/smart_fans/artifacts/tb6612_web_sources/pid_same.clean.txt>)。原始HTML同目录，抓取脚本与解析脚本仅用于保存公开静态内容，没有登录或绕过权限。

### 2. 官方厂家明确证明“同芯片、双排”不代表同排距

[Pololu #713 官方产品页](https://www.pololu.com/product-info-merged/713)明确写：

> The distance between the header rows on the PCB is 0.1\" smaller than a standard 0.6\" DIP package.

因此该型号排中心距 = (0.6−0.1)×25.4 = **12.70mm**。同页：

- 两个1×8排针（或1×16可掰开），0.1英寸针距 = **2.54mm**；
- Size 0.60×0.80英寸 = **15.24×20.32mm板框**；
- 带板底尺寸图、[机械尺寸PDF](https://www.pololu.com/file/0J1724/tb6612fng-dual-motor-driver-carrier-dimensions.pdf)、[孔位DXF](https://www.pololu.com/file/0J1726/md08a-drill.dxf)链接。

**没有证据用户持有Pololu #713，不采用此尺寸替换现有设计。** 此来源仅用于排除“TB6612一律排距15.24”的推断，并提示15.24可能是板宽误读。

### 3. 其他模块资料：无法对应江协具体采购版本

- [立创开发板技术文档中心TB6612模块](https://openkits-wiki.easyeda.com/zh-hans/hspi-d133ebs/module/control/tb6612-motor-drive-module.html)：有模块采购链接、接线/程序及VM<12V、VCC2.7~5.5V等参数。不是江协官方模块机械尺寸图，不能以此证明排距。
- [异方辰电子TB6612教学](https://www.yfcdz.cn/sys-nd/73.html)：有实物图、原理图和接口说明图，非江协官方，未获得可确认版本的尺寸文字；峰值/连续电流等描述不能替代电机额定参数或热验证。
- [DFRobot DRI0044商品页](https://mall.dfrobot.com.cn/goods-1634.html)：具有明确货号和尺寸图入口，但没有证据与用户版本相同，未借用尺寸。
- [SunFounder旧Wiki](http://wiki.sunfounder.cc/index.php?title=TB6612_DC_Motor_Driver_Module)：搜索可见，实际抓取多次连接失败，未取得正文，不以搜索片段确认15.24。

本次没有找到可验证身份的江协官方模块PCB/Gerber仓库。搜索命中的“15.24”还包括KiCad**符号文字坐标**，不能当机械排距。

## 建议最小确认方式

1. 两排孔/针中心距离实测，必须区分板宽；如为2.54mm网格，15.24是6格，12.70是5格，可用已知2.54排针/洞洞板对比。先断电，不为确认尺寸通电。
2. 一排第1到第8针中心跨度应17.78mm（若2.54针距），同时测板框长宽。
3. 清晰正反面照片，记录从上方看最终插到母板后的控制排和功率排，以及第一针角落。不能把底视标签直接镜像复制到母板顶视。
4. 或由用户原采购商提供对应版本尺寸图/封装文件并确认与手中板一致。

在上述确认前，15.24可保留为设计假设，但交付报告必须标注未验证，不可宣告直插装配通过。

## 工具与读取限制

浏览器列表没有可用browser lane连接；new-tab调用因schema强制窗口字段冲突返回INVALID_ARGUMENTS，未改动用户浏览器。后续使用公开静态HTTP页面。当前模型图像输入不可用，未宣称对商品图片做视觉核验。本轮未改主文件、未运行PCB重建、没有后台任务。
