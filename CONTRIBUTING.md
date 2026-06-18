# Contributing

Contributions are welcome for Packet Tracer lab presets, IOS templates, validation profiles, and extension improvements.

## Local Check

Run:

```powershell
python -m pip install -e .
python scripts\check_project.py
python scripts\build_script_engine.py
node --check extension\source\pt_api.js
node --check extension\source\interface\bridge.js
node --check extension\packet-tracer-visual-mcp-script-engine.js
```

## Design Rules

- Keep the MCP tool names under the `ptv_` prefix.
- Prefer explicit, reproducible lab plans over mouse automation.
- Keep `fast` validation quick; reserve command-heavy checks for `standard` or `strict`.
- Do not claim Cisco affiliation.
- Document Packet Tracer Script Engine limitations when adding new bridge APIs.
