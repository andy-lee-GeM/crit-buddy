"""
MCNP execution module for crit-buddy.

Provides a clean interface for running MCNP simulations with:
- Configurable parallel tasks (MCNP `tasks N` flag)
- Timeout handling
- Progress monitoring
- Structured result object
"""

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from critbuddy.progress import MCNPProgressMonitor


def _get_mcnp_executable():
    """Get MCNP executable from environment variable (checked at runtime)."""
    return os.getenv("MCNP_EXECUTABLE")


@dataclass
class MCNPExecutionResult:
    """Result of an MCNP execution."""

    success: bool
    return_code: int
    execution_time: float
    output_file: Optional[Path] = None
    error_message: Optional[str] = None
    stdout: str = ""
    stderr: str = ""


class MCNPExecutor:
    """
    Executes MCNP simulations with consistent configuration.

    Features:
    - Parallel task support via `tasks N` flag
    - Timeout handling
    - Clean working directory management

    Example:
        executor = MCNPExecutor(tasks=4, timeout=3600)
        result = executor.run(input_file, working_dir)
        if result.success:
            # parse result.output_file
    """

    def __init__(
        self,
        executable: str = None,
        tasks: int = 4,
        timeout: int = 3600,
        show_progress: bool = True,
    ):
        """
        Initialize executor with configuration.

        Args:
            executable: Path to MCNP executable (default: from MCNP_EXECUTABLE env var)
            tasks: Number of parallel tasks for MCNP
            timeout: Execution timeout in seconds
            show_progress: Whether to display progress bar during execution
        """
        self.executable = executable or _get_mcnp_executable()
        self.tasks = tasks
        self.timeout = timeout
        self.show_progress = show_progress

    def is_available(self) -> bool:
        """Check if MCNP executable exists and is accessible."""
        if self.executable is None:
            return False
        return Path(self.executable).exists()

    def run(
        self,
        input_file: Path,
        working_dir: Path,
        output_name: Optional[str] = None,
    ) -> MCNPExecutionResult:
        """
        Run MCNP simulation.

        Args:
            input_file: Path to MCNP input file (relative to working_dir)
            working_dir: Directory to run MCNP from
            output_name: Name for output file (default: input filename + 'o')

        Returns:
            MCNPExecutionResult with execution status and output path
        """
        working_dir = Path(working_dir)
        input_file = Path(input_file)
        input_name = input_file.name

        # Default output name is input name + 'o'
        if output_name is None:
            output_name = f"{input_name}o"

        output_path = working_dir / output_name
        input_path = working_dir / input_name

        # Build command with tasks flag
        cmd = [
            self.executable,
            f"i={input_name}",
            f"o={output_name}",
            "tasks",
            str(self.tasks),
        ]

        start_time = time.time()
        monitor = None

        try:
            # Setup progress monitoring
            if self.show_progress and input_path.exists():
                monitor = MCNPProgressMonitor(
                    input_file=input_path,
                    output_file=output_path,
                )
                monitor.start()

            # Run MCNP with Popen for non-blocking execution
            process = subprocess.Popen(
                cmd,
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
                return_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                if monitor:
                    monitor.stop()
                return MCNPExecutionResult(
                    success=False,
                    return_code=-1,
                    execution_time=self.timeout,
                    error_message=f"MCNP timeout after {self.timeout}s",
                )

            # Stop progress monitor
            if monitor:
                monitor.stop()

            execution_time = time.time() - start_time

            # Check result
            if return_code == 0:
                return MCNPExecutionResult(
                    success=True,
                    return_code=return_code,
                    execution_time=execution_time,
                    output_file=output_path if output_path.exists() else None,
                    stdout=stdout,
                    stderr=stderr,
                )
            else:
                return MCNPExecutionResult(
                    success=False,
                    return_code=return_code,
                    execution_time=execution_time,
                    output_file=output_path if output_path.exists() else None,
                    error_message=f"MCNP exited with code {return_code}",
                    stdout=stdout,
                    stderr=stderr,
                )

        except FileNotFoundError:
            if monitor:
                monitor.stop()
            return MCNPExecutionResult(
                success=False,
                return_code=-1,
                execution_time=0,
                error_message=f"MCNP executable not found: {self.executable}",
            )

        except Exception as e:
            if monitor:
                monitor.stop()
            return MCNPExecutionResult(
                success=False,
                return_code=-1,
                execution_time=time.time() - start_time,
                error_message=str(e),
            )
