# Campus Course Design Example

This example maps a common computer-network course-design requirement to the built-in campus preset.

## Lab Coverage

- VLANs: 10, 20, 30, 40, 50, 99.
- Access and trunk switching.
- Inter-VLAN routing on multilayer core switches.
- Static routing, RIP, OSPF, or EIGRP configuration generation.
- IOS DHCP pools or DHCP relay design.
- DNS, Web, and FTP server placement.
- NAT/PAT on the edge router.
- ACL 100 and ACL 101 allow/deny cases.
- Connectivity, service, NAT, ACL, and debug test notes.

## Fast Screen-Recording Build

Use `ptv_buildCampusRecordingDemo` with:

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

This creates the visual topology quickly and returns service steps, tests, and a fast validation report.

## Full Network Configuration

After the topology exists, use `ptv_generateCampusIosConfig` or `ptv_applyCampusIosConfig`:

```json
{
  "routingProtocol": "ospf",
  "dhcpMode": "ios",
  "includeNatPat": true,
  "includeAcl": true,
  "writeMemory": true
}
```

## Fast Validation

Use `ptv_validateCampusFast` immediately after a build:

```json
{
  "checkCanvas": true
}
```

Fast validation checks topology and workflow health without running a long `show` command sweep. For a final slower pass, generate a standard plan:

```json
{
  "validationMode": "standard",
  "routingProtocol": "ospf",
  "dhcpMode": "ios"
}
```

## Manual Server Services

Packet Tracer Server-PT graphical service panels may still need manual setup:

- DNS: `www.campus.local -> 192.168.40.20`, `ftp.campus.local -> 192.168.40.30`.
- HTTP: enable on the Web server.
- FTP: enable on the FTP server and add `ftpuser / cisco`.
