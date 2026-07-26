import sys
from pathlib import Path

# Stub forwarder to core/config.py for backward compatibility
core_dir = str(Path(__file__).resolve().parent / "core")
if core_dir not in sys.path:
    sys.path.append(core_dir)

from core.config import settings, Settings
