import os
import time
from abc import ABC, abstractmethod
from typing import Any

import psutil
from pydantic import BaseModel

from .models import PipelineConfig


class PerformanceMetrics(BaseModel):
    """Metrics captured during an operation."""

    operation: str
    start_time: float | None = None
    end_time: float | None = None
    duration_ms: float | None = None
    peak_memory_mb: float | None = None
    cpu_percent: float | None = None


class BasePerformanceMonitor(ABC):
    """Abstract base class for performance monitoring context managers."""

    def __init__(self, operation_name: str, config: PipelineConfig):
        self.operation_name = operation_name
        self.config = config
        self.metrics = PerformanceMetrics(operation=operation_name)

    def __enter__(self) -> "BasePerformanceMonitor":  # noqa: PYI034
        self._capture_start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,  # noqa: PYI036
    ) -> None:
        self._capture_end()

    @abstractmethod
    def _capture_start(self) -> None:
        """Logic to execute at the start of the block."""

    @abstractmethod
    def _capture_end(self) -> None:
        """Logic to execute at the end of the block."""

    @abstractmethod
    def report(self) -> PerformanceMetrics:
        """Return the captured metrics."""


class DefaultPerformanceMonitor(BasePerformanceMonitor):
    """Default monitor that captures time, memory, and CPU usage using psutil."""

    def __init__(self, operation_name: str, config: PipelineConfig):
        super().__init__(operation_name, config)
        self._process = psutil.Process(os.getpid()) if config.perf_capture_resources else None

    def _capture_start(self) -> None:
        if self.config.perf_capture_timing:
            self.metrics.start_time = time.perf_counter()

        if self.config.perf_capture_resources and self._process:
            # Call cpu_percent to initialize the baseline for this process
            self._process.cpu_percent(interval=None)

    def _capture_end(self) -> None:
        if self.config.perf_capture_timing and self.metrics.start_time is not None:
            self.metrics.end_time = time.perf_counter()
            self.metrics.duration_ms = (self.metrics.end_time - self.metrics.start_time) * 1000

        if self.config.perf_capture_resources and self._process:
            self.metrics.cpu_percent = self._process.cpu_percent(interval=None)
            mem_info = self._process.memory_info()
            self.metrics.peak_memory_mb = mem_info.rss / (1024 * 1024)

    def report(self) -> PerformanceMetrics:
        return self.metrics


class NullPerformanceMonitor(BasePerformanceMonitor):
    """No-op monitor used when monitoring is disabled."""

    def _capture_start(self) -> None:
        pass

    def _capture_end(self) -> None:
        pass

    def report(self) -> PerformanceMetrics:
        return self.metrics


def monitor_operation(config: PipelineConfig, operation_name: str) -> BasePerformanceMonitor:
    """Factory function to create the appropriate performance monitor context manager."""
    if not config.enable_perf_monitoring:
        return NullPerformanceMonitor(operation_name, config)
    return DefaultPerformanceMonitor(operation_name, config)
