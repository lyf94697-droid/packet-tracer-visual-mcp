# 常用提示词

这些提示词可以直接拿去给 Codex 用。

## 生成完整校园网配置

```text
使用 PT Visual MCP 生成完整校园网 IOS 配置，要求使用 OSPF、IOS DHCP 地址池、ACL 和 NAT/PAT。先预览配置，不要直接下发。
```

## 对比多种路由协议

```text
生成同一个校园网的四套 IOS 配置：静态路由、RIP、OSPF、EIGRP。告诉我四种方案主要差在哪里。
```

## 下发配置

```text
Packet Tracer 拓扑已经存在，PT Visual MCP bridge 已经 connected。请下发完整校园网 IOS 配置：routingProtocol ospf，dhcpMode ios，开启 ACL 和 NAT/PAT。
```

## 故障演示

```text
列出内置故障库，然后注入 OSPF area mismatch 故障。等我测试完后，再修复这个故障，并给出验证命令。
```

## 快速课设录屏

```text
使用 PT Visual MCP 快速搭建复杂校园网课设拓扑：qualityMode fast-safe，deviceDelayMs 40，linkDelayMs 20，autoAssignPorts true，configureDevices false。拓扑搭完后运行 fast 验收，并总结设备数量、链路数量、VLAN 覆盖、路由方案、NAT/PAT、ACL 测试、Server-PT 手动服务步骤和调试案例。
```

## 自动端口

```text
创建链路时使用自动端口分配。我只提供 fromDevice 和 toDevice，你选择空闲以太网端口，批量连线时不要复用端口，并告诉我最终分配了哪些接口。
```

## 最终验收计划

```text
生成校园网 standard 验收计划，routingProtocol ospf，dhcpMode ios，开启 NAT/PAT 和 ACL。先不要执行慢检查，先把命令清单给我。
```

## 探测 Server-PT 服务接口

```text
使用 ptv_probeServerServices 探测当前画布里的 Server-PT，看看 Packet Tracer 是否暴露了 DNS、HTTP、FTP、DHCP 服务配置相关 API。只读探测，不要修改任何服务。
```
