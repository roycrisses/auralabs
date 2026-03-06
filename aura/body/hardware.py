"""Hardware monitoring — CPU, GPU, RAM stats via psutil."""

from __future__ import annotations

import psutil

from aura.config import HARDWARE


def get_system_stats() -> dict:
    """Return current system resource usage."""
    mem = psutil.virtual_memory()
    stats = {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "cpu_freq_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
        "ram_used_gb": round(mem.used / (1024**3), 1),
        "ram_total_gb": round(mem.total / (1024**3), 1),
        "ram_percent": mem.percent,
        "hardware_profile": {
            "cpu": HARDWARE.cpu_model,
            "gpu": HARDWARE.gpu_model,
            "gpu_vram_mb": HARDWARE.gpu_vram_mb,
        },
    }

    # Try GPU stats via GPUtil
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            stats["gpu_load_percent"] = round(gpu.load * 100, 1)
            stats["gpu_memory_used_mb"] = round(gpu.memoryUsed, 0)
            stats["gpu_memory_total_mb"] = round(gpu.memoryTotal, 0)
            stats["gpu_temperature_c"] = gpu.temperature
    except Exception:
        stats["gpu_load_percent"] = None
        stats["gpu_note"] = "GPUtil unavailable"

    return stats
