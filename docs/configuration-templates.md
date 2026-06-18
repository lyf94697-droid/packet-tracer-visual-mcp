# IOS Configuration Templates

The MCP server exposes configuration tools that work without mouse automation:

- `ptv_generateIosTemplate`
- `ptv_generateCampusIosConfig`
- `ptv_applyCampusIosConfig`
- `ptv_applyIosConfigSet`
- `ptv_getFaultLibrary`
- `ptv_injectFault`
- `ptv_repairFault`

## Template Types

`ptv_generateIosTemplate` supports:

- `static_route`
- `rip`
- `ospf`
- `eigrp`
- `dhcp_pool`
- `acl_extended`
- `nat_pat`

The tool returns both raw commands and wrapped commands with `enable`, `configure terminal`, `end`, and optionally `write memory`.

## Campus Config Set

`ptv_generateCampusIosConfig` returns a full campus configuration set for the built-in topology.

Supported options:

- `routingProtocol`: `static`, `rip`, `ospf`, or `eigrp`
- `dhcpMode`: `ios`, `server-relay`, or `none`
- `includeNatPat`: enable or skip NAT/PAT on the edge router
- `includeAcl`: enable or skip ACL 100/101
- `writeMemory`: append `write memory`

`ptv_applyCampusIosConfig` generates the same config set and sends it to Packet Tracer devices. The topology must already exist and the bridge must be connected.

## Fault Library

Built-in fault IDs:

- `missing_trunk_vlan_40`
- `ospf_area_mismatch`
- `remove_core_a_default_route`
- `acl_overblock_dns`
- `disable_nat_outside`

Use `ptv_injectFault` with `apply: false` to preview the commands. Use `apply: true` to change the lab. Use `ptv_repairFault` with the same `faultId` to restore it.
