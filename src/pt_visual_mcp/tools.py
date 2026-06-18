from __future__ import annotations

from typing import Any


DEVICE_MODELS = [
    "2911",
    "1941",
    "2901",
    "2960-24TT",
    "2960-48TT",
    "3560-24PS",
    "PC-PT",
    "Server-PT",
    "Laptop-PT",
    "Printer-PT",
]


def obj(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": required or []}


DEVICE_SCHEMA = obj(
    {
        "name": {"type": "string"},
        "model": {"type": "string", "enum": DEVICE_MODELS},
        "x": {"type": "number"},
        "y": {"type": "number"},
    },
    ["name", "model", "x", "y"],
)


LINK_SCHEMA = obj(
    {
        "fromDevice": {"type": "string"},
        "fromInterface": {"type": "string", "default": "auto"},
        "toDevice": {"type": "string"},
        "toInterface": {"type": "string", "default": "auto"},
        "linkType": {"type": "string", "default": "auto"},
        "autoAssignPorts": {"type": "boolean", "default": True},
        "autoFallback": {"type": "boolean", "default": True},
    },
    ["fromDevice", "toDevice"],
)


COMMANDS_SCHEMA = {
    "oneOf": [
        {"type": "string"},
        {"type": "array", "items": {"type": "string"}},
    ]
}


CONFIG_ITEM_SCHEMA = obj(
    {
        "deviceName": {"type": "string"},
        "commands": COMMANDS_SCHEMA,
    },
    ["deviceName", "commands"],
)

QUALITY_SCHEMA = {
    "type": "string",
    "enum": ["max-speed", "fast-safe", "balanced", "strict"],
    "default": "fast-safe",
}

VALIDATION_MODE_SCHEMA = {
    "type": "string",
    "enum": ["off", "fast", "standard", "strict"],
    "default": "fast",
}

QUALITY_OPTIONS = {
    "qualityMode": QUALITY_SCHEMA,
    "maxRetries": {"type": "integer", "minimum": 0, "maximum": 10, "default": 3},
    "retryDelayMs": {"type": "integer", "minimum": 0, "maximum": 1000, "default": 30},
    "settleMs": {"type": "integer", "minimum": 0, "maximum": 1000, "default": 15},
    "minSpacing": {"type": "integer", "minimum": 0, "maximum": 300, "default": 55},
    "autoAssignPorts": {"type": "boolean", "default": True},
    "autoFallback": {"type": "boolean", "default": True},
}


TOOLS: list[dict[str, Any]] = [
    {
        "name": "ptv_bridgeStatus",
        "description": "Check whether the Packet Tracer Visual MCP extension is connected.",
        "inputSchema": obj({}),
        "local": True,
    },
    {
        "name": "ptv_getNetwork",
        "description": "Read the current Packet Tracer logical workspace: devices, interfaces, and links.",
        "inputSchema": obj({}),
        "action": "getNetwork",
    },
    {
        "name": "ptv_addDevice",
        "description": "Add one Packet Tracer device at a specific workspace coordinate.",
        "inputSchema": DEVICE_SCHEMA,
        "action": "addDevice",
    },
    {
        "name": "ptv_addDevicesTimeline",
        "description": (
            "Add devices one by one inside Packet Tracer with a short delay between real add operations. "
            "Use for screen recordings where viewers should see devices appear sequentially."
        ),
        "inputSchema": obj(
            {
                "devices": {"type": "array", "items": DEVICE_SCHEMA, "minItems": 1},
                "delayMs": {"type": "integer", "minimum": 0, "maximum": 10000, "default": 120},
                **QUALITY_OPTIONS,
            },
            ["devices"],
        ),
        "action": "addDevicesTimeline",
        "timeout": 180.0,
    },
    {
        "name": "ptv_addLink",
        "description": "Create one link between two existing Packet Tracer interfaces.",
        "inputSchema": LINK_SCHEMA,
        "action": "addLink",
    },
    {
        "name": "ptv_addLinksTimeline",
        "description": "Create links one by one with a short delay, optimized for recording a topology being wired.",
        "inputSchema": obj(
            {
                "links": {"type": "array", "items": LINK_SCHEMA, "minItems": 1},
                "delayMs": {"type": "integer", "minimum": 0, "maximum": 10000, "default": 60},
                **QUALITY_OPTIONS,
            },
            ["links"],
        ),
        "action": "addLinksTimeline",
        "timeout": 180.0,
    },
    {
        "name": "ptv_configurePc",
        "description": "Set a PC or Server IPv4 address, mask, gateway, DNS, or DHCP flag.",
        "inputSchema": obj(
            {
                "deviceName": {"type": "string"},
                "dhcp": {"type": "boolean", "default": False},
                "ip": {"type": "string", "default": ""},
                "mask": {"type": "string", "default": ""},
                "gateway": {"type": "string", "default": ""},
                "dns": {"type": "string", "default": ""},
            },
            ["deviceName"],
        ),
        "action": "configurePc",
    },
    {
        "name": "ptv_configureIos",
        "description": "Send Cisco IOS commands to one router or switch. Commands may be a string or an array of strings.",
        "inputSchema": obj(
            {
                "deviceName": {"type": "string"},
                "commands": COMMANDS_SCHEMA,
            },
            ["deviceName", "commands"],
        ),
        "action": "configureIos",
        "timeout": 120.0,
    },
    {
        "name": "ptv_getCommandLog",
        "description": "Read recent Packet Tracer command history for one device or the whole workspace.",
        "inputSchema": obj(
            {
                "deviceName": {"type": "string", "default": ""},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500, "default": 80},
            }
        ),
        "action": "getCommandLog",
    },
    {
        "name": "ptv_runShowCommands",
        "description": (
            "Issue show commands to one IOS device and return command-log confirmation. "
            "Packet Tracer does not guarantee full show-output parsing."
        ),
        "inputSchema": obj(
            {
                "deviceName": {"type": "string"},
                "commands": COMMANDS_SCHEMA,
                "logLimit": {"type": "integer", "minimum": 1, "maximum": 500, "default": 120},
            },
            ["deviceName", "commands"],
        ),
        "action": "runShowCommands",
        "timeout": 120.0,
    },
    {
        "name": "ptv_probeDeviceApi",
        "description": (
            "Read-only probe for Packet Tracer device object APIs. Use it to inspect whether a device exposes "
            "service-related methods before implementing Server-PT automation."
        ),
        "inputSchema": obj(
            {
                "deviceName": {"type": "string"},
                "maxDepth": {"type": "integer", "minimum": 0, "maximum": 5, "default": 2},
                "maxKeys": {"type": "integer", "minimum": 10, "maximum": 300, "default": 120},
                "includeSafeCalls": {"type": "boolean", "default": True},
            },
            ["deviceName"],
        ),
        "action": "probeDeviceApi",
    },
    {
        "name": "ptv_probeServerServices",
        "description": (
            "Read-only probe for Server-PT service automation hints. It scans one Server-PT or all Server-PT "
            "devices for DNS/HTTP/FTP/DHCP related API names without changing services."
        ),
        "inputSchema": obj(
            {
                "deviceName": {"type": "string", "default": ""},
                "maxDepth": {"type": "integer", "minimum": 0, "maximum": 5, "default": 2},
                "maxKeys": {"type": "integer", "minimum": 10, "maximum": 300, "default": 120},
            }
        ),
        "action": "probeServerServices",
    },
    {
        "name": "ptv_generateIosTemplate",
        "description": (
            "Generate reusable IOS command templates for static routes, RIP, OSPF, EIGRP, DHCP pools, "
            "extended ACLs, and NAT/PAT. This does not touch Packet Tracer."
        ),
        "inputSchema": obj(
            {
                "template": {
                    "type": "string",
                    "enum": ["static_route", "rip", "ospf", "eigrp", "dhcp_pool", "acl_extended", "nat_pat"],
                },
                "params": {"type": "object", "default": {}},
            },
            ["template"],
        ),
        "local": True,
    },
    {
        "name": "ptv_generateCampusValidationPlan",
        "description": (
            "Generate a campus validation plan. Default validationMode is fast, which avoids show-command sweeps. "
            "Use standard or strict only when slower IOS command checks are acceptable."
        ),
        "inputSchema": obj(
            {
                "prefix": {"type": "string", "default": ""},
                "routingProtocol": {"type": "string", "enum": ["static", "rip", "ospf", "eigrp"], "default": "ospf"},
                "dhcpMode": {"type": "string", "enum": ["ios", "server-relay", "none"], "default": "ios"},
                "includeNatPat": {"type": "boolean", "default": True},
                "includeAcl": {"type": "boolean", "default": True},
                "validationMode": VALIDATION_MODE_SCHEMA,
            }
        ),
        "local": True,
    },
    {
        "name": "ptv_validateCampusFast",
        "description": (
            "Run a speed-preserving campus validation: plan shape, build/apply results, one optional canvas snapshot, "
            "and key-device/link checks. It does not run heavy show commands."
        ),
        "inputSchema": obj(
            {
                "prefix": {"type": "string", "default": ""},
                "originX": {"type": "number", "default": 80},
                "originY": {"type": "number", "default": 60},
                "scale": {"type": "number", "default": 1.0},
                "checkCanvas": {"type": "boolean", "default": True},
                "plan": {"type": "object", "default": {}},
                "buildResult": {"type": "object", "default": {}},
                "applyResult": {"type": "object", "default": {}},
            }
        ),
        "local": True,
        "timeout": 20.0,
    },
    {
        "name": "ptv_generateCampusIosConfig",
        "description": (
            "Generate a complete IOS configuration set for the built-in campus topology. "
            "Supports routingProtocol static/rip/ospf/eigrp, IOS DHCP pools, ACL templates, and NAT/PAT."
        ),
        "inputSchema": obj(
            {
                "prefix": {"type": "string", "default": ""},
                "routingProtocol": {"type": "string", "enum": ["static", "rip", "ospf", "eigrp"], "default": "ospf"},
                "dhcpMode": {"type": "string", "enum": ["ios", "server-relay", "none"], "default": "ios"},
                "includeNatPat": {"type": "boolean", "default": True},
                "includeAcl": {"type": "boolean", "default": True},
                "writeMemory": {"type": "boolean", "default": True},
            }
        ),
        "local": True,
    },
    {
        "name": "ptv_applyCampusIosConfig",
        "description": (
            "One-click generation and application of the complete campus IOS configuration set. "
            "Requires the Packet Tracer bridge to be connected."
        ),
        "inputSchema": obj(
            {
                "prefix": {"type": "string", "default": ""},
                "routingProtocol": {"type": "string", "enum": ["static", "rip", "ospf", "eigrp"], "default": "ospf"},
                "dhcpMode": {"type": "string", "enum": ["ios", "server-relay", "none"], "default": "ios"},
                "includeNatPat": {"type": "boolean", "default": True},
                "includeAcl": {"type": "boolean", "default": True},
                "writeMemory": {"type": "boolean", "default": True},
            }
        ),
        "local": True,
        "timeout": 420.0,
    },
    {
        "name": "ptv_applyIosConfigSet",
        "description": "Apply an arbitrary IOS config set made of deviceName plus commands entries.",
        "inputSchema": obj(
            {
                "configs": {"type": "array", "items": CONFIG_ITEM_SCHEMA, "minItems": 1},
            },
            ["configs"],
        ),
        "local": True,
        "timeout": 420.0,
    },
    {
        "name": "ptv_getFaultLibrary",
        "description": "List built-in fault injection scenarios and their expected symptoms and verification commands.",
        "inputSchema": obj({}),
        "local": True,
    },
    {
        "name": "ptv_injectFault",
        "description": (
            "Generate or apply a built-in fault scenario, such as missing trunk VLAN, OSPF area mismatch, "
            "missing static route, overblocking ACL, or broken NAT outside marking."
        ),
        "inputSchema": obj(
            {
                "faultId": {"type": "string"},
                "prefix": {"type": "string", "default": ""},
                "apply": {"type": "boolean", "default": False},
            },
            ["faultId"],
        ),
        "local": True,
        "timeout": 120.0,
    },
    {
        "name": "ptv_repairFault",
        "description": "Generate or apply the repair commands for a built-in fault scenario.",
        "inputSchema": obj(
            {
                "faultId": {"type": "string"},
                "prefix": {"type": "string", "default": ""},
                "apply": {"type": "boolean", "default": False},
            },
            ["faultId"],
        ),
        "local": True,
        "timeout": 120.0,
    },
    {
        "name": "ptv_getCampusPlan",
        "description": (
            "Generate the built-in campus-network demo plan without touching Packet Tracer. "
            "Use this to preview device names, VLANs, links, service steps, and tests."
        ),
        "inputSchema": obj(
            {
                "prefix": {"type": "string", "default": ""},
                "originX": {"type": "number", "default": 80},
                "originY": {"type": "number", "default": 60},
                "scale": {"type": "number", "default": 1.0},
            }
        ),
        "local": True,
    },
    {
        "name": "ptv_buildCampusRecordingDemo",
        "description": (
            "Build a visually complex campus topology in Packet Tracer: devices appear sequentially, "
            "links are drawn sequentially, PC/server IPs are applied, and IOS commands are optionally sent. "
            "Designed for course-design demos and screen recordings."
        ),
        "inputSchema": obj(
            {
                "prefix": {"type": "string", "default": ""},
                "originX": {"type": "number", "default": 80},
                "originY": {"type": "number", "default": 60},
                "scale": {"type": "number", "default": 1.0},
                "deviceDelayMs": {"type": "integer", "minimum": 0, "maximum": 10000, "default": 120},
                "linkDelayMs": {"type": "integer", "minimum": 0, "maximum": 10000, "default": 60},
                "configureDevices": {"type": "boolean", "default": False},
                "validatePlan": {"type": "boolean", "default": True},
                "verifyAfterBuild": {"type": "boolean", "default": True},
                **QUALITY_OPTIONS,
            }
        ),
        "local": True,
        "timeout": 420.0,
    },
]

TOOLS_BY_NAME = {tool["name"]: tool for tool in TOOLS}
