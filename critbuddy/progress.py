"""Progress monitoring utilities for Monte Carlo simulations.

Provides progress bar display and monitoring for both OpenMC and MCNP solvers.
"""

import re
import threading
import time
import logging
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger(__name__)


# =============================================================================
# PROGRESS BAR DISPLAY
# =============================================================================

def display_progress_bar(
    current: int,
    total: int,
    prefix: str = "",
    bar_width: int = 30,
) -> None:
    """
    Display a progress bar to console.

    Args:
        current: Current progress value
        total: Total expected value
        prefix: Optional prefix text
        bar_width: Width of the progress bar in characters
    """
    if total == 0:
        return

    progress = min(1.0, current / total)
    filled = int(bar_width * progress)
    bar = "█" * filled + "░" * (bar_width - filled)

    line = f"\r{prefix}|{bar}| {progress*100:5.1f}% ({current:3d}/{total})"
    print(line, end='', flush=True)


def clear_progress_bar(width: int = 80) -> None:
    """Clear the progress bar line."""
    print(f"\r{' ' * width}\r", end='', flush=True)


# =============================================================================
# MCNP PROGRESS MONITORING
# =============================================================================

def extract_mcnp_total_cycles(input_file: Path) -> int:
    """
    Extract total cycles from MCNP input file kcode line.

    Args:
        input_file: Path to MCNP input file

    Returns:
        Total number of cycles, or 1000 as fallback
    """
    try:
        content = input_file.read_text(errors='ignore')

        # kcode line format: kcode nps keff skip total
        match = re.search(r'kcode\s+(\d+)\s+([\d.]+)\s+(\d+)\s+(\d+)', content, re.IGNORECASE)
        if match:
            return int(match.group(4))

        logger.debug(f"Could not find kcode line in {input_file}")
        return 1000

    except Exception as e:
        logger.debug(f"Failed to parse kcode from {input_file}: {e}")
        return 1000


def extract_mcnp_current_cycle(output_file: Path) -> int:
    """
    Extract the latest cycle number from MCNP output.

    Args:
        output_file: Path to MCNP output file

    Returns:
        Highest cycle number found, or 0 if none
    """
    try:
        content = output_file.read_text(errors='ignore')

        # Pattern: "estimator cycle NNNN"
        matches = re.findall(r'estimator\s+cycle\s+(\d+)', content, re.IGNORECASE)
        if matches:
            return max(int(cycle) for cycle in matches)

        return 0

    except Exception as e:
        logger.debug(f"Error extracting cycle from {output_file}: {e}")
        return 0


class MCNPProgressMonitor:
    """
    Monitor MCNP execution progress by tracking cycle completion.

    Uses a background thread to periodically check the output file for
    cycle progress and reports updates via callback or console.

    Example:
        monitor = MCNPProgressMonitor(input_file, output_file)
        monitor.start()
        # ... run MCNP ...
        monitor.stop()
    """

    def __init__(
        self,
        input_file: Path,
        output_file: Path,
        callback: Optional[Callable[[int, int], None]] = None,
        poll_interval: float = 2.0,
    ):
        """
        Initialize progress monitor.

        Args:
            input_file: Path to MCNP input file (for total cycles)
            output_file: Path to MCNP output file (for progress)
            callback: Optional callback(current_cycle, total_cycles) for updates
            poll_interval: Seconds between progress checks
        """
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.callback = callback
        self.poll_interval = poll_interval

        self.total_cycles = extract_mcnp_total_cycles(self.input_file)
        self.current_cycle = 0
        self._monitoring = False
        self._thread: Optional[threading.Thread] = None
        self._last_file_size = 0

    def start(self) -> None:
        """Start monitoring in background thread."""
        if self._monitoring:
            return

        self._monitoring = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

        logger.debug(f"Started monitoring {self.output_file} (expecting {self.total_cycles} cycles)")

    def stop(self) -> None:
        """Stop monitoring and clean up."""
        if not self._monitoring:
            return

        self._monitoring = False
        if self._thread:
            self._thread.join(timeout=2)

        # Clear progress line if using console display
        if self.callback is None:
            clear_progress_bar()

    def _monitor_loop(self) -> None:
        """Main monitoring loop running in background thread."""
        while self._monitoring:
            try:
                if self.output_file.exists():
                    file_size = self.output_file.stat().st_size

                    # Only read if file has grown significantly
                    if file_size > self._last_file_size + 1000:
                        cycle = extract_mcnp_current_cycle(self.output_file)

                        if cycle > self.current_cycle:
                            self.current_cycle = cycle
                            self._report_progress()

                        self._last_file_size = file_size

                time.sleep(self.poll_interval)

            except Exception as e:
                logger.debug(f"Monitor error: {e}")
                time.sleep(self.poll_interval)

    def _report_progress(self) -> None:
        """Report current progress via callback or console."""
        if self.callback:
            self.callback(self.current_cycle, self.total_cycles)
        else:
            display_progress_bar(self.current_cycle, self.total_cycles, prefix="  ")

    @property
    def progress_fraction(self) -> float:
        """Current progress as fraction from 0.0 to 1.0."""
        if self.total_cycles == 0:
            return 0.0
        return min(1.0, self.current_cycle / self.total_cycles)


# =============================================================================
# OPENMC PROGRESS MONITORING
# =============================================================================

class OpenMCProgressMonitor:
    """
    Monitor OpenMC execution progress by parsing stdout.

    Tracks batch completion from OpenMC k-eigenvalue output lines like:
        "       44/1    0.35958    0.37745 +/- 0.00237"

    The format is: batch/generation, k-eff, running average k-eff

    Example:
        monitor = OpenMCProgressMonitor(total_batches=150)
        for line in process.stdout:
            monitor.process_line(line)
    """

    def __init__(
        self,
        total_batches: int,
        callback: Optional[Callable[[int, int], None]] = None,
    ):
        """
        Initialize OpenMC progress monitor.

        Args:
            total_batches: Total number of batches expected
            callback: Optional callback(current_batch, total_batches) for updates
        """
        self.total_batches = total_batches
        self.callback = callback
        self.current_batch = 0

        # Pattern for OpenMC k-eigenvalue output: "   N/1    k-eff"
        # Matches lines like "       44/1    0.35958"
        self._pattern_batch = re.compile(r'^\s+(\d+)/\d+\s+[\d.]+')

    def process_line(self, line: str) -> None:
        """
        Process a line of OpenMC output and update progress.

        Args:
            line: A line from OpenMC stdout
        """
        # Try to match batch output line "   N/1    k-eff"
        match = self._pattern_batch.match(line)
        if match:
            batch = int(match.group(1))
            self._update_batch(batch)
            return

    def _update_batch(self, batch: int) -> None:
        """Update current batch and report progress."""
        if batch > self.current_batch:
            self.current_batch = batch
            self._report_progress()

    def _report_progress(self) -> None:
        """Report current progress via callback or console."""
        if self.callback:
            self.callback(self.current_batch, self.total_batches)
        else:
            display_progress_bar(self.current_batch, self.total_batches, prefix="  ")

    def finish(self) -> None:
        """Clean up after monitoring (clear progress bar)."""
        if self.callback is None:
            clear_progress_bar()

    @property
    def progress_fraction(self) -> float:
        """Current progress as fraction from 0.0 to 1.0."""
        if self.total_batches == 0:
            return 0.0
        return min(1.0, self.current_batch / self.total_batches)
