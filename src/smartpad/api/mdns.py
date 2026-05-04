"""mDNS broadcast — SPEC.MD section 13.

Registers _smartpad._tcp.local. so other SmartPad instances on the same
WiFi can discover this one. Wrapped in try/except so missing zeroconf
dependency or network issues never crash the app.
"""

from __future__ import annotations

import socket
from typing import Any

from loguru import logger

_service: Any = None
_zeroconf: Any = None


def start_mdns(device_id: str, port: int = 7823) -> bool:
    """Register the SmartPad mDNS service. Returns True on success."""
    global _service, _zeroconf
    try:
        from zeroconf import ServiceInfo, Zeroconf

        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

        _zeroconf = Zeroconf()
        _service = ServiceInfo(
            "_smartpad._tcp.local.",
            f"{device_id}._smartpad._tcp.local.",
            addresses=[socket.inet_aton(local_ip)],
            port=port,
            properties={"device_id": device_id, "version": "0.1.0"},
        )
        _zeroconf.register_service(_service)
        logger.info("mDNS: registered _smartpad._tcp.local. on {}:{}", local_ip, port)
        return True
    except Exception as exc:
        logger.warning("mDNS registration failed (non-fatal): {}", exc)
        return False


def stop_mdns() -> None:
    global _service, _zeroconf
    if _zeroconf and _service:
        try:
            _zeroconf.unregister_service(_service)
            _zeroconf.close()
        except Exception:
            pass
    _service = None
    _zeroconf = None
