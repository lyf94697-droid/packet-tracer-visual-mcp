from __future__ import annotations

import importlib.util
from pathlib import Path

from pt_visual_mcp.campus import build_campus_plan
from pt_visual_mcp.config_templates import build_campus_config_set
from pt_visual_mcp.tools import TOOLS_BY_NAME
from pt_visual_mcp.validation import build_campus_validation_plan, build_fast_validation_report


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_TOOLS = {
    "ptv_bridgeStatus",
    "ptv_getNetwork",
    "ptv_addDevice",
    "ptv_addDevicesTimeline",
    "ptv_addLink",
    "ptv_addLinksTimeline",
    "ptv_configurePc",
    "ptv_configureIos",
    "ptv_getCommandLog",
    "ptv_runShowCommands",
    "ptv_probeDeviceApi",
    "ptv_probeServerServices",
    "ptv_generateIosTemplate",
    "ptv_generateCampusIosConfig",
    "ptv_generateCampusValidationPlan",
    "ptv_validateCampusFast",
    "ptv_applyCampusIosConfig",
    "ptv_applyIosConfigSet",
    "ptv_getFaultLibrary",
    "ptv_injectFault",
    "ptv_repairFault",
    "ptv_getCampusPlan",
    "ptv_buildCampusRecordingDemo",
}


def main() -> int:
    missing = sorted(REQUIRED_TOOLS - set(TOOLS_BY_NAME))
    if missing:
        raise AssertionError(f"missing MCP tools: {missing}")

    campus = build_campus_plan(prefix="DEMO")
    assert campus["summary"]["deviceCount"] == 33
    assert campus["summary"]["linkCount"] == 34
    assert len(campus["serviceSteps"]) >= 3
    assert campus["debugCase"]["checks"]

    for protocol in ("static", "rip", "ospf", "eigrp"):
        config = build_campus_config_set(prefix="DEMO", routing_protocol=protocol, dhcp_mode="ios")
        assert config["summary"]["deviceConfigCount"] >= 10
        assert protocol in config["summary"]["supports"]

    fast_plan = build_campus_validation_plan(prefix="DEMO", validation_mode="fast")
    standard_plan = build_campus_validation_plan(prefix="DEMO", validation_mode="standard")
    assert fast_plan["summary"]["commandCount"] == 0
    assert standard_plan["summary"]["commandCount"] > 0

    network = {
        "devices": [{"name": item["name"]} for item in campus["devices"]],
        "linkCount": len(campus["links"]),
        "links": [{} for _ in campus["links"]],
    }
    report = build_fast_validation_report(campus, network=network)
    assert report["success"], report

    script_text = _build_script_engine_text()
    assert "ptvActions" in script_text
    assert "runShowCommands" in script_text
    assert "getCommandLog" in script_text
    assert "probeDeviceApi" in script_text
    assert "probeServerServices" in script_text

    print(
        "project check passed: "
        f"{len(TOOLS_BY_NAME)} tools, "
        f"{campus['summary']['deviceCount']} devices, "
        f"{campus['summary']['linkCount']} links"
    )
    return 0


def _build_script_engine_text() -> str:
    path = ROOT / "scripts" / "build_script_engine.py"
    spec = importlib.util.spec_from_file_location("ptv_build_script_engine", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("failed to load scripts/build_script_engine.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build("file:///tmp/ptv-test.html")


if __name__ == "__main__":
    raise SystemExit(main())
