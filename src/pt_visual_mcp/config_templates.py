from __future__ import annotations

import time
from typing import Any


ROUTING_PROTOCOLS = {"static", "rip", "ospf", "eigrp"}
DHCP_MODES = {"ios", "server-relay", "none"}
ALL_VLANS = "10,20,30,40,50,99"


def default_prefix(prefix: str | None) -> str:
    if prefix:
        return prefix.strip().rstrip("-")
    return "PTV-" + time.strftime("%H%M%S")


def wrap_config(commands: list[str], write_memory: bool = True) -> list[str]:
    wrapped = ["enable", "configure terminal"]
    wrapped.extend(commands)
    wrapped.append("end")
    if write_memory:
        wrapped.append("write memory")
    return wrapped


def render_ios_template(template: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    params = params or {}
    template = template.strip().lower()

    if template == "static_route":
        network = str(params.get("network", "0.0.0.0"))
        mask = str(params.get("mask", "0.0.0.0"))
        next_hop = str(params.get("nextHop", params.get("next_hop", "192.0.2.1")))
        commands = [f"ip route {network} {mask} {next_hop}"]

    elif template == "rip":
        networks = _list(params.get("networks", ["10.0.0.0"]))
        commands = ["router rip", "version 2", "no auto-summary"]
        commands.extend(f"network {network}" for network in networks)
        if params.get("defaultInformation"):
            commands.append("default-information originate")

    elif template == "ospf":
        process_id = str(params.get("processId", 1))
        router_id = params.get("routerId")
        networks = params.get("networks", [{"network": "10.0.0.0", "wildcard": "0.0.0.255", "area": 0}])
        commands = [f"router ospf {process_id}"]
        if router_id:
            commands.append(f"router-id {router_id}")
        for item in networks:
            commands.append(
                "network {network} {wildcard} area {area}".format(
                    network=item.get("network", "10.0.0.0"),
                    wildcard=item.get("wildcard", "0.0.0.255"),
                    area=item.get("area", 0),
                )
            )
        if params.get("defaultInformation"):
            commands.append("default-information originate")

    elif template == "eigrp":
        asn = str(params.get("asn", 100))
        networks = params.get("networks", [{"network": "10.0.0.0", "wildcard": "0.0.0.255"}])
        commands = [f"router eigrp {asn}", "no auto-summary"]
        for item in networks:
            if isinstance(item, str):
                commands.append(f"network {item}")
            else:
                commands.append(f"network {item.get('network', '10.0.0.0')} {item.get('wildcard', '0.0.0.255')}")

    elif template == "dhcp_pool":
        pool = str(params.get("pool", "VLAN10"))
        network = str(params.get("network", "192.168.10.0"))
        mask = str(params.get("mask", "255.255.255.0"))
        gateway = str(params.get("gateway", "192.168.10.1"))
        dns = str(params.get("dns", "192.168.40.10"))
        domain = str(params.get("domain", "campus.local"))
        excluded_start = params.get("excludedStart")
        excluded_end = params.get("excludedEnd")
        commands = []
        if excluded_start and excluded_end:
            commands.append(f"ip dhcp excluded-address {excluded_start} {excluded_end}")
        commands.extend(
            [
                f"ip dhcp pool {pool}",
                f"network {network} {mask}",
                f"default-router {gateway}",
                f"dns-server {dns}",
                f"domain-name {domain}",
                "exit",
            ]
        )

    elif template == "acl_extended":
        acl_id = str(params.get("aclId", 100))
        action = str(params.get("action", "deny"))
        protocol = str(params.get("protocol", "ip"))
        source = str(params.get("source", "192.168.10.0 0.0.0.255"))
        destination = str(params.get("destination", "host 192.168.40.20"))
        operator = params.get("operator")
        port = params.get("port")
        line = f"access-list {acl_id} {action} {protocol} {source} {destination}"
        if operator and port:
            line += f" {operator} {port}"
        commands = [line]
        if params.get("permitRest", True):
            commands.append(f"access-list {acl_id} permit ip any any")

    elif template == "nat_pat":
        inside_interfaces = _list(params.get("insideInterfaces", ["GigabitEthernet0/1"]))
        outside_interface = str(params.get("outsideInterface", "GigabitEthernet0/0"))
        acl_id = str(params.get("aclId", 1))
        source = str(params.get("source", "192.168.0.0 0.0.255.255"))
        overload_interface = str(params.get("overloadInterface", outside_interface))
        commands = []
        commands.append(f"interface {outside_interface}")
        commands.append("ip nat outside")
        commands.append("exit")
        for interface in inside_interfaces:
            commands.append(f"interface {interface}")
            commands.append("ip nat inside")
            commands.append("exit")
        commands.append(f"access-list {acl_id} permit {source}")
        commands.append(f"ip nat inside source list {acl_id} interface {overload_interface} overload")

    else:
        raise ValueError(f"unsupported IOS template: {template}")

    return {
        "template": template,
        "commands": wrap_config(commands, bool(params.get("writeMemory", True))),
        "rawCommands": commands,
    }


def build_campus_config_set(
    prefix: str | None = None,
    routing_protocol: str = "ospf",
    dhcp_mode: str = "ios",
    include_nat: bool = True,
    include_acl: bool = True,
    write_memory: bool = True,
) -> dict[str, Any]:
    routing_protocol = routing_protocol.lower()
    dhcp_mode = dhcp_mode.lower()
    if routing_protocol not in ROUTING_PROTOCOLS:
        raise ValueError("routingProtocol must be one of: static, rip, ospf, eigrp")
    if dhcp_mode not in DHCP_MODES:
        raise ValueError("dhcpMode must be one of: ios, server-relay, none")

    p = default_prefix(prefix)

    def name(short: str) -> str:
        return f"{p}-{short}"

    configs = [
        _edge_config(name, routing_protocol, include_nat, write_memory),
        _isp_config(name, write_memory),
        _core_a_config(name, routing_protocol, dhcp_mode, include_acl, write_memory),
        _core_b_config(name, routing_protocol, dhcp_mode, include_acl, write_memory),
        _dist_config(name, "DIST-L", write_memory),
        _dist_config(name, "DIST-R", write_memory),
        _server_switch_config(name, write_memory),
        _access_switch_config(name, "SW-ADMIN", 10, write_memory),
        _access_switch_config(name, "SW-TEACH", 20, write_memory),
        _access_switch_config(name, "SW-LAB", 20, write_memory),
        _access_switch_config(name, "SW-OFFICE", 10, write_memory),
        _access_switch_config(name, "SW-DORM", 30, write_memory),
        _access_switch_config(name, "SW-GUEST", 50, write_memory),
        _access_switch_config(name, "SW-MGMT", 99, write_memory),
    ]

    return {
        "profile": "campus-core",
        "prefix": p,
        "routingProtocol": routing_protocol,
        "dhcpMode": dhcp_mode,
        "includeNatPat": include_nat,
        "includeAcl": include_acl,
        "configs": configs,
        "summary": {
            "deviceConfigCount": len(configs),
            "supports": ["static", "rip", "ospf", "eigrp", "ios_dhcp_pools", "acl_templates", "nat_pat"],
        },
        "tests": _campus_config_tests(name, routing_protocol, dhcp_mode, include_nat, include_acl),
    }


FAULTS: dict[str, dict[str, Any]] = {
    "missing_trunk_vlan_40": {
        "title": "Server VLAN removed from a trunk",
        "device": "SW-SRV",
        "symptom": "Server VLAN 40 becomes unreachable through the server access switch uplink.",
        "verify": ["show interfaces trunk", "show vlan brief", "ping 192.168.40.20 from an internal client"],
        "inject": ["interface gigabitEthernet0/1", "switchport trunk allowed vlan 10,20,30,50,99"],
        "repair": ["interface gigabitEthernet0/1", f"switchport trunk allowed vlan {ALL_VLANS}"],
    },
    "ospf_area_mismatch": {
        "title": "OSPF area mismatch on the CORE-A uplink",
        "device": "CORE-A",
        "symptom": "CORE-A does not form the expected OSPF relationship toward EDGE on 10.0.0.0/30.",
        "verify": ["show ip ospf neighbor", "show ip protocols", "show ip route ospf"],
        "inject": [
            "router ospf 1",
            "no network 10.0.0.0 0.0.0.3 area 0",
            "network 10.0.0.0 0.0.0.3 area 1",
        ],
        "repair": [
            "router ospf 1",
            "no network 10.0.0.0 0.0.0.3 area 1",
            "network 10.0.0.0 0.0.0.3 area 0",
        ],
    },
    "remove_core_a_default_route": {
        "title": "Static default route removed from CORE-A",
        "device": "CORE-A",
        "symptom": "VLANs behind CORE-A lose upstream connectivity when static routing is used.",
        "verify": ["show ip route static", "ping 198.51.100.10 source vlan 10"],
        "inject": ["no ip route 0.0.0.0 0.0.0.0 10.0.0.1"],
        "repair": ["ip route 0.0.0.0 0.0.0.0 10.0.0.1"],
    },
    "acl_overblock_dns": {
        "title": "ACL accidentally blocks VLAN30 DNS",
        "device": "CORE-A",
        "symptom": "VLAN30 can no longer resolve DNS, while the intended policy only blocks Web.",
        "verify": ["show access-lists 100", "ping 192.168.40.10 from VLAN30", "HTTP to 192.168.40.20 from VLAN30"],
        "inject": [
            "no access-list 100",
            "access-list 100 deny ip 192.168.30.0 0.0.0.255 host 192.168.40.10",
            "access-list 100 deny ip 192.168.30.0 0.0.0.255 host 192.168.40.20",
            "access-list 100 permit ip any any",
        ],
        "repair": [
            "no access-list 100",
            "access-list 100 deny ip 192.168.30.0 0.0.0.255 host 192.168.40.20",
            "access-list 100 permit ip any any",
        ],
    },
    "disable_nat_outside": {
        "title": "NAT outside marking removed",
        "device": "EDGE",
        "symptom": "Internal clients fail NAT/PAT tests to the simulated internet server.",
        "verify": ["show ip nat translations", "show run interface gigabitEthernet0/0", "ping 198.51.100.10"],
        "inject": ["interface gigabitEthernet0/0", "no ip nat outside"],
        "repair": ["interface gigabitEthernet0/0", "ip nat outside"],
    },
}


def get_fault_library() -> dict[str, Any]:
    return {
        "faults": [
            {
                "faultId": fault_id,
                "title": fault["title"],
                "deviceRole": fault["device"],
                "symptom": fault["symptom"],
                "verify": fault["verify"],
            }
            for fault_id, fault in FAULTS.items()
        ]
    }


def build_fault_plan(fault_id: str, prefix: str | None = None, action: str = "inject") -> dict[str, Any]:
    if fault_id not in FAULTS:
        raise ValueError(f"unknown faultId: {fault_id}")
    if action not in {"inject", "repair"}:
        raise ValueError("action must be inject or repair")

    p = default_prefix(prefix)
    fault = FAULTS[fault_id]
    commands = fault[action]
    device_name = f"{p}-{fault['device']}"
    opposite = "repair" if action == "inject" else "inject"
    return {
        "faultId": fault_id,
        "action": action,
        "title": fault["title"],
        "symptom": fault["symptom"],
        "verify": fault["verify"],
        "configs": [{"deviceName": device_name, "commands": wrap_config(commands)}],
        "oppositeAction": opposite,
        "oppositeCommands": wrap_config(fault[opposite]),
    }


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value]


def _vlan_batch() -> list[str]:
    return [
        "vlan 10",
        "name ADMIN",
        "vlan 20",
        "name TEACH",
        "vlan 30",
        "name DORM",
        "vlan 40",
        "name SERVER",
        "vlan 50",
        "name GUEST",
        "vlan 99",
        "name MGMT",
    ]


def _trunk(interface: str) -> list[str]:
    return [
        f"interface {interface}",
        "switchport mode trunk",
        f"switchport trunk allowed vlan {ALL_VLANS}",
        "exit",
    ]


def _svi(vlan: int, ip: str, dhcp_mode: str, helper: bool = False, acl: int | None = None) -> list[str]:
    commands = [f"interface vlan {vlan}", f"ip address {ip} 255.255.255.0"]
    if dhcp_mode == "server-relay" and helper:
        commands.append("ip helper-address 192.168.40.40")
    if acl is not None:
        commands.append(f"ip access-group {acl} in")
    commands.append("no shutdown")
    commands.append("exit")
    return commands


def _edge_config(name, routing_protocol: str, include_nat: bool, write_memory: bool) -> dict[str, Any]:
    commands = [
        "hostname EDGE",
        "no ip domain-lookup",
        "interface gigabitEthernet0/0",
        "ip address 203.0.113.2 255.255.255.252",
    ]
    if include_nat:
        commands.append("ip nat outside")
    commands.extend(
        [
            "no shutdown",
            "exit",
            "interface gigabitEthernet0/1",
            "ip address 10.0.0.1 255.255.255.252",
        ]
    )
    if include_nat:
        commands.append("ip nat inside")
    commands.extend(
        [
            "no shutdown",
            "exit",
            "interface gigabitEthernet0/2",
            "ip address 10.0.0.5 255.255.255.252",
        ]
    )
    if include_nat:
        commands.append("ip nat inside")
    commands.append("no shutdown")
    commands.append("exit")
    if include_nat:
        commands.extend(
            [
                "access-list 1 permit 192.168.0.0 0.0.255.255",
                "ip nat inside source list 1 interface gigabitEthernet0/0 overload",
            ]
        )
    commands.extend(_routing_commands("EDGE", routing_protocol))
    return {"deviceName": name("EDGE"), "commands": wrap_config(commands, write_memory), "features": ["edge", routing_protocol, "nat_pat" if include_nat else "no_nat"]}


def _isp_config(name, write_memory: bool) -> dict[str, Any]:
    commands = [
        "hostname ISP",
        "interface gigabitEthernet0/0",
        "ip address 203.0.113.1 255.255.255.252",
        "no shutdown",
        "exit",
        "interface gigabitEthernet0/1",
        "ip address 198.51.100.1 255.255.255.0",
        "no shutdown",
        "exit",
        "ip route 192.168.0.0 255.255.0.0 203.0.113.2",
    ]
    return {"deviceName": name("ISP"), "commands": wrap_config(commands, write_memory), "features": ["isp", "static_return"]}


def _core_a_config(name, routing_protocol: str, dhcp_mode: str, include_acl: bool, write_memory: bool) -> dict[str, Any]:
    commands = ["hostname CORE-A", "no ip domain-lookup"]
    commands.extend(_vlan_batch())
    commands.append("ip routing")
    commands.extend(
        [
            "interface gigabitEthernet0/1",
            "no switchport",
            "ip address 10.0.0.2 255.255.255.252",
            "no shutdown",
            "exit",
        ]
    )
    commands.extend(_trunk("gigabitEthernet0/2"))
    commands.extend(_trunk("fastEthernet0/1"))
    commands.extend(_trunk("fastEthernet0/2"))
    commands.extend(_svi(10, "192.168.10.1", dhcp_mode, helper=True))
    commands.extend(_svi(20, "192.168.20.1", dhcp_mode, helper=True))
    commands.extend(_svi(30, "192.168.30.1", dhcp_mode, helper=True, acl=100 if include_acl else None))
    commands.extend(_svi(40, "192.168.40.1", dhcp_mode))
    if dhcp_mode == "ios":
        commands.extend(_dhcp_pool("VLAN10", "192.168.10.0", "192.168.10.1"))
        commands.extend(_dhcp_pool("VLAN20", "192.168.20.0", "192.168.20.1"))
        commands.extend(_dhcp_pool("VLAN30", "192.168.30.0", "192.168.30.1"))
    if include_acl:
        commands.extend(
            [
                "access-list 100 deny ip 192.168.30.0 0.0.0.255 host 192.168.40.20",
                "access-list 100 permit ip any any",
            ]
        )
    commands.extend(_routing_commands("CORE-A", routing_protocol))
    return {"deviceName": name("CORE-A"), "commands": wrap_config(commands, write_memory), "features": ["core", routing_protocol, dhcp_mode, "acl" if include_acl else "no_acl"]}


def _core_b_config(name, routing_protocol: str, dhcp_mode: str, include_acl: bool, write_memory: bool) -> dict[str, Any]:
    commands = ["hostname CORE-B", "no ip domain-lookup"]
    commands.extend(_vlan_batch())
    commands.append("ip routing")
    commands.extend(
        [
            "interface gigabitEthernet0/1",
            "no switchport",
            "ip address 10.0.0.6 255.255.255.252",
            "no shutdown",
            "exit",
        ]
    )
    commands.extend(_trunk("gigabitEthernet0/2"))
    commands.extend(_trunk("fastEthernet0/1"))
    commands.extend(_trunk("fastEthernet0/2"))
    commands.extend(_svi(50, "192.168.50.1", dhcp_mode, helper=True, acl=101 if include_acl else None))
    commands.extend(_svi(99, "192.168.99.1", dhcp_mode))
    if dhcp_mode == "ios":
        commands.extend(_dhcp_pool("VLAN50", "192.168.50.0", "192.168.50.1"))
        commands.extend(_dhcp_pool("VLAN99", "192.168.99.0", "192.168.99.1"))
    if include_acl:
        commands.extend(
            [
                "access-list 101 deny tcp 192.168.50.0 0.0.0.255 host 192.168.40.30 eq 21",
                "access-list 101 permit ip any any",
            ]
        )
    commands.extend(_routing_commands("CORE-B", routing_protocol))
    return {"deviceName": name("CORE-B"), "commands": wrap_config(commands, write_memory), "features": ["core", routing_protocol, dhcp_mode, "acl" if include_acl else "no_acl"]}


def _dist_config(name, role: str, write_memory: bool) -> dict[str, Any]:
    commands = [f"hostname {role}", "no ip domain-lookup"]
    commands.extend(_vlan_batch())
    commands.extend(_trunk("gigabitEthernet0/1"))
    for port in ("fastEthernet0/1", "fastEthernet0/2", "fastEthernet0/3"):
        commands.extend(_trunk(port))
    return {"deviceName": name(role), "commands": wrap_config(commands, write_memory), "features": ["distribution", "trunk"]}


def _server_switch_config(name, write_memory: bool) -> dict[str, Any]:
    commands = ["hostname SW-SRV", "no ip domain-lookup"]
    commands.extend(_vlan_batch())
    commands.extend(_trunk("gigabitEthernet0/1"))
    commands.extend(_trunk("gigabitEthernet0/2"))
    commands.extend(
        [
            "interface range fastEthernet0/1-4",
            "switchport mode access",
            "switchport access vlan 40",
            "spanning-tree portfast",
            "exit",
        ]
    )
    commands.extend(_trunk("fastEthernet0/23"))
    return {"deviceName": name("SW-SRV"), "commands": wrap_config(commands, write_memory), "features": ["server_access", "vlan40"]}


def _access_switch_config(name, role: str, vlan: int, write_memory: bool) -> dict[str, Any]:
    commands = [f"hostname {role}", "no ip domain-lookup"]
    commands.extend(_vlan_batch())
    commands.extend(_trunk("gigabitEthernet0/1"))
    commands.extend(
        [
            "interface range fastEthernet0/1-12",
            "switchport mode access",
            f"switchport access vlan {vlan}",
            "spanning-tree portfast",
            "exit",
        ]
    )
    return {"deviceName": name(role), "commands": wrap_config(commands, write_memory), "features": ["access", f"vlan{vlan}"]}


def _dhcp_pool(pool: str, network: str, gateway: str) -> list[str]:
    base = gateway.rsplit(".", 1)[0]
    return [
        f"ip dhcp excluded-address {gateway} {base}.20",
        f"ip dhcp pool {pool}",
        f"network {network} 255.255.255.0",
        f"default-router {gateway}",
        "dns-server 192.168.40.10",
        "domain-name campus.local",
        "exit",
    ]


def _routing_commands(role: str, protocol: str) -> list[str]:
    if protocol == "static":
        return _static_routing(role)
    if protocol == "rip":
        return _rip_routing(role)
    if protocol == "ospf":
        return _ospf_routing(role)
    if protocol == "eigrp":
        return _eigrp_routing(role)
    raise ValueError(f"unsupported routing protocol: {protocol}")


def _static_routing(role: str) -> list[str]:
    if role == "EDGE":
        return [
            "ip route 192.168.10.0 255.255.255.0 10.0.0.2",
            "ip route 192.168.20.0 255.255.255.0 10.0.0.2",
            "ip route 192.168.30.0 255.255.255.0 10.0.0.2",
            "ip route 192.168.40.0 255.255.255.0 10.0.0.2",
            "ip route 192.168.50.0 255.255.255.0 10.0.0.6",
            "ip route 192.168.99.0 255.255.255.0 10.0.0.6",
            "ip route 0.0.0.0 0.0.0.0 203.0.113.1",
        ]
    if role == "CORE-A":
        return ["ip route 0.0.0.0 0.0.0.0 10.0.0.1"]
    if role == "CORE-B":
        return ["ip route 0.0.0.0 0.0.0.0 10.0.0.5"]
    return []


def _rip_routing(role: str) -> list[str]:
    commands = ["router rip", "version 2", "no auto-summary"]
    if role == "EDGE":
        commands.extend(["network 10.0.0.0", "default-information originate", "exit", "ip route 0.0.0.0 0.0.0.0 203.0.113.1"])
    elif role == "CORE-A":
        commands.extend(["network 10.0.0.0", "network 192.168.10.0", "network 192.168.20.0", "network 192.168.30.0", "network 192.168.40.0"])
    elif role == "CORE-B":
        commands.extend(["network 10.0.0.0", "network 192.168.50.0", "network 192.168.99.0"])
    return commands


def _ospf_routing(role: str) -> list[str]:
    if role == "EDGE":
        return [
            "router ospf 1",
            "router-id 1.1.1.1",
            "network 10.0.0.0 0.0.0.3 area 0",
            "network 10.0.0.4 0.0.0.3 area 0",
            "default-information originate",
            "exit",
            "ip route 0.0.0.0 0.0.0.0 203.0.113.1",
        ]
    if role == "CORE-A":
        return [
            "router ospf 1",
            "router-id 2.2.2.2",
            "network 10.0.0.0 0.0.0.3 area 0",
            "network 192.168.10.0 0.0.0.255 area 0",
            "network 192.168.20.0 0.0.0.255 area 0",
            "network 192.168.30.0 0.0.0.255 area 0",
            "network 192.168.40.0 0.0.0.255 area 0",
        ]
    if role == "CORE-B":
        return [
            "router ospf 1",
            "router-id 3.3.3.3",
            "network 10.0.0.4 0.0.0.3 area 0",
            "network 192.168.50.0 0.0.0.255 area 0",
            "network 192.168.99.0 0.0.0.255 area 0",
        ]
    return []


def _eigrp_routing(role: str) -> list[str]:
    commands = ["router eigrp 100", "no auto-summary"]
    if role == "EDGE":
        commands.extend(["network 10.0.0.0 0.0.0.3", "network 10.0.0.4 0.0.0.3", "redistribute static", "exit", "ip route 0.0.0.0 0.0.0.0 203.0.113.1"])
    elif role == "CORE-A":
        commands.extend(
            [
                "network 10.0.0.0 0.0.0.3",
                "network 192.168.10.0 0.0.0.255",
                "network 192.168.20.0 0.0.0.255",
                "network 192.168.30.0 0.0.0.255",
                "network 192.168.40.0 0.0.0.255",
            ]
        )
    elif role == "CORE-B":
        commands.extend(["network 10.0.0.4 0.0.0.3", "network 192.168.50.0 0.0.0.255", "network 192.168.99.0 0.0.0.255"])
    return commands


def _campus_config_tests(name, routing_protocol: str, dhcp_mode: str, include_nat: bool, include_acl: bool) -> list[str]:
    tests = [
        f"{name('CORE-A')}: show ip route",
        f"{name('CORE-B')}: show ip route",
        f"{name('EDGE')}: show ip route",
    ]
    if routing_protocol in {"rip", "ospf", "eigrp"}:
        tests.append(f"{name('EDGE')}: show ip protocols")
    if routing_protocol == "ospf":
        tests.append(f"{name('EDGE')}: show ip ospf neighbor")
    if dhcp_mode == "ios":
        tests.append(f"{name('CORE-A')}: show ip dhcp binding")
    if include_nat:
        tests.append(f"{name('EDGE')}: show ip nat translations after an inside host pings 198.51.100.10")
    if include_acl:
        tests.extend([f"{name('CORE-A')}: show access-lists 100", f"{name('CORE-B')}: show access-lists 101"])
    return tests
