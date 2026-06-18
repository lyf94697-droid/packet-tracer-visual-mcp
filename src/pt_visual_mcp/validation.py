from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .config_templates import default_prefix


VALIDATION_MODES = {"off", "fast", "standard", "strict"}
EXPECTED_CAMPUS_DEVICE_COUNT = 33
EXPECTED_CAMPUS_LINK_COUNT = 34
CAMPUS_ROLES = [
    "ISP",
    "EDGE",
    "CORE-A",
    "CORE-B",
    "DIST-L",
    "DIST-R",
    "SW-SRV",
    "SW-MGMT",
    "SW-ADMIN",
    "SW-TEACH",
    "SW-LAB",
    "SW-OFFICE",
    "SW-DORM",
    "SW-GUEST",
    "DNS",
    "WEB",
    "FTP",
    "DHCP",
    "INET-SRV",
    "ADMIN-PC1",
    "ADMIN-PC2",
    "TEACH-PC1",
    "TEACH-PC2",
    "LAB-PC1",
    "LAB-PC2",
    "NOC-PC",
    "OPS-LAP",
    "OFFICE-PC1",
    "OFFICE-PC2",
    "DORM-PC1",
    "DORM-PC2",
    "GUEST-LAP1",
    "GUEST-LAP2",
]
KEY_FAST_ROLES = ["EDGE", "CORE-A", "CORE-B", "SW-SRV", "DNS", "WEB", "FTP", "DHCP"]


def normalize_validation_mode(value: str | None = None) -> str:
    mode = str(value or "fast").strip().lower().replace("_", "-")
    if mode not in VALIDATION_MODES:
        raise ValueError("validationMode must be one of: off, fast, standard, strict")
    return mode


def infer_campus_prefix_from_network(network: dict[str, Any] | None) -> str | None:
    if not network:
        return None
    names = [str(device.get("name") or "") for device in network.get("devices", [])]
    counts: Counter[str] = Counter()
    for role in CAMPUS_ROLES:
        suffix = f"-{role}"
        for name in names:
            if name.endswith(suffix) and len(name) > len(suffix):
                counts[name[: -len(suffix)]] += 1
    if not counts:
        return None
    prefix, count = counts.most_common(1)[0]
    return prefix if count >= 3 else None


def build_campus_validation_plan(
    prefix: str | None = None,
    routing_protocol: str = "ospf",
    dhcp_mode: str = "ios",
    include_nat: bool = True,
    include_acl: bool = True,
    validation_mode: str = "fast",
) -> dict[str, Any]:
    routing_protocol = routing_protocol.lower()
    dhcp_mode = dhcp_mode.lower()
    mode = normalize_validation_mode(validation_mode)
    p = default_prefix(prefix)

    def name(short: str) -> str:
        return f"{p}-{short}"

    if mode in {"off", "fast"}:
        return _build_light_validation_plan(
            p,
            routing_protocol,
            dhcp_mode,
            include_nat,
            include_acl,
            mode,
        )

    checks: list[dict[str, Any]] = []

    checks.extend(
        [
            _check(
                "vlan-core-a",
                name("CORE-A"),
                ["show vlan brief"],
                "VLANs 10/20/30/40 should exist on CORE-A.",
                ["10", "20", "30", "40"],
            ),
            _check(
                "vlan-core-b",
                name("CORE-B"),
                ["show vlan brief"],
                "VLANs 50/99 should exist on CORE-B.",
                ["50", "99"],
            ),
            _check(
                "trunks-core-a",
                name("CORE-A"),
                ["show interfaces trunk"],
                "CORE-A trunk ports should allow VLAN 10,20,30,40,50,99.",
                ["10", "20", "30", "40", "50", "99"],
            ),
            _check(
                "trunks-core-b",
                name("CORE-B"),
                ["show interfaces trunk"],
                "CORE-B trunk ports should allow VLAN 10,20,30,40,50,99.",
                ["10", "20", "30", "40", "50", "99"],
            ),
            _check(
                "routing-core-a",
                name("CORE-A"),
                ["show ip route"],
                "CORE-A should have connected VLAN networks and an upstream route.",
                ["192.168.10.0", "192.168.20.0", "192.168.30.0", "192.168.40.0"],
            ),
            _check(
                "routing-core-b",
                name("CORE-B"),
                ["show ip route"],
                "CORE-B should have connected VLAN networks and an upstream route.",
                ["192.168.50.0", "192.168.99.0"],
            ),
            _check(
                "routing-edge",
                name("EDGE"),
                ["show ip route"],
                "EDGE should know campus networks and default route.",
                ["0.0.0.0", "192.168"],
            ),
        ]
    )

    if routing_protocol == "ospf":
        checks.extend(
            [
                _check(
                    "ospf-edge",
                    name("EDGE"),
                    ["show ip protocols", "show ip ospf neighbor", "show ip route ospf"],
                    "EDGE should run OSPF and learn/advertise campus routes.",
                    ["ospf", "10.0.0.0", "10.0.0.4"],
                ),
                _check(
                    "ospf-core-a",
                    name("CORE-A"),
                    ["show ip protocols", "show ip ospf neighbor"],
                    "CORE-A should form OSPF adjacency toward EDGE.",
                    ["ospf"],
                ),
                _check(
                    "ospf-core-b",
                    name("CORE-B"),
                    ["show ip protocols", "show ip ospf neighbor"],
                    "CORE-B should form OSPF adjacency toward EDGE.",
                    ["ospf"],
                ),
            ]
        )
    elif routing_protocol == "rip":
        checks.append(
            _check(
                "rip-routing",
                name("EDGE"),
                ["show ip protocols", "show ip route rip"],
                "RIP v2 should be active and campus routes should be present.",
                ["rip", "Routing Protocol is"],
            )
        )
    elif routing_protocol == "eigrp":
        checks.append(
            _check(
                "eigrp-routing",
                name("EDGE"),
                ["show ip protocols", "show ip eigrp neighbors", "show ip route eigrp"],
                "EIGRP AS 100 should be active and neighbor/routes should appear.",
                ["eigrp", "100"],
            )
        )
    elif routing_protocol == "static":
        checks.extend(
            [
                _check(
                    "static-edge",
                    name("EDGE"),
                    ["show ip route static"],
                    "EDGE should have static routes for campus VLAN networks and internet default route.",
                    ["192.168.10.0", "192.168.50.0", "0.0.0.0"],
                ),
                _check(
                    "static-core-a",
                    name("CORE-A"),
                    ["show ip route static"],
                    "CORE-A should have a default route toward EDGE.",
                    ["0.0.0.0", "10.0.0.1"],
                ),
                _check(
                    "static-core-b",
                    name("CORE-B"),
                    ["show ip route static"],
                    "CORE-B should have a default route toward EDGE.",
                    ["0.0.0.0", "10.0.0.5"],
                ),
            ]
        )

    if dhcp_mode == "ios":
        checks.extend(
            [
                _check(
                    "dhcp-core-a",
                    name("CORE-A"),
                    ["show ip dhcp pool", "show ip dhcp binding"],
                    "CORE-A should expose DHCP pools/bindings for VLAN10/20/30 after clients request addresses.",
                    ["VLAN10", "VLAN20", "VLAN30"],
                ),
                _check(
                    "dhcp-core-b",
                    name("CORE-B"),
                    ["show ip dhcp pool", "show ip dhcp binding"],
                    "CORE-B should expose DHCP pools/bindings for VLAN50/99 after clients request addresses.",
                    ["VLAN50", "VLAN99"],
                ),
            ]
        )
    elif dhcp_mode == "server-relay":
        checks.extend(
            [
                _check(
                    "dhcp-relay-core-a",
                    name("CORE-A"),
                    ["show running-config | include helper-address"],
                    "CORE-A SVI interfaces should relay DHCP to 192.168.40.40.",
                    ["192.168.40.40"],
                ),
                _check(
                    "dhcp-relay-core-b",
                    name("CORE-B"),
                    ["show running-config | include helper-address"],
                    "CORE-B SVI interfaces should relay DHCP to 192.168.40.40.",
                    ["192.168.40.40"],
                ),
            ]
        )

    if include_nat:
        checks.extend(
            [
                _check(
                    "nat-edge-config",
                    name("EDGE"),
                    ["show running-config | include ip nat", "show access-lists 1"],
                    "EDGE should mark NAT inside/outside and overload campus addresses through G0/0.",
                    ["ip nat inside", "ip nat outside", "overload"],
                ),
                _check(
                    "nat-edge-runtime",
                    name("EDGE"),
                    ["show ip nat translations", "show ip nat statistics"],
                    "After an inside client reaches 198.51.100.10, NAT translations/statistics should change.",
                    ["translations"],
                    runtime=True,
                ),
            ]
        )

    if include_acl:
        checks.extend(
            [
                _check(
                    "acl-core-a",
                    name("CORE-A"),
                    ["show access-lists 100", "show ip interface vlan 30"],
                    "ACL 100 should deny VLAN30 to Web server and permit the rest.",
                    ["192.168.30.0", "192.168.40.20", "permit ip any any"],
                ),
                _check(
                    "acl-core-b",
                    name("CORE-B"),
                    ["show access-lists 101", "show ip interface vlan 50"],
                    "ACL 101 should deny guest VLAN FTP to FTP server and permit the rest.",
                    ["192.168.50.0", "192.168.40.30", "eq 21", "permit ip any any"],
                ),
            ]
        )

    command_set = _command_set(checks)
    return {
        "profile": "campus-validation",
        "prefix": p,
        "validationMode": mode,
        "routingProtocol": routing_protocol,
        "dhcpMode": dhcp_mode,
        "includeNatPat": include_nat,
        "includeAcl": include_acl,
        "checks": checks,
        "commandSet": command_set,
        "summary": {
            "checkCount": len(checks),
            "deviceCount": len(command_set),
            "commandCount": sum(len(item["commands"]) for item in command_set),
        },
        "limitations": [
            "standard/strict validation issues show commands and is slower than fast mode.",
            "Packet Tracer commandLog exposes command history, not guaranteed full show-command output.",
            "Runtime checks such as DHCP binding and NAT translations require traffic to be generated first.",
        ],
    }


def build_fast_validation_report(
    plan: dict[str, Any],
    network: dict[str, Any] | None = None,
    apply_result: dict[str, Any] | None = None,
    build_result: dict[str, Any] | None = None,
    check_canvas: bool = True,
    canvas_error: str | None = None,
) -> dict[str, Any]:
    prefix = str(plan.get("prefix") or "")
    expected_devices = plan.get("devices", []) or []
    expected_links = plan.get("links", []) or []
    expected_names = {str(device.get("name") or "") for device in expected_devices if device.get("name")}
    key_names = {f"{prefix}-{role}" for role in KEY_FAST_ROLES if prefix}
    results: list[dict[str, Any]] = []

    def add(
        check_id: str,
        title: str,
        status: str,
        details: dict[str, Any] | None = None,
        required: bool = True,
    ) -> None:
        results.append(
            {
                "checkId": check_id,
                "title": title,
                "status": status,
                "required": required,
                "details": details or {},
            }
        )

    add(
        "plan-shape",
        "Built-in campus plan contains the expected topology size.",
        "pass"
        if len(expected_devices) == EXPECTED_CAMPUS_DEVICE_COUNT and len(expected_links) == EXPECTED_CAMPUS_LINK_COUNT
        else "fail",
        {
            "expectedDevices": EXPECTED_CAMPUS_DEVICE_COUNT,
            "actualPlannedDevices": len(expected_devices),
            "expectedLinks": EXPECTED_CAMPUS_LINK_COUNT,
            "actualPlannedLinks": len(expected_links),
        },
    )

    build = _unwrap_build_result(build_result)
    if build:
        add(
            "build-result",
            "Packet Tracer build returned success.",
            "pass" if build.get("success", True) is not False else "fail",
            {"success": build.get("success", True), "error": build.get("error")},
        )
        _add_stage_check(results, build, "preflight", "Preflight accepted the plan.", "success")
        _add_stage_check(results, build, "devices", "Device timeline completed.", "added")
        _add_stage_check(results, build, "links", "Link timeline completed.", "added")
        _add_stage_check(results, build, "pcConfigs", "PC/server IP stage completed or was skipped.", "configured")
        _add_stage_check(results, build, "iosConfigs", "IOS configuration stage completed or was skipped.", "configured")
        _add_verify_check(results, build)
    else:
        add("build-result", "No build result was supplied.", "skip", required=False)

    if check_canvas:
        if network:
            actual_names = {str(device.get("name") or "") for device in network.get("devices", [])}
            missing = sorted(expected_names - actual_names)
            missing_keys = sorted(key_names - actual_names)
            actual_link_count = _safe_int(network.get("linkCount"), len(network.get("links", []) or []))
            add(
                "canvas-devices",
                "Canvas contains all expected campus devices.",
                "pass" if not missing else "fail",
                {
                    "expected": len(expected_names),
                    "matched": len(expected_names) - len(missing),
                    "missing": missing[:20],
                    "truncatedMissing": len(missing) > 20,
                },
            )
            add(
                "canvas-key-devices",
                "Canvas contains key routing and service devices.",
                "pass" if not missing_keys else "fail",
                {"keyDevices": sorted(key_names), "missing": missing_keys},
            )
            add(
                "canvas-link-count",
                "Canvas has at least the expected number of links.",
                "pass" if actual_link_count >= len(expected_links) else "fail",
                {"expectedAtLeast": len(expected_links), "actual": actual_link_count},
            )
        else:
            add(
                "canvas-read",
                "Canvas was not checked.",
                "skip",
                {"reason": canvas_error or "Packet Tracer bridge was not connected or checkCanvas was false."},
                required=True,
            )
    else:
        add("canvas-read", "Canvas check intentionally skipped.", "skip", required=False)

    apply = _unwrap_apply_result(apply_result)
    if apply:
        configured = _safe_int(apply.get("configured"), 0)
        total = _safe_int(apply.get("total"), 0)
        failed_items = [
            item
            for item in apply.get("results", []) or []
            if isinstance(item, dict) and item.get("success") is False
        ]
        add(
            "config-apply",
            "IOS configuration apply result has no failed devices.",
            "pass" if apply.get("success", configured == total) and configured == total and not failed_items else "fail",
            {
                "configured": configured,
                "total": total,
                "failedDevices": [item.get("deviceName") for item in failed_items],
            },
        )
    else:
        add("config-apply", "No standalone IOS apply result was supplied.", "skip", required=False)

    failed = [item for item in results if item["status"] == "fail"]
    required_skipped = [item for item in results if item["status"] == "skip" and item.get("required")]
    status = "fail" if failed else "partial" if required_skipped else "pass"
    return {
        "success": status == "pass",
        "status": status,
        "validationMode": "fast",
        "prefix": prefix,
        "canvasChecked": bool(network),
        "checks": results,
        "summary": {
            "totalChecks": len(results),
            "passed": sum(1 for item in results if item["status"] == "pass"),
            "failed": len(failed),
            "skipped": sum(1 for item in results if item["status"] == "skip"),
            "requiredSkipped": len(required_skipped),
            "expectedDevices": len(expected_devices),
            "expectedLinks": len(expected_links),
        },
        "manualServiceSteps": plan.get("serviceSteps", []),
        "limitations": [
            "Fast mode does not run heavy show-command sweeps.",
            "Fast mode proves topology/config workflow health, not every live protocol state.",
            "Use standard or strict validation for slower CLI command checks before final submission.",
        ],
    }


def summarize_validation_execution(plan: dict[str, Any], execution: dict[str, Any]) -> dict[str, Any]:
    executed = _executed_command_map(execution)
    results = []
    for check in plan.get("checks", []):
        commands = check.get("commands", [])
        device = check.get("deviceName", "")
        missing = [command for command in commands if command not in executed.get(device, set())]
        status = "executed_unverified" if not missing else "not_executed"
        results.append(
            {
                "checkId": check["checkId"],
                "deviceName": device,
                "status": status,
                "missingCommands": missing,
                "expectedEvidence": check.get("expectedEvidence", ""),
                "expectedContains": check.get("expectedContains", []),
                "requiresTraffic": check.get("requiresTraffic", False),
            }
        )

    executed_count = sum(1 for item in results if item["status"] == "executed_unverified")
    return {
        "success": executed_count == len(results),
        "mode": "command-log-confirmation",
        "executedChecks": executed_count,
        "totalChecks": len(results),
        "results": results,
        "note": "Show commands were issued and command history was checked. Full output parsing is not available unless Packet Tracer exposes show-command output.",
    }


def _build_light_validation_plan(
    prefix: str,
    routing_protocol: str,
    dhcp_mode: str,
    include_nat: bool,
    include_acl: bool,
    mode: str,
) -> dict[str, Any]:
    checks = [] if mode == "off" else [
        {
            "checkId": "fast-plan-shape",
            "method": "local-plan",
            "expectedEvidence": "33 devices and 34 links in the built-in campus plan.",
        },
        {
            "checkId": "fast-build-result",
            "method": "build-result",
            "expectedEvidence": "preflight, device, link, PC config, IOS config, and verify stages have no failures.",
        },
        {
            "checkId": "fast-canvas-snapshot",
            "method": "single-getNetwork",
            "expectedEvidence": "A single canvas read sees all expected devices and at least 34 links.",
        },
        {
            "checkId": "fast-key-devices",
            "method": "single-getNetwork",
            "expectedEvidence": "EDGE, CORE-A, CORE-B, SW-SRV, DNS, WEB, FTP, and DHCP exist.",
        },
    ]
    return {
        "profile": "campus-validation",
        "prefix": prefix,
        "validationMode": mode,
        "routingProtocol": routing_protocol,
        "dhcpMode": dhcp_mode,
        "includeNatPat": include_nat,
        "includeAcl": include_acl,
        "checks": checks,
        "commandSet": [],
        "summary": {
            "checkCount": len(checks),
            "deviceCount": 0,
            "commandCount": 0,
            "expectedCampusDevices": EXPECTED_CAMPUS_DEVICE_COUNT,
            "expectedCampusLinks": EXPECTED_CAMPUS_LINK_COUNT,
        },
        "limitations": [
            "fast mode does not issue IOS show commands.",
            "Use ptv_validateCampusFast for the lightweight runtime report.",
            "Use validationMode standard or strict when slower command checks are acceptable.",
        ],
    }


def _add_stage_check(
    results: list[dict[str, Any]],
    build: dict[str, Any],
    stage_name: str,
    title: str,
    count_key: str,
) -> None:
    stage = _stage_result(build, stage_name)
    if not stage:
        results.append({"checkId": f"stage-{stage_name}", "title": title, "status": "skip", "required": False, "details": {}})
        return
    if stage.get("skipped"):
        results.append(
            {
                "checkId": f"stage-{stage_name}",
                "title": title,
                "status": "skip",
                "required": False,
                "details": {"skipped": True},
            }
        )
        return
    total = _safe_int(stage.get("total"), 0)
    done = _safe_int(stage.get(count_key), total if stage.get("success", True) else 0)
    failed = _safe_int(stage.get("failed"), max(0, total - done))
    passed = stage.get("success", True) is not False and failed == 0 and (total == 0 or done == total)
    results.append(
        {
            "checkId": f"stage-{stage_name}",
            "title": title,
            "status": "pass" if passed else "fail",
            "required": True,
            "details": {"done": done, "total": total, "failed": failed, "error": stage.get("error")},
        }
    )


def _add_verify_check(results: list[dict[str, Any]], build: dict[str, Any]) -> None:
    stage = _stage_result(build, "verify")
    if not stage:
        results.append({"checkId": "stage-verify", "title": "Post-build verify ran.", "status": "skip", "required": False, "details": {}})
        return
    if stage.get("skipped"):
        results.append(
            {
                "checkId": "stage-verify",
                "title": "Post-build verify was skipped.",
                "status": "skip",
                "required": False,
                "details": {"skipped": True},
            }
        )
        return
    passed = stage.get("success", True) is not False and stage.get("verified", True) is not False
    results.append(
        {
            "checkId": "stage-verify",
            "title": "Post-build verify did not report missing devices or links.",
            "status": "pass" if passed else "fail",
            "required": True,
            "details": {
                "verified": stage.get("verified"),
                "expectedDevices": stage.get("expectedDevices"),
                "expectedLinks": stage.get("expectedLinks"),
                "actualDevices": stage.get("actualDevices"),
                "actualLinks": stage.get("actualLinks"),
                "errors": stage.get("errors", []),
            },
        }
    )


def _unwrap_build_result(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(value, dict) or not value:
        return None
    if isinstance(value.get("bridgeResult"), dict):
        return value["bridgeResult"]
    return value


def _unwrap_apply_result(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(value, dict) or not value:
        return None
    if isinstance(value.get("applyResult"), dict):
        return value["applyResult"]
    return value


def _stage_result(build: dict[str, Any], stage_name: str) -> dict[str, Any] | None:
    for stage in build.get("stages", []) or []:
        if isinstance(stage, dict) and stage.get("name") == stage_name and isinstance(stage.get("result"), dict):
            return stage["result"]
    return None


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _check(
    check_id: str,
    device_name: str,
    commands: list[str],
    expected: str,
    contains: list[str],
    runtime: bool = False,
) -> dict[str, Any]:
    return {
        "checkId": check_id,
        "deviceName": device_name,
        "commands": commands,
        "expectedEvidence": expected,
        "expectedContains": contains,
        "requiresTraffic": runtime,
    }


def _command_set(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for check in checks:
        device = check["deviceName"]
        for command in check["commands"]:
            if command not in grouped[device]:
                grouped[device].append(command)
    return [{"deviceName": device, "commands": commands} for device, commands in sorted(grouped.items())]


def _executed_command_map(execution: dict[str, Any]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    for item in execution.get("results", []):
        device = item.get("deviceName", "")
        for command in item.get("executedCommands", []):
            out[device].add(command)
        for entry in item.get("commandLog", {}).get("entries", []):
            command = entry.get("command")
            if command:
                out[device].add(command)
    return out
