# Example Prompts

## Complete Campus Configuration

```text
Use PT Visual MCP to generate the complete campus IOS configuration with OSPF, IOS DHCP pools, ACLs, and NAT/PAT. Preview the config set first.
```

## Routing Protocol Variants

```text
Generate the same campus network IOS configuration four times: static routing, RIP, OSPF, and EIGRP. Show what commands change between the versions.
```

## Apply Configuration

```text
The Packet Tracer topology already exists and the PT Visual MCP bridge is connected. Apply the complete campus IOS configuration with routingProtocol ospf, dhcpMode ios, ACL enabled, and NAT/PAT enabled.
```

## Fault Injection

```text
List the built-in fault library, then inject the OSPF area mismatch fault. After I test it, repair the fault and give me the verification commands.
```

## Visual Topology Build

```text
Build the campus topology with devices appearing one by one and links appearing one by one, then generate the full IOS configuration separately.
```

## Fast Course-Design Demo

```text
Use PT Visual MCP to build the complex campus course-design topology with qualityMode fast-safe, deviceDelayMs 40, linkDelayMs 20, autoAssignPorts true, and configureDevices false. After the visual build, run fast validation and summarize the device count, link count, VLAN coverage, routing plan, NAT/PAT, ACL tests, manual Server-PT service steps, and debug case.
```

## Automatic Ports

```text
Create links using automatic port allocation. I will give only fromDevice and toDevice; choose free Ethernet ports, reserve ports during the batch, and report the assigned interfaces.
```

## Final Validation Plan

```text
Generate the campus validation plan with validationMode standard, routingProtocol ospf, dhcpMode ios, NAT/PAT enabled, and ACL enabled. Do not run the slow checks yet; show me the command set first.
```
