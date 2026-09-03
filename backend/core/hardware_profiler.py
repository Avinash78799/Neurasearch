"""
NeuraSearch – Hardware Auto-Detection & Adaptive Profile Engine.
Inspects CPU, System RAM, and GPU VRAM to dynamically configure optimal LLM models,
retrieval depth, and chunk limits tailored to user laptop hardware.
"""

import logging
import platform
import subprocess
import psutil
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from config import settings

logger = logging.getLogger("neurasearch.hardware")


class HardwareSpec(BaseModel):
    cpu_name: str
    cpu_cores: int
    system_ram_gb: float
    gpu_name: str
    gpu_vram_gb: float
    os_name: str
    recommended_profile: str


class ProfileConfig(BaseModel):
    id: str
    name: str
    description: str
    target_hardware: str
    recommended_model: str
    top_k: int
    chunk_size: int
    chunk_overlap: int
    num_ctx: int
    estimated_latency_sec: str
    badge_color: str


PROFILES: Dict[str, ProfileConfig] = {
    "eco": ProfileConfig(
        id="eco",
        name="Eco / Ultra-Light (4GB VRAM & Budget Laptops)",
        description="Optimized for entry-level laptops, GTX 1650, or CPU-only with 8GB RAM. Fast and battery-friendly.",
        target_hardware="Intel i3/i5, 8GB RAM, GTX 1650 (4GB VRAM) or Integrated Graphics",
        recommended_model="llama3.2:3b",
        top_k=3,
        chunk_size=800,
        chunk_overlap=150,
        num_ctx=2048,
        estimated_latency_sec="3–6s",
        badge_color="emerald"
    ),
    "balanced": ProfileConfig(
        id="balanced",
        name="Balanced / Creator (6–8GB VRAM Gaming Laptops)",
        description="Optimized for mid-range gaming laptops with RTX 3050/3060/4050 and 16GB RAM. Native tool-calling with Qwen 3 / Llama 3.1.",
        target_hardware="Intel i7/Ryzen 7, 16GB RAM, RTX 3050/3060/4050 (6–8GB VRAM)",
        recommended_model="qwen3:8b",
        top_k=5,
        chunk_size=1000,
        chunk_overlap=200,
        num_ctx=4096,
        estimated_latency_sec="6–12s",
        badge_color="amber"
    ),

    "turbo": ProfileConfig(
        id="turbo",
        name="Cloud Turbo & Workstation (Groq 70B / High-End)",
        description="Free Groq Cloud LPU or RTX 4080/4090 / Apple M-series. Instant PhD-grade research on any laptop.",
        target_hardware="Any laptop via Free Groq LPU (350 tok/s) OR 16GB+ VRAM local GPU",
        recommended_model="llama-3.3-70b-versatile",
        top_k=8,
        chunk_size=1200,
        chunk_overlap=250,
        num_ctx=8192,
        estimated_latency_sec="1–3s",
        badge_color="violet"
    )
}


class HardwareProfiler:
    """Detects system hardware and applies adaptive performance profiles."""

    @staticmethod
    def detect_hardware() -> HardwareSpec:
        """Inspects CPU, RAM, and GPU to return accurate hardware specs."""
        cpu_cores = psutil.cpu_count(logical=True) or 4
        ram_bytes = psutil.virtual_memory().total
        ram_gb = round(ram_bytes / (1024 ** 3), 1)
        os_name = f"{platform.system()} {platform.release()}"
        cpu_name = platform.processor() or "Multi-core CPU"

        gpu_name = "Integrated / CPU"
        gpu_vram_gb = 0.0

        # 1. Try PyTorch CUDA inspection if available
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                vram_bytes = torch.cuda.get_device_properties(0).total_memory
                gpu_vram_gb = round(vram_bytes / (1024 ** 3), 1)
        except Exception:
            pass

        # 2. Try nvidia-smi command if torch not installed or not CUDA-enabled
        if gpu_vram_gb == 0.0:
            try:
                res = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if res.returncode == 0 and res.stdout.strip():
                    line = res.stdout.strip().split("\n")[0]
                    parts = line.split(",")
                    if len(parts) >= 2:
                        gpu_name = parts[0].strip()
                        mb_val = float(parts[1].strip())
                        gpu_vram_gb = round(mb_val / 1024.0, 1)
            except Exception:
                pass

        # Determine recommended profile
        if gpu_vram_gb >= 12.0 or settings.llm_provider in ["groq", "openai", "deepseek"]:
            recommended = "turbo"
        elif gpu_vram_gb >= 6.0 and ram_gb >= 14.0:
            recommended = "balanced"
        else:
            recommended = "eco"

        return HardwareSpec(
            cpu_name=cpu_name,
            cpu_cores=cpu_cores,
            system_ram_gb=ram_gb,
            gpu_name=gpu_name,
            gpu_vram_gb=gpu_vram_gb,
            os_name=os_name,
            recommended_profile=recommended
        )

    @staticmethod
    def apply_profile(profile_id: str) -> Dict[str, Any]:
        """Apply a hardware-adaptive profile to active runtime configuration."""
        profile = PROFILES.get(profile_id.lower().strip())
        if not profile:
            raise ValueError(f"Unknown hardware profile '{profile_id}'. Available: {list(PROFILES.keys())}")

        logger.info("Applying adaptive hardware profile: %s (%s)", profile.name, profile.recommended_model)

        settings.top_k_retrieval = profile.top_k
        settings.chunk_size = profile.chunk_size
        settings.chunk_overlap = profile.chunk_overlap
        settings.llm_num_ctx = profile.num_ctx

        if profile_id == "turbo":
            settings.llm_provider = "groq" if settings.groq_api_key else "ollama"
            settings.groq_model = profile.recommended_model
        else:
            settings.llm_provider = "ollama"
            settings.ollama_llm_model = profile.recommended_model

        # Reset LLM singleton to pick up new profile
        import core.model_registry
        core.model_registry._llm = None

        return {
            "status": "success",
            "profile_id": profile.id,
            "profile_name": profile.name,
            "applied_model": profile.recommended_model,
            "top_k": profile.top_k,
            "chunk_size": profile.chunk_size,
            "num_ctx": profile.num_ctx,
            "estimated_latency": profile.estimated_latency_sec
        }
