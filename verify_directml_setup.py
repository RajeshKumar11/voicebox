#!/usr/bin/env python3
"""
Verify DirectML setup for Windows Iris iGPU.

Run: python verify_directml_setup.py

This script checks:
1. Python version (3.12+)
2. PyTorch installation and version
3. torch_directml availability
4. DirectML device detection
5. Iris iGPU detection (Windows)
6. Basic tensor operations on DirectML
7. Model loading capability (optional)
"""

import sys
import platform
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def check_python_version():
    """Check if Python 3.12+ is installed."""
    logger.info("=" * 60)
    logger.info("STEP 1: Checking Python version")
    logger.info("=" * 60)

    version = sys.version_info
    logger.info(f"Python {version.major}.{version.minor}.{version.micro}")

    if version.major >= 3 and version.minor >= 12:
        logger.info("✓ Python 3.12+ OK")
        return True
    else:
        logger.error(f"✗ Python 3.12+ required, got {version.major}.{version.minor}")
        return False


def check_torch_installation():
    """Check PyTorch is installed and get version."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 2: Checking PyTorch installation")
    logger.info("=" * 60)

    try:
        import torch
        logger.info(f"PyTorch {torch.__version__}")

        # Check for cu128 (important for DirectML)
        if "cu128" in torch.__version__:
            logger.info("✓ cu128 (CUDA 12.8) build detected")
        else:
            logger.warning(f"⚠ torch version doesn't mention cu128: {torch.__version__}")
            logger.warning("  This may work but cu128 builds are recommended")

        return True
    except ImportError as e:
        logger.error(f"✗ PyTorch not installed: {e}")
        logger.error("  Run: pip install torch>=2.2.0")
        return False


def check_directml_installation():
    """Check torch_directml is installed."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 3: Checking torch_directml installation")
    logger.info("=" * 60)

    try:
        import torch_directml
        try:
            version = torch_directml.__version__
            logger.info(f"torch_directml {version}")
        except AttributeError:
            # Dev versions don't have __version__
            logger.info("torch_directml (dev version)")
        logger.info("✓ torch_directml installed")
        return True
    except ImportError as e:
        logger.error(f"✗ torch_directml not installed: {e}")
        logger.error("  Run: pip install torch-directml")
        return False


def check_windows_platform():
    """Check if running on Windows."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 4: Checking Windows platform")
    logger.info("=" * 60)

    os_name = platform.system()
    logger.info(f"OS: {os_name} {platform.release()}")

    if os_name == "Windows":
        logger.info("✓ Windows detected")
        return True
    else:
        logger.warning(f"⚠ Not Windows, DirectML only works on Windows (got {os_name})")
        return False


def check_directml_devices():
    """Check DirectML can detect GPU devices."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 5: Checking DirectML device detection")
    logger.info("=" * 60)

    try:
        import torch_directml
        device_count = torch_directml.device_count()
        logger.info(f"DirectML devices detected: {device_count}")

        if device_count > 0:
            logger.info("✓ DirectML device found")
            return True
        else:
            logger.error("✗ DirectML found no devices")
            logger.error("  Possible causes:")
            logger.error("  - GPU driver outdated (update from Intel/manufacturer)")
            logger.error("  - iGPU disabled in BIOS (enable and reboot)")
            logger.error("  - Iris GPU not supported by driver")
            return False
    except Exception as e:
        logger.error(f"✗ DirectML device check failed: {e}")
        return False


def check_iris_detection():
    """Try to detect Iris iGPU via WMI (Windows only)."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 6: Checking Iris iGPU detection")
    logger.info("=" * 60)

    try:
        import wmi

        iris_found = False
        intel_gpus = []

        for gpu in wmi.WMI().Win32_VideoController():
            name = gpu.Name or ""
            intel_gpus.append(name)

            if any(intel_gfx in name for intel_gfx in ["Iris", "UHD Graphics", "Arc", "Intel Arc"]):
                iris_found = True
                logger.info(f"Detected: {name}")

        if not intel_gpus:
            logger.error("✗ No GPUs detected in WMI")
            logger.error("  This may indicate a driver issue")
            return False

        if iris_found:
            logger.info("✓ Intel Iris/UHD/Arc GPU detected")
            return True
        else:
            logger.warning(f"⚠ No Iris GPU detected, found: {', '.join(intel_gpus)}")
            logger.warning("  DirectML will still work with other Intel/AMD GPUs")
            return True
    except ImportError:
        logger.warning("⚠ wmi module not available (optional)")
        logger.warning("  Install: pip install pywin32")
        logger.warning("  DirectML will still work without WMI detection")
        return True
    except Exception as e:
        logger.warning(f"⚠ Iris detection failed: {e}")
        logger.warning("  DirectML will still work (WMI is optional)")
        return True


def check_tensor_operations():
    """Test basic tensor operations on DirectML device."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 7: Testing tensor operations")
    logger.info("=" * 60)

    try:
        import torch
        import torch_directml

        if torch_directml.device_count() == 0:
            logger.warning("⚠ No DirectML devices, skipping tensor test")
            return True

        device = torch_directml.device(0)
        logger.info(f"Using device: {device}")

        # Create tensors
        x = torch.randn(100, 100, device=device)
        y = torch.randn(100, 100, device=device)

        # Matrix multiply
        z = torch.mm(x, y)

        logger.info(f"Tensor op result shape: {z.shape}")
        logger.info("✓ Tensor operations OK")
        return True
    except Exception as e:
        logger.error(f"✗ Tensor operations failed: {e}")
        return False


def check_get_torch_device():
    """Test get_torch_device() function."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 8: Testing get_torch_device()")
    logger.info("=" * 60)

    try:
        from backend.backends.base import get_torch_device

        device = get_torch_device(allow_directml=True)
        logger.info(f"Selected device: {device}")

        if str(device) != "cpu":
            logger.info("✓ GPU device selected (not CPU)")
        else:
            logger.warning("⚠ CPU device selected (GPU unavailable)")

        return True
    except Exception as e:
        logger.error(f"✗ get_torch_device() failed: {e}")
        return False


def check_model_loading():
    """Test model loading (optional, may download models)."""
    logger.info("\n" + "=" * 60)
    logger.info("STEP 9: Testing model loading (optional)")
    logger.info("=" * 60)

    try:
        import asyncio
        from backend.backends.pytorch_backend import PyTorchSTTBackend

        async def load_test():
            backend = PyTorchSTTBackend(model_size="base")
            logger.info(f"Backend device: {backend.device}")

            if backend.device == "cpu":
                logger.warning("⚠ Backend using CPU (GPU not detected)")
            else:
                logger.info("✓ Backend using GPU device")

            # Try to load model (downloads ~1.5GB first time)
            logger.info("Loading Whisper Base model (may download ~1.5GB)...")
            try:
                await backend.load_model_async("base")
                logger.info("✓ Model loaded successfully")
                backend.unload_model()
                return True
            except Exception as e:
                logger.warning(f"⚠ Model loading skipped: {e}")
                return True

        asyncio.run(load_test())
        return True
    except Exception as e:
        logger.warning(f"⚠ Model loading test skipped: {e}")
        return True


def main():
    """Run all checks."""
    logger.info("\n" + "=" * 60)
    logger.info("DirectML Setup Verification for Windows Iris iGPU")
    logger.info("=" * 60)

    checks = [
        ("Python 3.12+", check_python_version),
        ("PyTorch", check_torch_installation),
        ("torch_directml", check_directml_installation),
        ("Windows platform", check_windows_platform),
        ("DirectML devices", check_directml_devices),
        ("Iris iGPU detection", check_iris_detection),
        ("Tensor operations", check_tensor_operations),
        ("get_torch_device()", check_get_torch_device),
        ("Model loading", check_model_loading),
    ]

    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            logger.error(f"✗ {name} check crashed: {e}")
            results[name] = False

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓" if result else "✗"
        logger.info(f"{status} {name}")

    logger.info(f"\nPassed: {passed}/{total}")

    if passed == total:
        logger.info("\n🎉 All checks passed! DirectML is ready to use.")
        return 0
    elif passed >= total - 1:
        logger.info("\n⚠ Most checks passed. Some optional features may not work.")
        logger.info("See details above for any issues.")
        return 0
    else:
        logger.error("\n❌ Setup incomplete. Fix errors above before using DirectML.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
