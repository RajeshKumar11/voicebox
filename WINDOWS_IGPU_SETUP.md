# Windows Intel Iris iGPU Setup Guide

This guide enables DirectML GPU acceleration for Voicebox on Windows systems with Intel Iris integrated graphics (iGPU).

## Supported Hardware

- **Intel 12th-14th Gen (Alder Lake, Raptor Lake)**: i5/i7/i9 with Iris Xe Graphics
- **Intel Arc Mobile GPUs**: Arc A-series (A380, A770M, etc.)
- **AMD Integrated GPUs**: Radeon Graphics (RDNA, Vega)
- **Older Intel iGPU**: UHD Graphics 630+ on Windows 10/11

## System Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 10 Build 1909+ or Windows 11 |
| **Python** | 3.12+ |
| **GPU Driver** | Intel Arc/Iris drivers (latest recommended) or standard Windows iGPU driver |
| **VRAM** | 4GB+ system RAM (iGPU shares system memory) |
| **Torch** | PyTorch 2.2+ with cu128 CUDA libraries |

### Check Your GPU

**Option 1: Device Manager**
1. Right-click "This PC" → Properties
2. Device Manager → Display adapters
3. Look for "Intel Iris Xe Graphics" or "Intel UHD Graphics"

**Option 2: PowerShell**
```powershell
Get-WmiObject Win32_VideoController | Select Name, VideoProcessor, AdapterRAM
```

**Option 3: Python**
```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")

try:
    import torch_directml
    print(f"DirectML devices: {torch_directml.device_count()}")
except ImportError:
    print("torch_directml not installed")
```

## Installation Steps

### 1. Install / Update GPU Driver

**For Intel Iris/UHD (Integrated):**
- Update via Windows Update (automatic for most systems)
- Or manually: https://www.intel.com/content/www/us/en/support/intel-arc-iris-xe-graphics.html

**For Intel Arc (Discrete):**
- https://www.intel.com/content/www/us/en/support/intel-arc-iris-xe-graphics.html
- Ensure Intel Arc Graphics Control Panel is installed

### 2. Set Environment Variables (Optional but Recommended)

Open PowerShell and run:

```powershell
# Enable DirectML debugging (optional)
[Environment]::SetEnvironmentVariable("DIRECTML_DEBUG", "0", [EnvironmentVariableTarget]::User)

# Disable offline mode for HuggingFace (allows model downloads)
[Environment]::SetEnvironmentVariable("HF_HUB_OFFLINE", "0", [EnvironmentVariableTarget]::User)

# Disable CUDA fallback (force DirectML on Windows)
[Environment]::SetEnvironmentVariable("CUDA_VISIBLE_DEVICES", "", [EnvironmentVariableTarget]::User)
```

Then restart your terminal or Python IDE.

### 3. Install Voicebox with DirectML Support

```bash
# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install from voicebox directory
cd backend
pip install -r requirements.txt
```

This installs:
- `torch>=2.2.0` (with cu128 CUDA libraries)
- `torch-directml>=1.13.0` (Windows GPU acceleration)
- All other dependencies (transformers, qwen-tts, whisper, etc.)

### 4. Verify Installation

```python
import torch
import torch_directml
from backend.backends.base import get_torch_device

# Check device
device = get_torch_device(allow_directml=True)
print(f"Device: {device}")

# Check DirectML
print(f"DirectML devices: {torch_directml.device_count()}")

# Test tensor operation
x = torch.randn(100, 100, device=device)
y = torch.randn(100, 100, device=device)
z = torch.mm(x, y)
print(f"Tensor operation OK: {z.shape}")
```

Expected output:
```
Device: cuda:0  # <- This is actually DirectML (torch_directml wraps as CUDA-compatible)
DirectML devices: 1
Tensor operation OK: torch.Size([100, 100])
```

## Running Tests

### Quick Verification

```bash
# Test DirectML device detection
pytest backend/tests/test_directml_iris.py::TestDirectMLDetection -v -s

# Test tensor operations
pytest backend/tests/test_directml_iris.py::TestDirectMLTorchTensor -v -s
```

### Full Test Suite (includes model loading)

```bash
# Test Whisper on DirectML (may download 1.5GB model)
pytest backend/tests/test_directml_iris.py::TestWhisperOnDirectML -v -s

# Test Qwen TTS on DirectML (may download 3GB model)
pytest backend/tests/test_directml_iris.py::TestQwenTTSOnDirectML -v -s
```

## Troubleshooting

### Issue: "torch_directml not found"

**Solution:** Install explicitly
```bash
pip install torch-directml>=1.13.0
```

Then verify:
```python
import torch_directml
print(torch_directml.device_count())  # Should be > 0
```

### Issue: "DirectML device_count() returns 0"

**Causes:**
1. GPU driver outdated → Update from Intel/OEM
2. Iris GPU disabled in BIOS → Enable in System Settings > Advanced > GPU
3. Wrong Python/torch version → Use Python 3.12+, torch 2.2+
4. Compatibility issue with specific iGPU model

**Solution:**
```bash
# Force CPU for now (models still run, just slower)
set VOICEBOX_DEVICE=cpu
python -m backend.main
```

### Issue: "Models load but inference is slow"

**Causes:**
1. DirectML overhead on first inference (expected ~2-5 sec warmup)
2. Iris iGPU has lower bandwidth than discrete GPU
3. Model is too large for available VRAM
4. DirectML not properly detecting GPU capabilities

**Solutions:**
- Use smaller model: `0.6B` instead of `1.7B` for Qwen TTS
- Use faster models: LuxTTS, Kokoro instead of Qwen
- Check available VRAM: `wmi.WMI().Win32_VideoController()[0].AdapterRAM`
- Profile: Add `torch.cuda.reset_peak_memory_stats()` before/after inference

### Issue: "CUDA out of memory" with DirectML

**Solution:** Clear cache and reduce batch size
```python
import torch
torch.cuda.empty_cache()  # Works with DirectML too

# Or reduce model size
await backend.load_model_async("0.6B")  # Instead of 1.7B
```

### Issue: "wmi module import fails"

**Solution:** Install pywin32
```bash
pip install pywin32
pywin32_postinstall -install
```

This enables optional Iris GPU detection logging. Not required for DirectML to work.

## Performance Expectations

### Iris Xe (i5/i7 12th+ gen)

| Model | Hardware | Device | Time/inference |
|-------|----------|--------|-----------------|
| Qwen TTS 1.7B | i7-12700H | DirectML (Iris) | ~8-12 sec (first), ~6-8 sec (cached) |
| Qwen TTS 0.6B | i7-12700H | DirectML (Iris) | ~3-5 sec (first), ~2-3 sec (cached) |
| Whisper Base | i7-12700H | DirectML (Iris) | ~4-6 sec |
| LuxTTS | i7-12700H | DirectML (Iris) | ~1-2 sec (lightweight) |

**Note:** Iris iGPU is slower than NVIDIA RTX but faster than CPU-only. Performance varies by:
- System thermal state (throttling)
- Available system RAM (iGPU shares memory)
- Other apps consuming GPU resources
- Model complexity and batch size

## Advanced Configuration

### Use Multiple GPU Devices

If you have discrete + integrated GPU:

```python
from backend.backends.pytorch_backend import PyTorchTTSBackend

# Force specific device
backend = PyTorchTTSBackend("1.7B")
backend.device = "cuda:1"  # Use second GPU if available
await backend.load_model_async("1.7B")
```

### Disable DirectML (Force CPU)

```python
from backend.backends.base import get_torch_device

# Skip DirectML check
device = get_torch_device(allow_directml=False)  # Returns CPU
```

### Profile GPU Memory Usage

```python
import torch

# For DirectML
try:
    memory_allocated = torch.cuda.memory_allocated()
    memory_reserved = torch.cuda.memory_reserved()
    print(f"Allocated: {memory_allocated / 1e6:.1f} MB")
    print(f"Reserved: {memory_reserved / 1e6:.1f} MB")
except:
    print("Memory profiling not available for this device")
```

## Reporting Issues

If DirectML isn't working, collect this info:

```powershell
python -c "
import platform, torch, sys
try:
    import torch_directml
    directml_ok = True
    device_count = torch_directml.device_count()
except:
    directml_ok = False
    device_count = 0

print(f'OS: {platform.system()} {platform.release()}')
print(f'Python: {sys.version}')
print(f'PyTorch: {torch.__version__}')
print(f'DirectML: {directml_ok} (devices: {device_count})')
print(f'CUDA: {torch.cuda.is_available()}')

import wmi
for gpu in wmi.WMI().Win32_VideoController():
    print(f'GPU: {gpu.Name} ({gpu.DriverVersion})')
"
```

Then open an issue on GitHub with this output.

## References

- **PyTorch DirectML**: https://learn.microsoft.com/en-us/windows/ai/directml/pytorch-support
- **Intel Iris Xe Drivers**: https://www.intel.com/content/www/us/en/support/intel-arc-iris-xe-graphics.html
- **DirectML Documentation**: https://learn.microsoft.com/en-us/windows/ai/directml/
- **torch_directml PyPI**: https://pypi.org/project/torch-directml/
