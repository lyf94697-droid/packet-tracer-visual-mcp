from __future__ import annotations

import time
from typing import Any


def _prefix(prefix: str | None) -> str:
    if prefix:
        return prefix.strip().rstrip("-")
    return "PTV-" + time.strftime("%H%M%S")


def _xy(origin_x: float, origin_y: float, scale: float, x: float, y: float) -> dict[str, float]:
    return {"x": round(origin_x + x * scale, 2), "y": round(origin_y + y * scale, 2)}


def build_campus_plan(
    prefix: str | None = None,
    origin_x: float = 80,
    origin_y: float = 60,
    scale: float = 1.0,
) -> dict[str, Any]:
    """Return a complete Packet Tracer visual campus plan.

    The coordinates are intentionally spacious for screen recording: a viewer
    can read the hierarchy at a glance, and devices do not overlap.
    """

    p = _prefix(prefix)

    def name(short: str) -> str:
        return f"{p}-{short}"

    raw_devices = [
        ("ISP", "2911", 1540, 40),
        ("EDGE", "2911", 1280, 40),
        ("CORE-A", "3560-24PS", 760, 190),
        ("CORE-B", "3560-24PS", 1080, 190),
        ("DIST-L", "3560-24PS", 440, 360),
        ("DIST-R", "3560-24PS", 1400, 360),
        ("SW-SRV", "2960-24TT", 920, 390),
        ("SW-MGMT", "2960-24TT", 920, 560),
        ("SW-ADMIN", "2960-24TT", 160, 560),
        ("SW-TEACH", "2960-24TT", 380, 560),
        ("SW-LAB", "2960-24TT", 600, 560),
        ("SW-OFFICE", "2960-24TT", 1240, 560),
        ("SW-DORM", "2960-24TT", 1460, 560),
        ("SW-GUEST", "2960-24TT", 1680, 560),
        ("DNS", "Server-PT", 720, 760),
        ("WEB", "Server-PT", 880, 760),
        ("FTP", "Server-PT", 1040, 760),
        ("DHCP", "Server-PT", 1200, 760),
        ("INET-SRV", "Server-PT", 1700, 220),
        ("ADMIN-PC1", "PC-PT", 90, 760),
        ("ADMIN-PC2", "PC-PT", 220, 760),
        ("TEACH-PC1", "PC-PT", 330, 780),
        ("TEACH-PC2", "PC-PT", 460, 780),
        ("LAB-PC1", "PC-PT", 570, 800),
        ("LAB-PC2", "PC-PT", 700, 800),
        ("NOC-PC", "PC-PT", 840, 950),
        ("OPS-LAP", "Laptop-PT", 1000, 950),
        ("OFFICE-PC1", "PC-PT", 1190, 780),
        ("OFFICE-PC2", "PC-PT", 1320, 780),
        ("DORM-PC1", "PC-PT", 1430, 800),
        ("DORM-PC2", "PC-PT", 1560, 800),
        ("GUEST-LAP1", "Laptop-PT", 1670, 780),
        ("GUEST-LAP2", "Laptop-PT", 1800, 780),
    ]

    devices = []
    for short, model, x, y in raw_devices:
        pos = _xy(origin_x, origin_y, scale, x, y)
        devices.append(
            {
                "name": name(short),
                "model": model,
                "x": pos["x"],
                "y": pos["y"],
                "role": short,
            }
        )

    def link(a: str, ai: str, b: str, bi: str) -> dict[str, str]:
        return {
            "fromDevice": name(a),
            "fromInterface": ai,
            "toDevice": name(b),
            "toInterface": bi,
            "linkType": "auto",
        }

    links = [
        link("EDGE", "GigabitEthernet0/0", "ISP", "GigabitEthernet0/0"),
        link("ISP", "GigabitEthernet0/1", "INET-SRV", "FastEthernet0"),
        link("EDGE", "GigabitEthernet0/1", "CORE-A", "GigabitEthernet0/1"),
        link("EDGE", "GigabitEthernet0/2", "CORE-B", "GigabitEthernet0/1"),
        link("CORE-A", "GigabitEthernet0/2", "CORE-B", "GigabitEthernet0/2"),
        link("CORE-A", "FastEthernet0/1", "DIST-L", "GigabitEthernet0/1"),
        link("CORE-B", "FastEthernet0/1", "DIST-R", "GigabitEthernet0/1"),
        link("CORE-A", "FastEthernet0/2", "SW-SRV", "GigabitEthernet0/1"),
        link("CORE-B", "FastEthernet0/2", "SW-SRV", "GigabitEthernet0/2"),
        link("SW-SRV", "FastEthernet0/23", "SW-MGMT", "GigabitEthernet0/1"),
        link("DIST-L", "FastEthernet0/1", "SW-ADMIN", "GigabitEthernet0/1"),
        link("DIST-L", "FastEthernet0/2", "SW-TEACH", "GigabitEthernet0/1"),
        link("DIST-L", "FastEthernet0/3", "SW-LAB", "GigabitEthernet0/1"),
        link("DIST-R", "FastEthernet0/1", "SW-OFFICE", "GigabitEthernet0/1"),
        link("DIST-R", "FastEthernet0/2", "SW-DORM", "GigabitEthernet0/1"),
        link("DIST-R", "FastEthernet0/3", "SW-GUEST", "GigabitEthernet0/1"),
        link("SW-SRV", "FastEthernet0/1", "DNS", "FastEthernet0"),
        link("SW-SRV", "FastEthernet0/2", "WEB", "FastEthernet0"),
        link("SW-SRV", "FastEthernet0/3", "FTP", "FastEthernet0"),
        link("SW-SRV", "FastEthernet0/4", "DHCP", "FastEthernet0"),
        link("SW-ADMIN", "FastEthernet0/1", "ADMIN-PC1", "FastEthernet0"),
        link("SW-ADMIN", "FastEthernet0/2", "ADMIN-PC2", "FastEthernet0"),
        link("SW-TEACH", "FastEthernet0/1", "TEACH-PC1", "FastEthernet0"),
        link("SW-TEACH", "FastEthernet0/2", "TEACH-PC2", "FastEthernet0"),
        link("SW-LAB", "FastEthernet0/1", "LAB-PC1", "FastEthernet0"),
        link("SW-LAB", "FastEthernet0/2", "LAB-PC2", "FastEthernet0"),
        link("SW-MGMT", "FastEthernet0/1", "NOC-PC", "FastEthernet0"),
        link("SW-MGMT", "FastEthernet0/2", "OPS-LAP", "FastEthernet0"),
        link("SW-OFFICE", "FastEthernet0/1", "OFFICE-PC1", "FastEthernet0"),
        link("SW-OFFICE", "FastEthernet0/2", "OFFICE-PC2", "FastEthernet0"),
        link("SW-DORM", "FastEthernet0/1", "DORM-PC1", "FastEthernet0"),
        link("SW-DORM", "FastEthernet0/2", "DORM-PC2", "FastEthernet0"),
        link("SW-GUEST", "FastEthernet0/1", "GUEST-LAP1", "FastEthernet0"),
        link("SW-GUEST", "FastEthernet0/2", "GUEST-LAP2", "FastEthernet0"),
    ]

    pc_configs = [
        {"deviceName": name("DNS"), "dhcp": False, "ip": "192.168.40.10", "mask": "255.255.255.0", "gateway": "192.168.40.1", "dns": "192.168.40.10"},
        {"deviceName": name("WEB"), "dhcp": False, "ip": "192.168.40.20", "mask": "255.255.255.0", "gateway": "192.168.40.1", "dns": "192.168.40.10"},
        {"deviceName": name("FTP"), "dhcp": False, "ip": "192.168.40.30", "mask": "255.255.255.0", "gateway": "192.168.40.1", "dns": "192.168.40.10"},
        {"deviceName": name("DHCP"), "dhcp": False, "ip": "192.168.40.40", "mask": "255.255.255.0", "gateway": "192.168.40.1", "dns": "192.168.40.10"},
        {"deviceName": name("INET-SRV"), "dhcp": False, "ip": "198.51.100.10", "mask": "255.255.255.0", "gateway": "198.51.100.1", "dns": "192.168.40.10"},
        {"deviceName": name("ADMIN-PC1"), "dhcp": True},
        {"deviceName": name("ADMIN-PC2"), "dhcp": True},
        {"deviceName": name("TEACH-PC1"), "dhcp": True},
        {"deviceName": name("TEACH-PC2"), "dhcp": True},
        {"deviceName": name("LAB-PC1"), "dhcp": True},
        {"deviceName": name("LAB-PC2"), "dhcp": True},
        {"deviceName": name("NOC-PC"), "dhcp": True},
        {"deviceName": name("OPS-LAP"), "dhcp": True},
        {"deviceName": name("OFFICE-PC1"), "dhcp": True},
        {"deviceName": name("OFFICE-PC2"), "dhcp": True},
        {"deviceName": name("DORM-PC1"), "dhcp": True},
        {"deviceName": name("DORM-PC2"), "dhcp": True},
        {"deviceName": name("GUEST-LAP1"), "dhcp": True},
        {"deviceName": name("GUEST-LAP2"), "dhcp": True},
    ]

    ios_configs = _ios_configs(name)

    service_steps = [
        f"{name('DHCP')}: Services > DHCP > On, add pools VLAN10/20/30/50/99 with DNS 192.168.40.10 and default gateways 192.168.10.1, 192.168.20.1, 192.168.30.1, 192.168.50.1, 192.168.99.1.",
        f"{name('DNS')}: Services > DNS > On, add www.campus.local -> 192.168.40.20 and ftp.campus.local -> 192.168.40.30.",
        f"{name('WEB')}: Services > HTTP > On.",
        f"{name('FTP')}: Services > FTP > On, add user ftpuser / cisco.",
    ]

    tests = [
        "DHCP: access clients should obtain addresses from VLAN 10/20/30/50 pools.",
        "Inter-VLAN: VLAN10 host pings 192.168.40.10 and 192.168.40.20.",
        "NAT/PAT: internal host pings 198.51.100.10, then check NAT translations on EDGE.",
        "ACL allow: VLAN30 can reach DNS 192.168.40.10.",
        "ACL deny: VLAN30 is denied to Web 192.168.40.20; guest VLAN is denied FTP TCP/21.",
    ]

    debug_case = {
        "title": "VLAN30 cannot access the Web server while DNS still works",
        "symptom": "A dorm client in VLAN30 can ping 192.168.40.10 but cannot open http://192.168.40.20.",
        "expectedCause": "ACL 100 is applied inbound on interface VLAN30 and blocks VLAN30 to the Web server.",
        "checks": [
            f"On {name('CORE-A')}: show access-lists 100",
            f"On {name('CORE-A')}: show ip interface vlan 30",
            "From a VLAN30 client: ping 192.168.40.10 should pass, ping 192.168.40.20 or HTTP should fail.",
        ],
        "fixForDemo": [
            f"On {name('CORE-A')}: configure terminal",
            "interface vlan 30",
            "no ip access-group 100 in",
            "end",
            "Retest Web access to prove the ACL caused the failure.",
        ],
        "restore": [
            f"On {name('CORE-A')}: configure terminal",
            "interface vlan 30",
            "ip access-group 100 in",
            "end",
        ],
    }

    return {
        "prefix": p,
        "devices": devices,
        "links": links,
        "pcConfigs": pc_configs,
        "iosConfigs": ios_configs,
        "serviceSteps": service_steps,
        "tests": tests,
        "debugCase": debug_case,
        "summary": {
            "deviceCount": len(devices),
            "linkCount": len(links),
            "vlans": [10, 20, 30, 40, 50, 99],
            "routing": "OSPF with edge default route",
            "security": ["ACL 100 dorm-to-web deny", "ACL 101 guest-to-ftp deny"],
        },
    }


def _ios_configs(name) -> list[dict[str, Any]]:
    vlan_batch = "vlan 10\n name ADMIN\nvlan 20\n name TEACH\nvlan 30\n name DORM\nvlan 40\n name SERVER\nvlan 50\n name GUEST\nvlan 99\n name MGMT"
    trunk_all = "switchport mode trunk\n switchport trunk allowed vlan 10,20,30,40,50,99"

    def sw(device: str, extra: list[str]) -> dict[str, Any]:
        return {
            "deviceName": name(device),
            "commands": ["enable", "configure terminal", vlan_batch] + extra + ["end", "write memory"],
        }

    def access(device: str, vlan: int) -> dict[str, Any]:
        return sw(
            device,
            [
                "interface gigabitEthernet0/1\n " + trunk_all,
                f"interface range fastEthernet0/1-12\n switchport mode access\n switchport access vlan {vlan}\n spanning-tree portfast",
            ],
        )

    configs = [
        {
            "deviceName": name("EDGE"),
            "commands": [
                "enable",
                "configure terminal",
                "hostname EDGE",
                "interface gigabitEthernet0/0\n ip address 203.0.113.2 255.255.255.252\n ip nat outside\n no shutdown",
                "interface gigabitEthernet0/1\n ip address 10.0.0.1 255.255.255.252\n ip nat inside\n no shutdown",
                "interface gigabitEthernet0/2\n ip address 10.0.0.5 255.255.255.252\n ip nat inside\n no shutdown",
                "access-list 1 permit 192.168.0.0 0.0.255.255",
                "ip nat inside source list 1 interface gigabitEthernet0/0 overload",
                "router ospf 1\n router-id 1.1.1.1\n network 10.0.0.0 0.0.0.3 area 0\n network 10.0.0.4 0.0.0.3 area 0\n default-information originate",
                "ip route 0.0.0.0 0.0.0.0 203.0.113.1",
                "end",
                "write memory",
            ],
        },
        {
            "deviceName": name("ISP"),
            "commands": [
                "enable",
                "configure terminal",
                "hostname ISP",
                "interface gigabitEthernet0/0\n ip address 203.0.113.1 255.255.255.252\n no shutdown",
                "interface gigabitEthernet0/1\n ip address 198.51.100.1 255.255.255.0\n no shutdown",
                "ip route 192.168.0.0 255.255.0.0 203.0.113.2",
                "end",
                "write memory",
            ],
        },
        {
            "deviceName": name("CORE-A"),
            "commands": [
                "enable",
                "configure terminal",
                "hostname CORE-A",
                vlan_batch,
                "ip routing",
                "interface gigabitEthernet0/1\n no switchport\n ip address 10.0.0.2 255.255.255.252\n no shutdown",
                "interface gigabitEthernet0/2\n " + trunk_all,
                "interface fastEthernet0/1\n " + trunk_all,
                "interface fastEthernet0/2\n " + trunk_all,
                "interface vlan 10\n ip address 192.168.10.1 255.255.255.0\n ip helper-address 192.168.40.40\n no shutdown",
                "interface vlan 20\n ip address 192.168.20.1 255.255.255.0\n ip helper-address 192.168.40.40\n no shutdown",
                "interface vlan 30\n ip address 192.168.30.1 255.255.255.0\n ip helper-address 192.168.40.40\n ip access-group 100 in\n no shutdown",
                "interface vlan 40\n ip address 192.168.40.1 255.255.255.0\n no shutdown",
                "access-list 100 deny ip 192.168.30.0 0.0.0.255 host 192.168.40.20",
                "access-list 100 permit ip any any",
                "router ospf 1\n router-id 2.2.2.2\n network 10.0.0.0 0.0.0.3 area 0\n network 192.168.10.0 0.0.0.255 area 0\n network 192.168.20.0 0.0.0.255 area 0\n network 192.168.30.0 0.0.0.255 area 0\n network 192.168.40.0 0.0.0.255 area 0",
                "end",
                "write memory",
            ],
        },
        {
            "deviceName": name("CORE-B"),
            "commands": [
                "enable",
                "configure terminal",
                "hostname CORE-B",
                vlan_batch,
                "ip routing",
                "interface gigabitEthernet0/1\n no switchport\n ip address 10.0.0.6 255.255.255.252\n no shutdown",
                "interface gigabitEthernet0/2\n " + trunk_all,
                "interface fastEthernet0/1\n " + trunk_all,
                "interface fastEthernet0/2\n " + trunk_all,
                "interface vlan 50\n ip address 192.168.50.1 255.255.255.0\n ip helper-address 192.168.40.40\n ip access-group 101 in\n no shutdown",
                "interface vlan 99\n ip address 192.168.99.1 255.255.255.0\n no shutdown",
                "access-list 101 deny tcp 192.168.50.0 0.0.0.255 host 192.168.40.30 eq 21",
                "access-list 101 permit ip any any",
                "router ospf 1\n router-id 3.3.3.3\n network 10.0.0.4 0.0.0.3 area 0\n network 192.168.50.0 0.0.0.255 area 0\n network 192.168.99.0 0.0.0.255 area 0",
                "end",
                "write memory",
            ],
        },
        sw("DIST-L", ["interface gigabitEthernet0/1\n " + trunk_all, "interface range fastEthernet0/1-3\n " + trunk_all]),
        sw("DIST-R", ["interface gigabitEthernet0/1\n " + trunk_all, "interface range fastEthernet0/1-3\n " + trunk_all]),
        sw("SW-SRV", ["interface range gigabitEthernet0/1-2\n " + trunk_all, "interface range fastEthernet0/1-4\n switchport mode access\n switchport access vlan 40", "interface fastEthernet0/23\n " + trunk_all]),
        access("SW-ADMIN", 10),
        access("SW-TEACH", 20),
        access("SW-LAB", 20),
        access("SW-OFFICE", 10),
        access("SW-DORM", 30),
        access("SW-GUEST", 50),
        access("SW-MGMT", 99),
    ]
    return configs
