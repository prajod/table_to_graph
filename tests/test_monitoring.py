import time

from table_to_graph.models import PipelineConfig
from table_to_graph.monitoring import monitor_operation


def test_null_monitor(default_config):
    # Disabled by default
    assert not default_config.enable_perf_monitoring

    with monitor_operation(default_config, "test_null") as monitor:
        time.sleep(0.01)

    metrics = monitor.report()
    assert metrics.operation == "test_null"
    assert metrics.duration_ms is None
    assert metrics.peak_memory_mb is None


def test_default_monitor_timing_only():
    config = PipelineConfig(enable_perf_monitoring=True, perf_capture_resources=False)

    with monitor_operation(config, "test_timing") as monitor:
        time.sleep(0.05)

    metrics = monitor.report()
    assert metrics.operation == "test_timing"
    assert metrics.duration_ms is not None
    assert metrics.duration_ms >= 50  # Should be at least 50ms
    assert metrics.peak_memory_mb is None


def test_default_monitor_full():
    config = PipelineConfig(enable_perf_monitoring=True)

    with monitor_operation(config, "test_full") as monitor:
        time.sleep(0.01)
        # Allocate some memory to ensure resource capture works
        _ = [i for i in range(100000)]

    metrics = monitor.report()
    assert metrics.operation == "test_full"
    assert metrics.duration_ms is not None
    assert metrics.peak_memory_mb is not None
    assert metrics.cpu_percent is not None
