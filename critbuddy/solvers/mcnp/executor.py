"""
MCNP execution module for crit-buddy.

Provides a clean interface for running MCNP simulations with:
- Configurable parallel tasks (MCNP `tasks N` flag)
- Timeout handling
- Structured result object
"""

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

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
    ):
        """
        Initialize executor with configuration.

        Args:
            executable: Path to MCNP executable (default: from MCNP_EXECUTABLE env var)
            tasks: Number of parallel tasks for MCNP
            timeout: Execution timeout in seconds
        """
        self.executable = executable or _get_mcnp_executable()
        self.tasks = tasks
        self.timeout = timeout

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

        # Build command with tasks flag
        cmd = [
            self.executable,
            f"i={input_name}",
            f"o={output_name}",
            "tasks",
            str(self.tasks),
        ]

        start_time = time.time()

        try:
            # Run MCNP
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            execution_time = time.time() - start_time

            # Check result
            if result.returncode == 0:
                return MCNPExecutionResult(
                    success=True,
                    return_code=result.returncode,
                    execution_time=execution_time,
                    output_file=output_path if output_path.exists() else None,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )
            else:
                return MCNPExecutionResult(
                    success=False,
                    return_code=result.returncode,
                    execution_time=execution_time,
                    output_file=output_path if output_path.exists() else None,
                    error_message=f"MCNP exited with code {result.returncode}",
                    stdout=result.stdout,
                    stderr=result.stderr,
                )

        except subprocess.TimeoutExpired:
            return MCNPExecutionResult(
                success=False,
                return_code=-1,
                execution_time=self.timeout,
                error_message=f"MCNP timeout after {self.timeout}s",
            )

        except FileNotFoundError:
            return MCNPExecutionResult(
                success=False,
                return_code=-1,
                execution_time=0,
                error_message=f"MCNP executable not found: {self.executable}",
            )

        except Exception as e:
            return MCNPExecutionResult(
                success=False,
                return_code=-1,
                execution_time=time.time() - start_time,
                error_message=str(e),
            )
