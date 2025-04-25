import os
import subprocess
import platform
from pathlib import Path
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


def get_platform():
    """Get the current platform identifier for .NET runtime"""
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


class HatchRunBuildHook(BuildHookInterface):
    PLUGIN_NAME = "hatch-run-build"

    def initialize(self, version, build_data):
        """Hatch build hook to compile .NET binaries"""
        # Get the platform we're building for
        platform_env = os.environ.get("PYTHON_REDLINES_PLATFORM", "auto")

        # Handle special "auto" value for cibuildwheel
        if platform_env == "auto":
            target_platform = get_platform()
        # Handle cibuildwheel template variables
        elif "{arch}" in platform_env:
            system_arch = (
                "arm64" if platform.machine().lower() in ("arm64", "aarch64") else "x64"
            )
            target_platform = platform_env.replace("{arch}", system_arch)
        else:
            target_platform = platform_env

        print(f"Building for platform: {target_platform}")

        # Compile .NET binaries
        out_dir = f"./csproj/bin/Release/net8.0/{target_platform}/publish"
        os.makedirs(os.path.dirname(out_dir), exist_ok=True)

        subprocess.run(
            [
                "dotnet",
                "publish",
                "./csproj/redlines.csproj",
                "-c",
                "Release",
                "-r",
                target_platform,
                "--self-contained",
                "true",
                "-o",
                out_dir,
            ],
            check=True,
        )

        # Use force_include to include the binaries in the wheel
        # This is the correct way to include files in the wheel according to the docs
        bin_dir_rel = f"bin/{target_platform}"

        # Create a mapping from source files to destination paths in the package
        for file in Path(out_dir).glob("*"):
            if file.is_file():
                # Calculate the destination path within the package
                # This will place the file in src/python_redlines/bin/{platform}/
                dest_path = f"src/python_redlines/{bin_dir_rel}/{file.name}"

                # Add to force_include
                build_data["force_include"][str(file)] = dest_path

        # Mark the wheel as not pure Python
        build_data["pure_python"] = False

        # Set the platform tag for the wheel
        if target_platform.startswith("linux"):
            if "arm64" in target_platform:
                build_data["tag"] = "py3-none-manylinux2014_aarch64"
            else:
                build_data["tag"] = "py3-none-manylinux2014_x86_64"
        elif target_platform.startswith("osx"):
            if "arm64" in target_platform:
                build_data["tag"] = "py3-none-macosx_11_0_arm64"
            else:
                build_data["tag"] = "py3-none-macosx_10_14_x86_64"
        elif target_platform.startswith("win"):
            if "arm64" in target_platform:
                build_data["tag"] = "py3-none-win_arm64"
            else:
                build_data["tag"] = "py3-none-win_amd64"

        print(f"Added .NET binaries to force_include for platform: {target_platform}")
        return True
