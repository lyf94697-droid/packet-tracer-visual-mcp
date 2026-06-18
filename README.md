# Packet Tracer Lab MCP

Original MCP bridge for Cisco Packet Tracer lab generation and IOS automation.

This project exposes `ptv_*` MCP tools, connects to a Packet Tracer extension over WebSocket, builds campus-network labs, generates complete IOS configurations, applies those configurations, and supports fault injection/repair demos for teaching and course design.

It is an independent project and is not affiliated with Cisco.

## What It Does

- Adds Packet Tracer devices one by one with controllable delay.
- Adds links one by one with controllable delay.
- Builds a campus-network demo preset:
  - VLAN 10/20/30/40/50/99
  - Access and trunk links
  - Inter-VLAN routing
  - OSPF
  - DHCP relay/server placement
  - DNS/Web/FTP server placement
  - NAT/PAT edge design
  - Two ACL verification cases
- Generates and applies complete IOS config sets.
- Supports static routing, RIP, OSPF, and EIGRP templates.
- Supports IOS DHCP pools, extended ACL templates, and NAT/PAT templates.
- Provides fault injection and repair scenarios for debugging demos.
- Supports fast-safe topology builds with preflight validation, short retries, settle time, and post-build verification.
- Supports automatic link port allocation and fixed-port fallback.
- Supports fast campus validation by default: no heavy show-command sweep, just build/apply status plus one optional canvas snapshot.
- Generates service steps and test checklist for course-design labs.

## Quick Start

One-line install from GitHub:

```powershell
git clone https://github.com/lyf94697-droid/packet-tracer-visual-mcp.git; cd packet-tracer-visual-mcp; python -m pip install -e .; python scripts\build_script_engine.py
```

Then add the MCP server to Codex:

```toml
[mcp_servers.packet-tracer-visual-mcp]
command = "pt-visual-mcp"
args = []
```

Local development install:

```powershell
cd E:\mc\packet-tracer-visual-mcp
python -m pip install -e .
python scripts\check_project.py
python scripts\build_script_engine.py
pt-visual-mcp
```

Then open Packet Tracer, import and run:

```text
extension\packet-tracer-visual-mcp-script-engine.js
```

Open `Extensions > PT Visual MCP`. The bridge window should show `connected`.

## Project Shape

```text
packet-tracer-visual-mcp/
  src/pt_visual_mcp/        Python MCP server and WebSocket bridge
  extension/source/         Packet Tracer extension source
  skill/SKILL.md            Codex skill instructions
  examples/                 Config snippets and example prompts
  docs/                     Notes for packaging and roadmap
  scripts/check_project.py   Lightweight project self-check
```

## Install For Local Development

```powershell
cd E:\mc\packet-tracer-visual-mcp
python -m pip install -e .
pt-visual-mcp --help
```

## Codex MCP Config

Add this to `C:\Users\lyfhf\.codex\config.toml` after the package is installed:

```toml
[mcp_servers.packet-tracer-visual-mcp]
command = "pt-visual-mcp"
args = []
```

For `uvx` publishing later, use:

```toml
[mcp_servers.packet-tracer-visual-mcp]
command = "uvx"
args = ["packet-tracer-visual-mcp"]
```

Until the package is published to PyPI, prefer the GitHub clone command above because the Packet Tracer extension files are part of the repository.

## Packet Tracer Extension

The extension source is in `extension/source`. For local use, generate a
Packet Tracer Script Engine entry file:

```powershell
cd E:\mc\packet-tracer-visual-mcp
python scripts\build_script_engine.py
```

This writes:

```text
extension\packet-tracer-visual-mcp-script-engine.js
```

Expected runtime:

1. Start `pt-visual-mcp`.
2. Open Cisco Packet Tracer.
3. Import and run `extension\packet-tracer-visual-mcp-script-engine.js` in Packet Tracer Script Engine.
4. Open `Extensions > PT Visual MCP`.
5. The bridge window should show `connected`.

The extension connects to:

```text
ws://127.0.0.1:7541/ws
```

## Main MCP Tools

- `ptv_bridgeStatus`
- `ptv_getNetwork`
- `ptv_addDevice`
- `ptv_addDevicesTimeline`
- `ptv_addLink`
- `ptv_addLinksTimeline`
- `ptv_configurePc`
- `ptv_configureIos`
- `ptv_getCommandLog`
- `ptv_runShowCommands`
- `ptv_generateIosTemplate`
- `ptv_generateCampusIosConfig`
- `ptv_generateCampusValidationPlan`
- `ptv_validateCampusFast`
- `ptv_applyCampusIosConfig`
- `ptv_applyIosConfigSet`
- `ptv_getFaultLibrary`
- `ptv_injectFault`
- `ptv_repairFault`
- `ptv_getCampusPlan`
- `ptv_buildCampusRecordingDemo`

## Fast-Safe Build Mode

Topology creation supports quality modes:

- `max-speed`: fastest visual build, minimal settle time, 1 retry.
- `fast-safe`: default, short visual delays, 3 retries, preflight validation, and post-build verification.
- `balanced`: more retries and longer settle time.
- `strict`: strongest validation/retry profile.

For demos that need to look fast but still be reliable, use:

```json
{
  "qualityMode": "fast-safe",
  "deviceDelayMs": 40,
  "linkDelayMs": 20,
  "autoAssignPorts": true,
  "autoFallback": true,
  "validatePlan": true,
  "verifyAfterBuild": true
}
```

## Validation Modes

Validation defaults to `fast` so screen-recorded builds and course-design generation stay responsive.

- `fast`: checks the generated plan shape, build/apply results, key devices, and link count. It can use one `getNetwork` canvas snapshot and does not run IOS `show` sweeps.
- `standard`: generates an IOS command-check plan for VLAN, trunk, routing, DHCP, NAT, and ACL evidence.
- `strict`: same command-check surface as standard, intended for slower final checks after traffic has been generated.
- `off`: generates no validation checks.

Use `ptv_validateCampusFast` right after a build when speed matters. Use `ptv_generateCampusValidationPlan` with `validationMode: "standard"` or `"strict"` before final submission or a slower debugging pass.

## Automatic Port Allocation

Links can omit interface names:

```json
{
  "fromDevice": "CORE-A",
  "toDevice": "DIST-L",
  "linkType": "auto"
}
```

The Packet Tracer extension scans real device ports, prefers sensible Ethernet ports, reserves ports during batch linking, and falls back from invalid fixed ports when `autoFallback` is enabled.

## Example Prompt

```text
Generate the complete campus IOS configuration with OSPF, IOS DHCP pools, ACLs, and NAT/PAT.
Preview it first, then apply it to Packet Tracer if the bridge is connected.
```

For a course-design walkthrough, see:

```text
examples/campus-course-design.md
```

## Development Check

```powershell
python -m pip install -e .
python scripts\check_project.py
python -m compileall src scripts
python scripts\build_script_engine.py
node --check extension\source\pt_api.js
node --check extension\source\interface\bridge.js
node --check extension\packet-tracer-visual-mcp-script-engine.js
```

## Originality And License

This is an independent implementation. It does not claim to be affiliated with Cisco.

If you later copy code from another MIT-licensed Packet Tracer MCP project, keep that project's license and attribution. The current repository is intended to be a clean rewrite focused on visual timeline builds and course-design presets.

License: MIT.
