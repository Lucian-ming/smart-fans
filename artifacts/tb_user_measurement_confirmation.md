# TB6612 用户实测确认与源接口变更

2026-11-04用户经父会话确认：两排中心距约15mm；左从上PWMA/AIN2/AIN1/STBY/BIN1/BIN2/PWMB/GND，右从上VM/VCC/GND/AO1/AO2/BO2/BO1/GND。该实物证据替代此前网上无法确定排距的未决状态；它不是精密机械图，不能宣称厂家公差。

## 采用值
- 按明确授权使用15.00mm，不自行归整15.24mm；同排针距维持2.54mm。
- J_TB_L中心(7.88,36.00)，J_TB_R中心(22.88,36.00)，右排由23.12左移0.24mm，左排不动。
- 两排均使用PinSocket_1x08_P2.54mm_Vertical库标识；实际焊盘仍由生成器自定义。
- 低Y端为用户报告的顶部，pad1到8依次向高Y排列；用户针序与现有电气映射一致，无需交换网络。
- VM保持+5V，VCC保持+3.3V；AO1/2分别去MOTO1.1/2；B通道BIN1/BIN2/PWMB接GND，BO2/BO1保持NC。
- 粗测值对应装配应先试插，必要时轻微成形；不能宣称用户已用量具证明15.00精确值。

## 验证
[test_tb6612_interface_ast.py](../tools/test_tb6612_interface_ast.py)只读取AST，不执行主生成器。正例通过，六种负例均拒绝：擅改15.24mm、VM接12V、VCC接5V、AO颠倒、B输出接地、单排上下镜像。结果[tb_interface_ast_validation.json](tb_interface_ast_validation.json)。

仅修改主生成器TB区注释、右排X和两排母库标识；未全build、未改其他代理EC区或布线调用。模块板框/朝下器件高度仍未量测，AST不等于重新生成后的制造或全装配通过。
