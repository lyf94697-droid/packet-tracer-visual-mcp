from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from typing import Any

from websockets.asyncio.server import ServerConnection, serve

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class BridgeState:
    host: str
    port: int
    connected: bool
    client_name: str | None
    pending_calls: int


class PacketTracerBridge:
    """Small JSON-over-WebSocket bridge used by the PT extension."""

    def __init__(self, host: str = "127.0.0.1", port: int = 7541) -> None:
        self.host = host
        self.port = port
        self._server: Any = None
        self._client: ServerConnection | None = None
        self._client_name: str | None = None
        self._connected = asyncio.Event()
        self._pending: dict[str, asyncio.Future[dict[str, Any]]] = {}
        self._send_lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    def state(self) -> BridgeState:
        return BridgeState(
            host=self.host,
            port=self.port,
            connected=self.is_connected,
            client_name=self._client_name,
            pending_calls=len(self._pending),
        )

    async def start(self) -> None:
        self._server = await serve(self._handle_client, self.host, self.port)
        log.info("Packet Tracer visual bridge listening on ws://%s:%s/ws", self.host, self.port)

    async def stop(self) -> None:
        for future in self._pending.values():
            if not future.done():
                future.set_exception(RuntimeError("bridge stopped"))
        self._pending.clear()
        if self._client is not None:
            await self._client.close()
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()

    async def wait_connected(self, timeout: float = 30.0) -> None:
        if self.is_connected:
            return
        try:
            await asyncio.wait_for(self._connected.wait(), timeout=timeout)
        except asyncio.TimeoutError as exc:
            raise RuntimeError(
                "Packet Tracer extension is not connected. Open Packet Tracer and the PT Visual MCP bridge window."
            ) from exc

    async def invoke(self, action: str, payload: dict[str, Any] | None = None, timeout: float = 60.0) -> dict[str, Any]:
        await self.wait_connected()
        if self._client is None:
            raise RuntimeError("Packet Tracer bridge disconnected")

        call_id = uuid.uuid4().hex
        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending[call_id] = future

        message = {
            "type": "call",
            "id": call_id,
            "action": action,
            "payload": payload or {},
        }
        try:
            async with self._send_lock:
                await self._client.send(json.dumps(message, separators=(",", ":")))
            result = await asyncio.wait_for(future, timeout=timeout)
        finally:
            self._pending.pop(call_id, None)

        if not result.get("ok", False):
            raise RuntimeError(str(result.get("error") or "Packet Tracer action failed"))
        data = result.get("data")
        return data if isinstance(data, dict) else {"value": data}

    async def _handle_client(self, websocket: ServerConnection) -> None:
        if self._client is not None and self._client is not websocket:
            await self._client.close()

        self._client = websocket
        self._client_name = None
        self._connected.set()
        log.info("Packet Tracer extension connected")

        try:
            async for raw in websocket:
                await self._dispatch_message(raw)
        finally:
            if self._client is websocket:
                self._client = None
                self._client_name = None
                self._connected.clear()
                for future in self._pending.values():
                    if not future.done():
                        future.set_exception(RuntimeError("Packet Tracer extension disconnected"))
                self._pending.clear()
                log.info("Packet Tracer extension disconnected")

    async def _dispatch_message(self, raw: str | bytes) -> None:
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            log.warning("Ignoring non-JSON bridge message")
            return

        kind = message.get("type")
        if kind == "hello":
            self._client_name = str(message.get("client") or "packet-tracer")
            return

        if kind == "result":
            call_id = str(message.get("id") or "")
            future = self._pending.get(call_id)
            if future is not None and not future.done():
                future.set_result(message)
            return

        if kind == "log":
            log.info("PT: %s", message.get("message", ""))
            return

        log.debug("Ignoring bridge message type %r", kind)
