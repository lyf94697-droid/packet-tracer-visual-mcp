# 校园网课程设计示例

这个示例对应常见《计算机网络课程设计》要求，目标是快速做出一个看起来像样、功能也够完整的中小型校园网。

## 覆盖内容

- VLAN：10、20、30、40、50、99。
- Access / Trunk 交换。
- 核心三层交换机做跨 VLAN。
- 支持静态路由、RIP、OSPF、EIGRP 配置生成。
- 支持 IOS DHCP 地址池，也可以切换成 DHCP relay 思路。
- 规划 DNS、Web、FTP 服务器区。
- 出口路由器做 NAT/PAT。
- 两条 ACL：一条拦 Web，一条拦 FTP。
- 自带连通性、服务、NAT、ACL、调试测试点。

## 快速录屏搭建

调用 `ptv_buildCampusRecordingDemo` 时可以用：

```json
{
  "qualityMode": "fast-safe",
  "deviceDelayMs": 40,
  "linkDelayMs": 20,
  "autoAssignPorts": true,
  "autoFallback": true,
  "configureDevices": false,
  "validatePlan": true,
  "verifyAfterBuild": true
}
```

这个模式会先把拓扑快速摆出来，同时保留基本校验，适合录屏宣传。

## 完整网络配置

拓扑存在后，再用 `ptv_generateCampusIosConfig` 或 `ptv_applyCampusIosConfig`：

```json
{
  "routingProtocol": "ospf",
  "dhcpMode": "ios",
  "includeNatPat": true,
  "includeAcl": true,
  "writeMemory": true
}
```

## 快速验收

搭完之后用 `ptv_validateCampusFast`：

```json
{
  "checkCanvas": true
}
```

`fast` 模式不会跑一大堆慢 `show` 命令，主要看拓扑有没有建全、构建有没有失败、关键设备和链路是否存在。

最后交课设前，可以生成慢一点但更细的验收计划：

```json
{
  "validationMode": "standard",
  "routingProtocol": "ospf",
  "dhcpMode": "ios"
}
```

## Server-PT 服务

Server-PT 的图形服务建议按下面手动确认：

- DNS：`www.campus.local -> 192.168.40.20`，`ftp.campus.local -> 192.168.40.30`
- HTTP：Web 服务器开启 HTTP
- FTP：FTP 服务器开启 FTP，添加 `ftpuser / cisco`

如果后续确认 Packet Tracer 脚本接口能稳定控制 Services 面板，可以再把这一步做成自动化工具。

可以先用 `ptv_probeServerServices` 做只读探测，看看当前 Packet Tracer 版本有没有暴露 DNS/HTTP/FTP 相关 API。
