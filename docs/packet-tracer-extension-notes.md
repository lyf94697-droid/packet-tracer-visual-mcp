# Packet Tracer Extension Notes

Packet Tracer script packaging differs by version. This repository keeps the extension as source files so it can be audited and repackaged cleanly.

## Source Files

- `source/main.js`: adds `Extensions > PT Visual MCP`.
- `source/window.js`: opens the bridge webview.
- `source/runcode.js`: safe wrapper used by the webview to execute PT-side code.
- `source/pt_api.js`: Packet Tracer canvas operations.
- `source/interface/index.html`: bridge UI.
- `source/interface/bridge.js`: WebSocket client and timeline scheduler.

## Runtime Flow

1. Codex calls an MCP tool such as `ptv_buildCampusRecordingDemo`.
2. The MCP server sends JSON to the Packet Tracer extension over WebSocket.
3. The webview receives the request and schedules one PT operation at a time.
4. The webview calls `$se("ptvRunCode", "...")` to execute PT-side canvas actions.
5. Results are returned to the MCP server as JSON.

## Why WebSocket Instead Of Socket.IO

The original design goal is a clean implementation with a small protocol:

```json
{"type":"call","id":"...","action":"addDevice","payload":{}}
{"type":"result","id":"...","ok":true,"data":{}}
```

This keeps the bridge easy to inspect, document, and reimplement.

## Local Script Engine Build

Packet Tracer `.pts` packaging is version-dependent and not documented as a stable open format. For an auditable open-source release, use the local Script Engine build:

```powershell
cd E:\mc\packet-tracer-visual-mcp
python scripts\build_script_engine.py
```

Then import and run:

```text
extension\packet-tracer-visual-mcp-script-engine.js
```

The generated file points Packet Tracer to `extension/source/interface/index.html` by absolute `file:///` URL. If the project directory moves, regenerate the file.

Publishing a prebuilt `.pts` can be added later only if the packaging method is reproducible and does not include Packet Tracer proprietary files.

Do not publish Cisco installers or Packet Tracer proprietary files.
