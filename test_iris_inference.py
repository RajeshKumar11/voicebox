#!/usr/bin/env python3
"""
Quick test: Run Whisper (STT) on DirectML/Iris iGPU.

This creates a simple test audio and runs transcription on your Iris GPU.
"""

import sys
import asyncio
import logging
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def test_whisper_on_iris():
    """Test Whisper model on DirectML/Iris iGPU."""
    logger.info("=" * 60)
    logger.info("Testing Whisper STT on Iris iGPU (DirectML)")
    logger.info("=" * 60)

    try:
        import torch
        import torch_directml
        from backend.backends.pytorch_backend import PyTorchSTTBackend

        # Check device
        device_count = torch_directml.device_count()
        logger.info(f"DirectML devices: {device_count}")

        if device_count == 0:
            logger.error("No DirectML devices found!")
            return False

        # Create backend
        logger.info("\n1. Creating Whisper backend...")
        backend = PyTorchSTTBackend(model_size="base")
        logger.info(f"   Device: {backend.device}")

        # Load model
        logger.info("\n2. Loading Whisper Base model (may download ~1.5GB)...")
        await backend.load_model_async("base")
        logger.info("   ✓ Model loaded")

        # Create synthetic audio (silence, 16kHz, 3 seconds)
        logger.info("\n3. Generating test audio...")
        sample_rate = 16000
        duration_sec = 3
        silence = np.zeros(sample_rate * duration_sec, dtype=np.float32)

        # Save to temp file
        import tempfile
        import soundfile as sf

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_audio_path = f.name
            sf.write(temp_audio_path, silence, sample_rate)

        logger.info(f"   Temp audio: {temp_audio_path}")

        # Run transcription
        logger.info("\n4. Running transcription on Iris iGPU...")
        result = await backend.transcribe(temp_audio_path, language="en")
        logger.info(f"   Result: {result}")

        # Cleanup
        backend.unload_model()
        import os
        os.unlink(temp_audio_path)

        logger.info("\n✓ Whisper inference on Iris iGPU completed successfully!")
        return True

    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_whisper_on_iris())
    sys.exit(0 if success else 1)
