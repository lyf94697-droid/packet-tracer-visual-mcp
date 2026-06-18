from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
from typing import Any

import mcp.types as mcp_types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .bridge import PacketTracerBridge
from .campus import build_campus_plan
from .config_templates import (
    build_campus_config_set,
    build_fault_plan,
    get_fault_library,
    render_ios_template,
)
from .tools import TOOLS, TOOLS_BY_NAME
from .validation import (
    build_campus_validation_plan,
    build_fast_validation_report,
    infer_campus_prefix_from_network,
)

log = logging.getLogger(__name__)


def _text(payload: Any) -> list[mcp_types.TextContent]:
    if isinstance(payload, str):
        body = payload
    else:
        body = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    return [mcp_types.TextContent(type="text", text=body)]


def _args(arguments: Any) -> dict[str, Any]:
    if arguments is None:
        return {}
    if not isinstance(arguments, dict):
        raise ValueError("tool arguments must be a JSON object")
    return arguments


def _num(args: dict[str, Any], key: str, default: float) -> float:
    value = args.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(args: dict[str, Any], key: str, default: int) -> int:
    value = args.get(key, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _bool(args: dict[str, Any], key: str, default: bool) -> bool:
    value = args.get(key, default)
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _campus_config_from_args(args: dict[str, Any]) -> dict[str, Any]:
    return build_campus_config_set(
        prefix=args.get("prefix") or None,
        routing_protocol=str(args.get("routingProtocol") or "ospf"),
        dhcp_mode=str(args.get("dhcpMode") or "ios"),
        include_nat=_bool(args, "includeNatPat", True),
        include_acl=_bool(args, "includeAcl", True),
        write_memory=_bool(args, "writeMemory", True),
    )


def _quality_args(args: dict[str, Any]) -> dict[str, Any]:
    quality_mode = str(args.get("qualityMode") or "fast-safe")
    if quality_mode not in {"max-speed", "fast-safe", "balanced", "strict"}:
        quality_mode = "fast-safe"
    return {
        "qualityMode": quality_mode,
        "maxRetries": max(0, min(10, _int(args, "maxRetries", 3))),
        "retryDelayMs": max(0, min(1000, _int(args, "retryDelayMs", 30))),
        "settleMs": max(0, min(1000, _int(args, "settleMs", 15))),
        "minSpacing": max(0, min(300, _int(args, "minSpacing", 55))),
        "validatePlan": _bool(args, "validatePlan", True),
        "verifyAfterBuild": _bool(args, "verifyAfterBuild", True),
        "autoAssignPorts": _bool(args, "autoAssignPorts", True),
        "autoFallback": _bool(args, "autoFallback", True),
    }


def _campus_validation_from_args(args: dict[str, Any]) -> dict[str, Any]:
    return build_campus_validation_plan(
        prefix=args.get("prefix") or None,
        routing_protocol=str(args.get("routingProtocol") or "ospf"),
        dhcp_mode=str(args.get("dhcpMode") or "ios"),
        include_nat=_bool(args, "includeNatPat", True),
        include_acl=_bool(args, "includeAcl", True),
        validation_mode=str(args.get("validationMode") or "fast"),
    )


def _prefix_from_validation_args(args: dict[str, Any], network: dict[str, Any] | None) -> str | None:
    prefix = str(args.get("prefix") or "").strip()
    if prefix:
        return prefix.rstrip("-")

    for key in ("buildResult", "applyResult"):
        value = args.get(key)
        if not isinstance(value, dict):
            continue
        direct = str(value.get("prefix") or "").strip()
        if direct:
            return direct.rstrip("-")
        config_set = value.get("configSet")
        if isinstance(config_set, dict):
            nested = str(config_set.get("prefix") or "").strip()
            if nested:
                return nested.rstrip("-")

    return infer_campus_prefix_from_network(network)


async def _apply_ios_configs(bridge: PacketTracerBridge, configs: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        await bridge.wait_connected(timeout=5.0)
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "configured": 0,
            "total": len(configs),
            "error": str(exc),
            "results": [],
        }

    results = []
    success_count = 0
    for config in configs:
        device_name = str(config.get("deviceName") or "")
        commands = config.get("commands") or []
        try:
            result = await bridge.invoke(
                "configureIos",
                {"deviceName": device_name, "commands": commands},
                timeout=120.0,
            )
            results.append({"deviceName": device_name, "success": True, "result": result})
            success_count += 1
        except Exception as exc:  # noqa: BLE001
            results.append({"deviceName": device_name, "success": False, "error": str(exc)})
    return {
        "success": success_count == len(configs),
        "configured": success_count,
        "total": len(configs),
        "results": results,
    }


async def _handle_local_tool(name: str, args: dict[str, Any], bridge: PacketTracerBridge) -> dict[str, Any]:
    if name == "ptv_bridgeStatus":
        return {"success": True, "bridge": bridge.state().__dict__}

    if name == "ptv_generateIosTemplate":
        template = render_ios_template(str(args.get("template") or ""), args.get("params") or {})
        return {"success": True, "template": template}

    if name == "ptv_generateCampusIosConfig":
        config_set = _campus_config_from_args(args)
        return {"success": True, "configSet": config_set}

    if name == "ptv_generateCampusValidationPlan":
        plan = _campus_validation_from_args(args)
        return {"success": True, "validationPlan": plan}

    if name == "ptv_validateCampusFast":
        network = None
        canvas_error = None
        if _bool(args, "checkCanvas", True):
            if bridge.is_connected:
                try:
                    network = await bridge.invoke("getNetwork", {}, timeout=5.0)
                except Exception as exc:  # noqa: BLE001
                    canvas_error = str(exc)
            else:
                canvas_error = "Packet Tracer bridge is not connected; skipped the canvas snapshot for speed."

        raw_plan = args.get("plan")
        if isinstance(raw_plan, dict) and raw_plan.get("devices"):
            plan = raw_plan
        else:
            prefix = _prefix_from_validation_args(args, network)
            plan = build_campus_plan(
                prefix=prefix,
                origin_x=_num(args, "originX", 80),
                origin_y=_num(args, "originY", 60),
                scale=_num(args, "scale", 1.0),
            )

        report = build_fast_validation_report(
            plan,
            network=network,
            apply_result=args.get("applyResult"),
            build_result=args.get("buildResult"),
            check_canvas=_bool(args, "checkCanvas", True),
            canvas_error=canvas_error,
        )
        return {"success": report["success"], "report": report}

    if name == "ptv_applyCampusIosConfig":
        config_set = _campus_config_from_args(args)
        apply_result = await _apply_ios_configs(bridge, config_set["configs"])
        return {"success": apply_result["success"], "configSet": config_set, "applyResult": apply_result}

    if name == "ptv_applyIosConfigSet":
        configs = args.get("configs") or []
        if not isinstance(configs, list):
            raise ValueError("configs must be an array")
        apply_result = await _apply_ios_configs(bridge, configs)
        return {"success": apply_result["success"], "applyResult": apply_result}

    if name == "ptv_getFaultLibrary":
        return {"success": True, "library": get_fault_library()}

    if name == "ptv_injectFault":
        plan = build_fault_plan(str(args.get("faultId") or ""), args.get("prefix") or None, "inject")
        if not _bool(args, "apply", False):
            return {"success": True, "plan": plan, "applied": False}
        apply_result = await _apply_ios_configs(bridge, plan["configs"])
        return {"success": apply_result["success"], "plan": plan, "applied": True, "applyResult": apply_result}

    if name == "ptv_repairFault":
        plan = build_fault_plan(str(args.get("faultId") or ""), args.get("prefix") or None, "repair")
        if not _bool(args, "apply", False):
            return {"success": True, "plan": plan, "applied": False}
        apply_result = await _apply_ios_configs(bridge, plan["configs"])
        return {"success": apply_result["success"], "plan": plan, "applied": True, "applyResult": apply_result}

    if name == "ptv_getCampusPlan":
        plan = build_campus_plan(
            prefix=args.get("prefix") or None,
            origin_x=_num(args, "originX", 80),
            origin_y=_num(args, "originY", 60),
            scale=_num(args, "scale", 1.0),
        )
        return {"success": True, "plan": plan}

    if name == "ptv_buildCampusRecordingDemo":
        plan = build_campus_plan(
            prefix=args.get("prefix") or None,
            origin_x=_num(args, "originX", 80),
            origin_y=_num(args, "originY", 60),
            scale=_num(args, "scale", 1.0),
        )
        quality = _quality_args(args)
        payload = {
            "plan": plan,
            "deviceDelayMs": max(0, min(10000, _int(args, "deviceDelayMs", 120))),
            "linkDelayMs": max(0, min(10000, _int(args, "linkDelayMs", 60))),
            "configureIos": bool(args.get("configureDevices", False)),
            "configurePc": True,
            **quality,
        }
        bridge_result = await bridge.invoke("buildTimeline", payload, timeout=420.0)
        fast_validation = build_fast_validation_report(plan, build_result=bridge_result, check_canvas=False)
        return {
            "success": bool(bridge_result.get("success", True)),
            "summary": plan["summary"],
            "prefix": plan["prefix"],
            "quality": quality,
            "bridgeResult": bridge_result,
            "fastValidation": fast_validation,
            "serviceSteps": plan["serviceSteps"],
            "tests": plan["tests"],
            "debugCase": plan["debugCase"],
        }

    raise ValueError(f"unknown local tool: {name}")


def make_server(bridge: PacketTracerBridge) -> Server:
    app = Server("packet-tracer-visual-mcp")
    descriptors = [
        mcp_types.Tool(
            name=tool["name"],
            description=tool["description"],
            inputSchema=tool["inputSchema"],
        )
        for tool in TOOLS
    ]

    @app.list_tools()
    async def list_tools() -> list[mcp_types.Tool]:
        return descriptors

    @app.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[mcp_types.TextContent]:
        if name not in TOOLS_BY_NAME:
            return _text({"success": False, "error": f"unknown tool: {name}"})

        try:
            call_args = _args(arguments)
            tool = TOOLS_BY_NAME[name]
            if tool.get("local"):
                result = await _handle_local_tool(name, call_args, bridge)
            else:
                action = str(tool["action"])
                timeout = float(tool.get("timeout", 60.0))
                result = await bridge.invoke(action, call_args, timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            log.exception("Tool %s failed", name)
            return _text({"success": False, "error": str(exc), "tool": name})

        return _text(result)

    return app


async def run(host: str, port: int) -> None:
    bridge = PacketTracerBridge(host=host, port=port)
    await bridge.start()
    try:
        app = make_server(bridge)
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())
    finally:
        await bridge.stop()


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pt-visual-mcp",
        description="Original Packet Tracer lab automation MCP server.",
    )
    parser.add_argument("--host", default=os.environ.get("PTV_MCP_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PTV_MCP_PORT", "7541")))
    parser.add_argument("--log-level", default=os.environ.get("PTV_MCP_LOG_LEVEL", "INFO"))
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        asyncio.run(run(args.host, args.port))
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
