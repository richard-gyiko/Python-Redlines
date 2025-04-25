import subprocess
import tempfile
import os
import logging
from pathlib import Path
from typing import Union, Tuple, Optional
from shutil import copytree

from . import BIN_DIR

logger = logging.getLogger(__name__)


class XmlPowerToolsEngine(object):
    def __init__(self, target_path: Optional[Path] = None):
        """
        Initialize the engine using the pre-installed .NET binary for the current platform.
        """
        target_dir = BIN_DIR

        if target_path is not None:
            # Copy every binary to the target path
            target_path = Path(target_path)
            if not target_path.exists():
                target_path.mkdir(parents=True, exist_ok=True)
            if not target_path.is_dir():
                raise ValueError(f"Target path {target_path} is not a directory.")

            copytree(BIN_DIR, target_path, dirs_exist_ok=True)
            target_dir = target_path

        if os.name == "nt":  # Windows
            self.binary_path = target_dir / "redlines.exe"
        else:  # Linux/macOS
            self.binary_path = target_dir / "redlines"
             # Ensure the binary is executable
            os.chmod(self.binary_path, 0o755)

        

    def run_redline(
        self,
        author_tag: str,
        original: Union[bytes, Path],
        modified: Union[bytes, Path],
    ) -> Tuple[bytes, Optional[str], Optional[str]]:
        """
        Runs the redlines binary. The 'original' and 'modified' arguments can be either bytes or file paths.
        Returns the redline output as bytes.
        """
        temp_files = []
        try:
            target_path = tempfile.NamedTemporaryFile(delete=False).name
            original_path = (
                self._write_to_temp_file(original)
                if isinstance(original, bytes)
                else original
            )
            modified_path = (
                self._write_to_temp_file(modified)
                if isinstance(modified, bytes)
                else modified
            )
            temp_files.extend([target_path, original_path, modified_path])

            command = [
                str(self.binary_path),
                author_tag,
                str(original_path),
                str(modified_path),
                target_path,
            ]

            # Capture stdout and stderr
            result = subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            stdout_output = (
                result.stdout if result.stdout and len(result.stdout) > 0 else None
            )
            stderr_output = (
                result.stderr if result.stderr and len(result.stderr) > 0 else None
            )

            redline_output = Path(target_path).read_bytes()

            return redline_output, stdout_output, stderr_output

        finally:
            self._cleanup_temp_files(temp_files)

    def _cleanup_temp_files(self, temp_files):
        for file_path in temp_files:
            try:
                os.remove(file_path)
            except OSError as e:
                logger.warning(f"Error deleting temp file {file_path}: {e}")

    def _write_to_temp_file(self, data):
        """
        Writes bytes data to a temporary file and returns the file path.
        """
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(data)
        temp_file.close()
        return temp_file.name
