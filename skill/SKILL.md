---
name: pt-visual-mcp
description: Use this skill whenever the user wants Cisco Packet Tracer automation for lab generation, campus-network course design, IOS configuration, static/RIP/OSPF/EIGRP routing, DHCP pools, ACL/NAT templates, fault injection, repair demos, or visual one-by-one topology building. Prefer the ptv_* MCP tools from packet-tracer-visual-mcp over mouse automation.
---

# PT Visual MCP

This skill drives the original `packet-tracer-visual-mcp` toolchain: a local MCP server plus a Packet Tracer extension bridge. It is optimized for Packet Tracer lab generation, IOS automation, course-design topologies, and optional visual topology building.

Default local checkout on this machine: `E:\mc\packet-tracer-visual-mcp`.

## Before Acting

1. Check whether the MCP tool list contains `ptv_bridgeStatus`.
2. If it is missing, tell the user the PT Visual MCP tools are not loaded and ask them to restart Codex after adding the MCP config.
3. If it is loaded, call `ptv_bridgeStatus` first.
4. If the bridge is not connected, ask the user to open Packet Tracer and choose `Extensions > PT Visual MCP`.
5. If the Packet Tracer menu is missing, tell the user to import and run `extension\packet-tracer-visual-mcp-script-engine.js` from this project.

## Main Workflow

For IOS automation:

1. Use `ptv_generateIosTemplate` for reusable static route, RIP, OSPF, EIGRP, DHCP pool, ACL, or NAT/PAT command blocks.
2. Use `ptv_generateCampusIosConfig` to preview a complete campus config set.
3. Use `ptv_applyCampusIosConfig` only after the topology exists and the bridge is connected.
4. Use `ptv_applyIosConfigSet` when applying a custom config set.

For validation:

1. Use `ptv_validateCampusFast` by default. It keeps validation quick by checking plan shape, build/apply results, one optional canvas snapshot, key devices, and link count.
2. Use `ptv_generateCampusValidationPlan` with `validationMode: "standard"` or `"strict"` only when the user explicitly wants slower IOS command checks.
3. Use `ptv_runShowCommands` and `ptv_getCommandLog` for targeted deep checks; do not claim full show-output parsing unless Packet Tracer exposes it.
4. Treat Server-PT DNS/Web/FTP graphical service toggles as manual unless the extension gains a reliable service API.

For fault demos:

1. Call `ptv_getFaultLibrary` to list supported faults.
2. Call `ptv_injectFault` with `apply: false` first if the user wants to preview commands.
3. Call `ptv_injectFault` with `apply: true` to break the lab intentionally.
4. Call `ptv_repairFault` with `apply: true` to restore the lab.

For screen-recorded campus builds:

1. Call `ptv_getNetwork` if you need to inspect the current canvas.
2. Call `ptv_getCampusPlan` if the user wants a preview.
3. Call `ptv_buildCampusRecordingDemo` for the full visual build.
4. Use `qualityMode: "fast-safe"` by default. It keeps short visual delays but adds preflight validation, short retries, settle time, and post-build verification.
5. Use a short device delay for promotional demos:
   - `deviceDelayMs: 40-100`
   - `linkDelayMs: 20-60`
6. Use `qualityMode: "max-speed"` only when the user explicitly wants speed over correctness.
7. Use `qualityMode: "strict"` when the user cares more about correctness than visual speed.
8. Keep `autoAssignPorts: true` and `autoFallback: true` unless the user needs exact physical port names.
9. Use `configureDevices: false` when visual speed matters.
10. Use `configureDevices: true` only when the user asks for network-side configuration in the same run and is willing to wait.
11. Use `ptv_validateCampusFast` after a build if the user wants a quick correctness report without slowing the visual flow.

Quality modes:

- `max-speed`: minimal settle time and 1 retry.
- `fast-safe`: default; 3 retries, short waits, preflight and verification.
- `balanced`: more retries and longer settle time.
- `strict`: strongest validation/retry profile.

Validation modes:

- `fast`: default; no heavy `show` sweep, uses build/apply results and one optional `getNetwork` snapshot.
- `standard`: generates IOS command checks for VLAN, trunk, routing, DHCP, NAT, and ACL evidence.
- `strict`: slower final validation after traffic has been generated.
- `off`: no validation checks.

Automatic port allocation:

- `ptv_addLink` and `ptv_addLinksTimeline` can omit `fromInterface` and `toInterface`, or set them to `auto`.
- Batch link creation reserves ports after each successful link so later links do not reuse them.
- Fixed ports are tried first. If unavailable and `autoFallback` is true, the tool falls back to a usable port.
- If IOS config depends on exact interface names, mention any assigned port differences before applying config.

## Course Design Coverage

The built-in campus plan is designed to satisfy common computer-network course requirements:

- At least 4 VLANs: VLAN 10, 20, 30, 40, 50, 99
- Access and trunk ports
- Inter-VLAN routing on multilayer switches
- Static routing, RIP, OSPF, or EIGRP between edge/core devices
- IOS DHCP pools or DHCP relay toward a server VLAN
- DNS, Web, and FTP server placement
- NAT/PAT on the edge router
- Two ACL checks:
  - VLAN30 denied to the Web server
  - VLAN50 denied to FTP
- Connectivity, service, NAT, ACL, and debugging test notes
- A complete debugging case for proving and restoring the VLAN30 Web ACL behavior
- Built-in fault library for trunk VLAN, OSPF, static route, ACL, and NAT mistakes

If Packet Tracer Server-PT services cannot be fully configured through automation, clearly tell the user to manually enable:

- DHCP on the DHCP server, with VLAN 10/20/30/50/99 pools and DNS 192.168.40.10
- DNS: `www.campus.local -> 192.168.40.20`, `ftp.campus.local -> 192.168.40.30`
- HTTP on the Web server
- FTP on the FTP server with `ftpuser / cisco`

## Visual Rules

When placing devices manually through `ptv_addDevicesTimeline`, keep enough spacing for video:

- Backbone and edge at the top.
- Core switches in the upper middle.
- Distribution layer in the middle.
- Access switches below.
- Servers grouped together but not overlapping.
- PCs/laptops on the bottom row.

Avoid creating all devices in one tool call unless the tool itself is a timeline call. The visual effect comes from Packet Tracer executing one creation at a time inside the extension.

## Response Style

When reporting completion, include:

- Device count and link count
- Whether IOS configuration was applied
- Routing protocol and DHCP mode if configuration was generated
- Fault ID and repair commands if a fault demo was used
- Manual server-service steps if needed
- A concise test checklist

Do not claim the project is Cisco official. Say it is an original Packet Tracer lab MCP implementation.
