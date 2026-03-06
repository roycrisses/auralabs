"""System information tools — OS, network, disk, and process details."""

from __future__ import annotations

import platform
import socket

import psutil

from aura.body.registry import register_tool


@register_tool("get_system_info")
def get_system_info() -> dict:
    """Return detailed operating system and hardware information."""
    uname = platform.uname()
    mem = psutil.virtual_memory()
    boot = psutil.boot_time()

    from datetime import datetime

    return {
        "os": f"{uname.system} {uname.release}",
        "os_version": uname.version,
        "hostname": uname.node,
        "architecture": uname.machine,
        "processor": uname.processor,
        "cpu_physical_cores": psutil.cpu_count(logical=False),
        "cpu_logical_cores": psutil.cpu_count(logical=True),
        "cpu_freq_mhz": round(psutil.cpu_freq().current) if psutil.cpu_freq() else None,
        "ram_total_gb": round(mem.total / (1024**3), 1),
        "ram_available_gb": round(mem.available / (1024**3), 1),
        "ram_percent_used": mem.percent,
        "boot_time": datetime.fromtimestamp(boot).isoformat(),
        "python_version": platform.python_version(),
    }


@register_tool("get_network_info")
def get_network_info() -> dict:
    """Return network interface addresses and connection stats."""
    addrs = {}
    for iface, snics in psutil.net_if_addrs().items():
        iface_addrs = []
        for snic in snics:
            if snic.family == socket.AF_INET:
                iface_addrs.append({"ipv4": snic.address, "netmask": snic.netmask})
            elif snic.family == socket.AF_INET6:
                iface_addrs.append({"ipv6": snic.address})
        if iface_addrs:
            addrs[iface] = iface_addrs

    counters = psutil.net_io_counters()

    return {
        "interfaces": addrs,
        "bytes_sent": counters.bytes_sent,
        "bytes_recv": counters.bytes_recv,
        "packets_sent": counters.packets_sent,
        "packets_recv": counters.packets_recv,
    }


@register_tool("get_disk_info")
def get_disk_info() -> list[dict]:
    """Return disk partition usage information."""
    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total_gb": round(usage.total / (1024**3), 1),
                "used_gb": round(usage.used / (1024**3), 1),
                "free_gb": round(usage.free / (1024**3), 1),
                "percent_used": usage.percent,
            })
        except PermissionError:
            continue
    return disks


@register_tool("list_processes")
def list_processes(sort_by: str = "memory", limit: int = 15) -> str:
    """List running processes sorted by CPU or memory usage.

    Args:
        sort_by: Sort key — 'memory' or 'cpu'.
        limit: Number of processes to return (max 50).
    """
    limit = max(1, min(50, limit))
    key = "memory_percent" if sort_by == "memory" else "cpu_percent"

    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = p.info
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    procs.sort(key=lambda x: x.get(key, 0) or 0, reverse=True)

    lines = [f"{'PID':<8} {'CPU%':<8} {'MEM%':<8} NAME"]
    for p in procs[:limit]:
        lines.append(
            f"{p['pid']:<8} {p.get('cpu_percent', 0) or 0:<8.1f} "
            f"{p.get('memory_percent', 0) or 0:<8.1f} {p.get('name', '?')}"
        )
    return "\n".join(lines)
