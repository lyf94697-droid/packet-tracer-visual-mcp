# 参与贡献

欢迎提交新的 Packet Tracer 实验模板、IOS 配置模板、验收方案、故障案例和扩展脚本改进。

## 本地检查

提交前建议跑一遍：

```powershell
python -m pip install -e .
python scripts\check_project.py
python scripts\build_script_engine.py
node --check extension\source\pt_api.js
node --check extension\source\interface\bridge.js
node --check extension\packet-tracer-visual-mcp-script-engine.js
```

## 基本约定

- MCP 工具名统一用 `ptv_` 前缀。
- 优先走 Packet Tracer 脚本接口，不把鼠标点击当成核心方案。
- `fast` 验收要保持快，不要塞一堆重型 `show` 命令。
- 慢检查放到 `standard` 或 `strict`。
- 不要写成 Cisco 官方项目。
- 如果新增 Packet Tracer Script Engine 能力，要把接口限制写清楚。
