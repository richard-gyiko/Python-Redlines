import platform
from pathlib import Path

def get_platform_folder():
    """Determine the correct platform folder for the .NET binaries"""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "linux":
        base = "linux"
    elif system == "darwin":
        base = "osx"
    elif system == "windows":
        base = "win"
    else:
        raise RuntimeError(f"Unsupported platform: {system}")
                                                                                                                                
    if machine in ("x86_64", "amd64"):
        arch = "x64"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        raise RuntimeError(f"Unsupported architecture: {machine}")
                                                                                                                                
    return f"{base}-{arch}"
                                                                                                                                
# Path to the .NET binaries
PLATFORM = get_platform_folder()
BIN_DIR = Path(__file__).parent / "bin" / PLATFORM

# Ensure the binary directory exists
if not BIN_DIR.exists():
    raise ImportError(
        f"Binary directory not found: {BIN_DIR}. "
        f"This package may not be compatible with your platform ({PLATFORM})."
    )  