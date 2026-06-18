# Fast-Safe Build Mode

Fast topology building is split into two concerns:

- Visual delay: how quickly devices and links appear on screen.
- Reliability controls: preflight validation, retry delay, settle time, and post-build verification.

This lets the build look fast without relying on long fixed sleeps.

## Quality Modes

- `max-speed`: minimal checks, 1 retry, shortest settle time.
- `fast-safe`: default. Preflight validation, 3 retries, short settle time, and verification.
- `balanced`: more retries and a larger settle window for heavier topologies.
- `strict`: strongest validation profile.

## What Fast-Safe Checks

Before building:

- Duplicate device names
- Unsupported models
- Invalid coordinates
- Severe device overlap
- Duplicate links
- Unsupported link types
- Interface names that do not match planned models
- Planned links that exceed available port capacity
- Planned reuse of the same fixed port
- Existing device names that would collide with the plan

During building:

- Each device creation is retried briefly before failing.
- Each link creation validates device and interface existence, then retries briefly.
- Link creation can automatically choose usable Ethernet ports and reserve them during a batch.
- Critical failures stop later stages, so configuration is not applied to a broken topology.

After building:

- Expected devices are checked on the Packet Tracer canvas.
- Planned link endpoints are checked for device/interface existence.
- Actual canvas device/link counts are returned for reporting.

## Recommended Demo Settings

```json
{
  "qualityMode": "fast-safe",
  "deviceDelayMs": 40,
  "linkDelayMs": 20,
  "maxRetries": 3,
  "retryDelayMs": 30,
  "settleMs": 15,
  "autoAssignPorts": true,
  "autoFallback": true,
  "validatePlan": true,
  "verifyAfterBuild": true
}
```
