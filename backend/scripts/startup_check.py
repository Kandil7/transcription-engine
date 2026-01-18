#!/usr/bin/env python3
"""Pre-startup validation script for Transcription Engine."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.core.validation import validate_all
from structlog import get_logger

logger = get_logger(__name__)


async def main():
    """Run startup validation checks."""
    print("=" * 60)
    print("Transcription Engine - Startup Validation")
    print("=" * 60)
    print(f"Environment: {settings.environment.value}")
    print(f"Profile: {settings.detected_profile.value}")
    print(f"GPU Memory: {settings.gpu_memory_gb:.2f} GB")
    print(f"CPU Cores: {settings.cpu_cores}")
    print("-" * 60)
    
    warnings = await validate_all()
    
    if warnings:
        print("\n⚠️  Validation Warnings:")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")
        print("\n⚠️  Application may not function correctly with these warnings.")
        return 1
    else:
        print("\n✅ All validations passed!")
        print("✅ Application is ready to start.")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
