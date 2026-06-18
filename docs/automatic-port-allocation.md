# Automatic Port Allocation

Packet Tracer links can now be created without fixed interface names.

## Supported Calls

- `ptv_addLink`
- `ptv_addLinksTimeline`
- `ptv_buildCampusRecordingDemo`

Use either omitted interfaces or explicit `auto`:

```json
{
  "fromDevice": "CORE-A",
  "toDevice": "DIST-L",
  "fromInterface": "auto",
  "toInterface": "auto",
  "linkType": "auto"
}
```

## Behavior

- Fixed ports are tried first.
- If a fixed port is invalid or unavailable and `autoFallback` is true, the extension selects another usable port.
- Batch linking keeps a reserved-port map so later links do not reuse ports assigned earlier in the same batch.
- Preflight checks duplicate device names, port capacity, duplicate planned ports, unsupported models, and invalid link types.
- Link results include `assignedFromInterface` and `assignedToInterface`.

## Recommended Defaults

```json
{
  "autoAssignPorts": true,
  "autoFallback": true,
  "qualityMode": "fast-safe"
}
```

## Configuration Caveat

If IOS configuration depends on exact interface names, inspect assigned link results before applying interface-specific configuration. For visual topology builds, automatic port allocation is usually the safer default.
