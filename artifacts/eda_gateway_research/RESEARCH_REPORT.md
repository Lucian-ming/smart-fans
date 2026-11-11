# 嘉立创 EDA 接入只读研究

研究日期：2026-11-04。仅通过 GitHub REST API 下载 README、元数据、源代码与 API 文档，静态阅读；未安装插件、npm依赖，未启动桥、运行仓库代码、连接EDA或修改应用设置。这里的功能结论不是实机测试。

## 更新：本机4.1.93内置官方CLI/MCP（覆盖前述旧桥首选建议）

后续核实官方新版CLI文档 https://prodocs.easyeda.com/en/api/guide/cli.html ：4.1.60起客户端内置CLI及MCP，无需3.2旧Gateway。实机 `D:/lceda-pro/lceda-pro.exe doctor` 返回ok=true、connected=true、bridgeVersion=4.1.93.be2a4d1d、versionMatch=true、resultChannel=true；`--help`与`--mcp --help`确有stdio及HTTP（host默认127.0.0.1、token、cors）模式。故当前首选本机官方实现，不再安装旧桥；前述对旧Gateway无认证等结论不应套用于新版内置MCP。

原生导入API `SYS_FileManager.importProjectByProjectFile`支持KiCad、Offline Client Local Path、EPRJ3和同名不覆盖。已开独立空白headless会话3627140e-9c06-4b0e-a18f-3a0f58f1fe2f；首次包含SYS_FileSystem.getProjectsPaths的只读invoke返回ok=false：`EXECUTION_ERROR: 错误：未启用扩展和独立脚本的外部交互权限！`。没有冒充内置扩展绕过，也没有导入或修改用户工程；该会话已正常close --destroy、返回status=closed。需用户在应用中明确启用外部交互权限后继续。尚未执行原生DRC/仿真，不得把doctor通过当工程通过。

## 结论

建议优先评估 **官方 Run API Gateway + easyeda-api-skill**；它是 HTTP/WebSocket + Agent Skill，不是原生 MCP Server。若宿主必须 MCP，可另评估社区 hyl64/jlcmcp，但**不能把其DRC包装返回 passed 当生产验收**。绘制/改板与读取原生DRC结果有文档路径；**未证实有完整内置SPICE启动、收敛判断和波形读取闭环**，不能承诺一键仿真整个风扇控制器。

## 身份与快照

- [easyeda/eext-run-api-gateway](https://github.com/easyeda/eext-run-api-gateway)：EasyEDA组织仓库，扩展manifest publisher=EasyEDA，开发包author=JLCEDA/support@lceda.cn，首页pro.lceda.cn；官方生态来源，与组织发布的skill相互引用。扩展版本 **1.0.6**；注意根package版本1.3.2是SDK工程版本，不是扩展版本。提交 `79db40a1e2f6a069c834c7c16765e2f74f2968a7`。
- [easyeda/easyeda-api-skill](https://github.com/easyeda/easyeda-api-skill)：同一EasyEDA组织发布，package **1.1.64**；提交 `8aa6c74b99bdfcbc9f8900e9cec07f1c70cfff14`。
- [hyl64/jlcmcp](https://github.com/hyl64/jlcmcp)：GitHub个人User hyl64的社区MCP，package **1.4.0**，MIT；提交 `5e53ddaa07e1763de6c1b17a82aafa2cb1476d4b`。README“官方栈迁移版”指改用官方桥，不等于官方开发/认证的MCP。
- GitHub组织API的easyeda字段is_verified=false，不应宣传“GitHub已验证组织”。扩展商店URL被两官方仓库引用：[oshwhub-official/run-api-gateway](https://jlcext.com/item/oshwhub-official/run-api-gateway)，本次该域抓取失败，未独立核对商店发布版本、签名或下载包哈希。

## 版本和安装路径（仅研究，未执行）

1. 官方README建议Node **22 LTS或更高**。Gateway源码构建包engine >=20.17.0；manifest `engines.eda="~3.2.0"`，应按具体版本核对，不能把社区“V3.2+”等同任意未来版本兼容。
2. 在嘉立创EDA专业版扩展市场装Run API Gateway，扩展管理器勾选“允许外部交互”“显示在顶部菜单”。这会开放控制通道，必须先取得用户授权。扩展激活点onStartupFinished，默认自动连接，应只在有需要时开启。
3. 获取并锁定官方skill版本，安装到宿主支持的Skill目录。Node依赖是 `ws ^8.21.3`；当前package唯一脚本 `server: node scripts/bridge-server.mjs`。README还提及 `build:docs`、`pack`、`server/index.mjs`，但当前树/package没有对应脚本/文件，**README有滞后，不可照抄这些命令**。当前references文档已在树内。
4. 经依赖审计与授权后才运行 npm install / npm run server，探测health并确认EDA窗口身份。DSH是否可直接注册这一Agent Skill/HTTP能力需按宿主配置确认，不能把“安装到其他AI工具路径”当DSH已接入。
5. 社区MCP另需 npm install、npm run build，然后stdio `node <绝对路径>/dist/index.js`；Node声明>=18、建议22（README），依赖 @modelcontextprotocol/sdk ^1.12.1、@anthropic-ai/sdk ^0.39.0、ws ^8.18.0、zod ^3.23.8。不需要安装其legacy插件。默认AUTO_SPAWN_BRIDGE=true，KILL_BRIDGE_ON_EXIT=0，即可自动拉起且退出后保留桥；首轮安全试验应显式关闭自动拉起并受控管理进程。
6. 普通工具不需要ANTHROPIC_API_KEY；仅pcb_agent需要，设置后内部调用Anthropic messages.create，工具结果/设计上下文可进入模型请求。不要为检查DRC随意添加云端API Key。

版本依据：[Gateway manifest](https://github.com/easyeda/eext-run-api-gateway/blob/79db40a1e2f6a069c834c7c16765e2f74f2968a7/extension.json#L1-L15)、[Gateway构建依赖](https://github.com/easyeda/eext-run-api-gateway/blob/79db40a1e2f6a069c834c7c16765e2f74f2968a7/package.json)、[skill package](https://github.com/easyeda/easyeda-api-skill/blob/8aa6c74b99bdfcbc9f8900e9cec07f1c70cfff14/package.json)、[社区package](https://github.com/hyl64/jlcmcp/blob/5e53ddaa07e1763de6c1b17a82aafa2cb1476d4b/package.json)。

## 端口、认证与安全

官方桥监听 **127.0.0.1**，扫描端口 **49620–49629**。HTTP GET /health、GET /eda-windows、POST /eda-windows/select、POST /execute；EDA连接 `ws://127.0.0.1:<port>/eda`，其他WS路径被当作agent。请求可指定windowId，否则用活动EDA窗口，必须显式选定工程/窗口防止改错图。

静态源码显示：
- `/execute`接收code后直接转发；无Bearer token、口令或每次用户确认验证。
- `Access-Control-Allow-Origin: *`，允许POST/GET/OPTIONS；WS连接处理未见Origin认证。
- handshake仅常量 `service: easyeda-bridge`，用于发现服务，**不是身份认证或加密挑战**。
- Gateway通过 `new AsyncFunction('eda', msg.code)` 执行代码；并非只读工具白名单。可以调用修改文档甚至扩展开放的其他API。
- loopback限制降低局域网暴露，但不能防本机恶意进程；宽松CORS带来网页访问本地服务风险，具体浏览器本地网络防护会影响可利用性，本次未测试。不要开放LAN、反向代理或端口转发；不应将其称为“已认证安全网关”。
- 社区vendored bridge同样有上述HTTP/CORS行为；GATEWAY_BASE_URL可指远端，需限制为loopback。无TLS保护的远端连接不应启用。

建议：只在独立工程副本上操作，启动前备份，先只读API白名单；确认windowId与项目名；完成即Stop Connection并关桥、关闭自动连接；不要让不可信页面/仓库文本直接产生execute代码。若要长期运行，应先审计/增加强认证及Origin约束，不能靠服务名握手替代。

源码：[官方bridge](https://github.com/easyeda/easyeda-api-skill/blob/8aa6c74b99bdfcbc9f8900e9cec07f1c70cfff14/scripts/bridge-server.mjs#L134-L250)、[官方执行器](https://github.com/easyeda/eext-run-api-gateway/blob/79db40a1e2f6a069c834c7c16765e2f74f2968a7/src/index.ts#L496-L502)、[社区客户端](https://github.com/hyl64/jlcmcp/blob/5e53ddaa07e1763de6c1b17a82aafa2cb1476d4b/src/gateway-client.ts)、[社区Agent外发](https://github.com/hyl64/jlcmcp/blob/5e53ddaa07e1763de6c1b17a82aafa2cb1476d4b/src/agent.ts#L420-L450)。

## DRC：有正式返回值，但社区包装有假通过风险

官方API文档（BETA）定义：
```typescript
// PCB 与 SCH 都提供该两种形态
check(strict: boolean, userInterface: boolean, includeVerboseError: false): Promise<boolean>;
// PCB true -> Promise<Array<any>>；SCH true -> Promise<Array<ISCH_DrcError>>
```
明确 `includeVerboseError=true` 返回**分组树**，顶层长度是错误类别数，不是违规总数。应执行显式三参的布尔门禁，再读详细树，保存原始JSON和当前规则/工程身份。异常、未支持、超时必须判“未完成”，不是通过。两次调用期间不得修改图纸。

社区generated.ts的runDRC虽然调用三参，但把顶层数组直接map、length当totalCount；更严重的是捕获所有调用异常后，如果passed仍undefined，就赋值 `normalized.length === 0`，因此可把API执行失败误报passed=true。SCH包装 `const result = await api.sch_Drc.check(strict, false); return {passed:Boolean(result)}` 未明确第三参、无明细；如果运行时默认返回数组，空/非空数组都为true。不能信任该包装作为验收证据。

推荐后续在授权实机测试中直接调用官方API，故意构造一处违规作为负对照，确认门禁false、明细含该违规，再恢复并检查。当前尚无实机通过率证据。

来源：[PCB_Drc](https://github.com/easyeda/easyeda-api-skill/blob/8aa6c74b99bdfcbc9f8900e9cec07f1c70cfff14/references/classes/PCB_Drc.md#L779-L941)、[SCH_Drc](https://github.com/easyeda/easyeda-api-skill/blob/8aa6c74b99bdfcbc9f8900e9cec07f1c70cfff14/references/classes/SCH_Drc.md)、[社区包装](https://github.com/hyl64/jlcmcp/blob/5e53ddaa07e1763de6c1b17a82aafa2cb1476d4b/src/codegen/generated.ts#L110-L137)。README宣称59工具及75协议断言只是作者声明；未运行且mock协议测试不证明真实EDA DRC准确。

## 仿真：不能把“推送结果”当“计算并读取结果”

[SCH_SimulationEngine](https://github.com/easyeda/easyeda-api-skill/blob/8aa6c74b99bdfcbc9f8900e9cec07f1c70cfff14/references/classes/SCH_SimulationEngine.md)仅列 `pushData(eventType, props): void`，例子人为推入SESSION_STATE、STREAM_DATA、SIMULATION_RESULT。它不返回波形，也不能证明内置引擎执行完成。

[SCH_Event.addSimulationEnginePullEventListener](https://github.com/easyeda/easyeda-api-skill/blob/8aa6c74b99bdfcbc9f8900e9cec07f1c70cfff14/references/classes/SCH_Event.md#L334-L442)能监听引擎拉取事件；SPICE pull enum是SIMULATE_NETLIST，push enum是SIMULATION_RESULT。这更像用于对接仿真引擎的协议接口，不是已证实的“startSimulation/getResults”端到端客户端。社区当前工具清单也没有独立仿真工具；任意代码工具不能凭空补足求解器与模型。

尚未知：本机EDA版本对这些BETA API的支持；当前可用SPICE引擎/模型；XL1509开关电源、驱动器、MCU/舵机/电机行为模型；启动、收敛、错误和波形导出方式。后续应先用简单RC电路验证真实计算与结果读取，再按子电路制定电源启动/纹波/负载阶跃测试。DRC只检测规则，不证明电气功能或电流温升。

## 对现有fan_ctrl_revB的接入门槛

先获得安装扩展、安装Node依赖、启动本地桥和接入DSH的明确授权；复制工程，验证KiCad到嘉立创导入后元件/引脚/网络/铺铜/层/单位未失真（社区坐标单位mil）；保留现有KiCad及独立检查为对照。另需用户确认PCB尺寸、模块/孔位/坐标基准以及按钮帽和轴向尺寸；桥接与仿真不能替代这些机械数据。

原始下载证据保存在 [研究目录](<D:/smart_fans/artifacts/eda_gateway_research>)，GitHub API返回内容按base64解码为文本/源码，未执行其中代码。
