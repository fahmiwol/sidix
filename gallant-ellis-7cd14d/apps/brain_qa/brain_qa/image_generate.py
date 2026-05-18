"""
image_generate.py — Bridge to SIDIX Image Generation (apps/image_gen)
"""

from __future__ import annotations
import sys
from pathlib import Path

def is_available() -> bool:
    """Check if image generation capabilities are ready."""
    try:
        # Check if apps/image_gen is accessible
        root = Path(__file__).parent.parent.parent.parent
        image_gen_path = root / "apps" / "image_gen"
        if str(image_gen_path) not in sys.path:
            sys.path.append(str(image_gen_path))
        
        # Try importing a core module
        from image_gen.queue import ImageJob
        return True
    except ImportError:
        return False
    except Exception:
        return False

def generate_image(prompt: str) -> dict:
    """Generate an image from a prompt."""
    return {"status": "mock", "url": "image_generation_bridge_active.png"}
