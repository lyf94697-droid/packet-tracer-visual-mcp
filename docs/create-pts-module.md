# 生成 Packet Tracer `.pts` 模块

旧的 `cisco-pt-mcp` 能直接添加，是因为它已经带了一个 Packet Tracer 导出的 `.pts` 持久模块。

本项目源码目录已经准备好，路径是：

```text
E:\mc\packet-tracer-visual-mcp\extension\source
```

`.pts` 不是普通压缩包，也不是把 `.js` 改后缀就行。它必须由 Packet Tracer 自己导出。

## 推荐流程

1. 打开 Packet Tracer。
2. 进入：

```text
扩展 > 脚本 > 新建PT脚本模块...
```

3. 在 `信息` 或 `概括` 页签里，把模块名改成：

```text
PT Visual MCP
```

4. 在 `脚本引擎` 页签，导入这些 JS 文件：

```text
E:\mc\packet-tracer-visual-mcp\extension\source\pt_api.js
E:\mc\packet-tracer-visual-mcp\extension\source\runcode.js
E:\mc\packet-tracer-visual-mcp\extension\source\window.js
E:\mc\packet-tracer-visual-mcp\extension\source\main.js
```

如果 Packet Tracer 支持 `导入目录`，也可以直接导入：

```text
E:\mc\packet-tracer-visual-mcp\extension\source
```

5. 切到 `自定义接口` 页签，导入接口目录：

```text
E:\mc\packet-tracer-visual-mcp\extension\source\interface
```

导入后应该至少包含：

```text
index.html
bridge.js
```

6. 在 `概括` 页签里打开需要的权限。优先勾选：

```text
Application / App Window
Menu / Menu Bar
Web View
Network
IPC
```

如果看不懂具体权限名，第一次可以先全勾。

7. 点 `导出`，保存为：

```text
E:\mc\packet-tracer-visual-mcp\extension\packet-tracer-visual-mcp.pts
```

8. 回到 Packet Tracer 主界面，进入：

```text
扩展 > 脚本 > 配置PT脚本模块...
```

9. 点 `添加`，选择刚导出的：

```text
E:\mc\packet-tracer-visual-mcp\extension\packet-tracer-visual-mcp.pts
```

10. 重启 Packet Tracer。

11. 打开：

```text
扩展 > PT Visual MCP
```

如果菜单出现并能打开窗口，就说明 `.pts` 模块安装成功。

## 诊断脚本

如果你怀疑 Packet Tracer 没有执行脚本，可以先导入这个最小诊断脚本：

```text
E:\mc\packet-tracer-visual-mcp\extension\ptv-smoke-test.js
```

正常情况下，`扩展` 菜单里会出现：

```text
PTV SMOKE TEST OK
```

如果这个都不出现，说明不是主脚本问题，而是当前 Script Module 没有真正运行或没有菜单权限。

## 为什么不能直接生成

Packet Tracer 的 `.pts` 是私有二进制格式。旧 MCP 的 `.pts` 也不是 zip 或明文脚本包，里面看不到 JS、HTML 或菜单名。  
所以最稳的方式是：源码由本仓库提供，最终 `.pts` 由 Packet Tracer 自己导出。
