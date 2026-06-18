# Validation Modes

The project keeps validation speed under explicit control. The default is `fast` because visual Packet Tracer demos should not pause for a long IOS command sweep.

## Modes

- `fast`: local plan checks, build/apply result checks, key device checks, and one optional canvas snapshot through `getNetwork`.
- `standard`: produces IOS `show` command checks for VLANs, trunks, routing, DHCP, NAT/PAT, and ACLs.
- `strict`: reserved for slower final checks. It uses the same command-check surface and should be run after DHCP/NAT/ACL traffic has been generated.
- `off`: returns an empty validation plan.

## Fast Validation

Use:

```json
{
  "tool": "ptv_validateCampusFast",
  "arguments": {
    "checkCanvas": true
  }
}
```

Fast validation does not run heavy `show` commands. It checks:

- The built-in campus plan still has 33 devices and 34 links.
- The build result has no failed preflight, device, link, PC config, IOS config, or verify stage.
- The canvas contains the expected device names when a bridge snapshot is available.
- The canvas has at least the expected link count.
- Standalone IOS apply results have no failed devices when supplied.

If `prefix` is not supplied, the validator first tries to infer it from the build result, then from the current canvas. This keeps the fast path convenient for screen-recorded demos.

## Standard And Strict Plans

Use:

```json
{
  "tool": "ptv_generateCampusValidationPlan",
  "arguments": {
    "validationMode": "standard",
    "routingProtocol": "ospf",
    "dhcpMode": "ios"
  }
}
```

The returned `commandSet` can be executed manually or with `ptv_runShowCommands`. Packet Tracer command history confirms that commands were sent, but full show-output parsing depends on what Packet Tracer exposes through its script engine.
