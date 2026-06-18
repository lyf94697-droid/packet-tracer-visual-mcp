# Packet Tracer Visual MCP

这个项目是一个给 Packet Tracer 用的 MCP 工具。

说白了：以前你在 Packet Tracer 里要自己拖设备、连线、配路由、配 VLAN；现在可以让 Codex 通过 MCP 去干这些活。它特别适合计网课设、校园网实验、录屏演示、故障排查演示。

这个项目是独立实现，不是 Cisco 官方项目，也不冒充官方工具。

## 现在能做什么

- 读取 Packet Tracer 当前画布。
- 自动放设备，支持一台一台出现，录屏看起来比较直观。
- 自动连线，支持一条一条连。
- 自动分配端口，不用每条线都手写 `FastEthernet0/1` 这种接口。
- 内置一个中小型校园网模板：`33` 台设备，`34` 条链路。
- 自动生成完整 IOS 配置：
  - VLAN
  - Access / Trunk
  - 跨 VLAN 通信
  - 静态路由 / RIP / OSPF / EIGRP
  - DHCP
  - ACL
  - NAT/PAT
- 可以把 IOS 配置直接下发到 Packet Tracer 设备。
- 支持故障注入和修复演示，比如 OSPF 区域错误、ACL 误拦截、NAT 配错。
- 默认有 `fast` 快速验收，不会一上来跑一大堆慢 `show` 命令。
- 也能生成标准验收计划，适合最后交课设前慢慢查。

## 一行安装

目前还没发到 PyPI，所以先用 GitHub 安装最稳：

```powershell
git clone https://github.com/lyf94697-droid/packet-tracer-visual-mcp.git; cd packet-tracer-visual-mcp; python -m pip install -e .; python scripts\build_script_engine.py
```

然后把 MCP 配到 Codex：

```toml
[mcp_servers.packet-tracer-visual-mcp]
command = "pt-visual-mcp"
args = []
```

启动 MCP：

```powershell
pt-visual-mcp
```

## Packet Tracer 里怎么接上

先生成扩展脚本：

```powershell
python scripts\build_script_engine.py
```

然后在 Packet Tracer 里导入并运行：

```text
extension\packet-tracer-visual-mcp-script-engine.js
```

接着打开：

```text
Extensions > PT Visual MCP
```

窗口里显示 `connected` 就说明接上了。

默认连接地址是：

```text
ws://127.0.0.1:7541/ws
```

## 计网课设能覆盖到哪

内置校园网模板就是按常见计网课设来做的：

- 至少 4 个 VLAN：支持，默认有 VLAN 10/20/30/40/50/99。
- Access / Trunk：支持。
- 跨 VLAN 通信：支持。
- 静态路由或 OSPF：支持，还额外支持 RIP 和 EIGRP。
- DHCP：支持 IOS DHCP 池，也可以做 DHCP relay 方案。
- DNS / Web / FTP：服务器位置和地址规划支持，服务开关见下面说明。
- NAT/PAT：支持。
- ACL：支持，默认有两条允许/拒绝验证案例。
- 连通性测试、服务测试、NAT 测试、ACL 测试：会自动生成测试清单。
- 完整调试案例：支持，比如“VLAN30 不能访问 Web，但 DNS 正常”。

## Server-PT 图形服务说明

网络侧我已经能自动做：IP、网关、DNS、VLAN、路由、ACL、NAT/PAT 都可以走 MCP。

但 Packet Tracer 的 `Server-PT > Services` 面板比较特殊。DNS、HTTP、FTP 这些开关和用户添加，取决于 Packet Tracer Script Engine 有没有暴露稳定 API。

所以当前最稳的做法是：

- `SRV-DNS`：`Services > DNS > On`
  - `www.campus.local -> 192.168.40.20`
  - `ftp.campus.local -> 192.168.40.30`
- `SRV-WEB`：`Services > HTTP > On`
- `SRV-FTP`：`Services > FTP > On`
  - 用户：`ftpuser`
  - 密码：`cisco`

后续可以做一个实验功能：

- 先探测 Server-PT 设备对象到底暴露了哪些服务相关方法。
- 如果有稳定 API，就加 `ptv_configureServerServices`，自动开 DNS/HTTP/FTP。
- 如果没有稳定 API，就不硬吹自动化；最多提供手动步骤或非默认的 GUI 点击方案。

## 常用 MCP 工具

基础操作：

- `ptv_bridgeStatus`
- `ptv_getNetwork`
- `ptv_addDevice`
- `ptv_addDevicesTimeline`
- `ptv_addLink`
- `ptv_addLinksTimeline`
- `ptv_configurePc`
- `ptv_configureIos`

校园网和配置：

- `ptv_getCampusPlan`
- `ptv_buildCampusRecordingDemo`
- `ptv_generateCampusIosConfig`
- `ptv_applyCampusIosConfig`
- `ptv_generateIosTemplate`
- `ptv_applyIosConfigSet`

验收和排错：

- `ptv_validateCampusFast`
- `ptv_generateCampusValidationPlan`
- `ptv_getCommandLog`
- `ptv_runShowCommands`
- `ptv_getFaultLibrary`
- `ptv_injectFault`
- `ptv_repairFault`

## 快速录屏推荐参数

想要“看起来很快，但别乱掉”，推荐：

```json
{
  "qualityMode": "fast-safe",
  "deviceDelayMs": 40,
  "linkDelayMs": 20,
  "autoAssignPorts": true,
  "autoFallback": true,
  "validatePlan": true,
  "verifyAfterBuild": true,
  "configureDevices": false
}
```

如果要顺手下发配置，把 `configureDevices` 改成 `true`，但会比单纯摆拓扑慢。

## 验收模式

- `fast`：默认模式。看拓扑是否建全、构建有没有失败、关键设备和链路是否存在。不跑重型 `show` 命令。
- `standard`：生成 VLAN、Trunk、路由、DHCP、NAT、ACL 的命令检查计划。
- `strict`：更适合最后交付前慢慢验。
- `off`：不验收。

录屏和快速生成用 `fast`，答辩前再用 `standard` 或 `strict`。

## 示例

课程设计示例看这里：

```text
examples/campus-course-design.md
```

常用提示词看这里：

```text
examples/prompts.md
```

## 本地自检

```powershell
python -m pip install -e .
python scripts\check_project.py
python -m compileall src scripts
python scripts\build_script_engine.py
node --check extension\source\pt_api.js
node --check extension\source\interface\bridge.js
node --check extension\packet-tracer-visual-mcp-script-engine.js
```

自检通过时会看到类似：

```text
project check passed: 21 tools, 33 devices, 34 links
```

## 项目结构

```text
packet-tracer-visual-mcp/
  src/pt_visual_mcp/         MCP 服务端和 WebSocket 桥接
  extension/source/          Packet Tracer 扩展源码
  extension/*.js             可导入 Packet Tracer 的脚本
  skill/SKILL.md             Codex 技能说明
  examples/                  示例提示词和课设示例
  docs/                      功能说明和开发笔记
  scripts/check_project.py   项目自检脚本
```

## 许可证

MIT License。

如果你基于别人的 MIT 项目继续改，记得保留对方的协议和署名。这个仓库当前定位是一个干净的原创实现，重点是 Packet Tracer 可视化拓扑生成、课程设计预设和 IOS 自动化。
