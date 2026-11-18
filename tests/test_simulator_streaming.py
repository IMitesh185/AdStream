import tracemalloc
from pathlib import Path

from adstream.ingestion.quarantine import QuarantineSink
from adstream.ingestion.validator import IngestionValidator
from adstream.observability.logs import StructuredLogStore, configure_python_logger
from adstream.simulator.generator import AdStreamSimulator, SimulatorConfig


def test_simulator_streaming_is_deterministic_and_o1_memory(tmp_path: Path) -> None:
    sim_a = AdStreamSimulator(SimulatorConfig(seed=42, num_advertisers=10, campaigns_per_advertiser=2))
    sim_b = AdStreamSimulator(SimulatorConfig(seed=42, num_advertisers=10, campaigns_per_advertiser=2))

    stream_a = list(sim_a.stream_raw_events(500))
    stream_b = list(sim_b.stream_raw_events(500))
    assert stream_a == stream_b

    validator = IngestionValidator(quarantine=QuarantineSink(tmp_path / "quarantine.jsonl"))
    res = validator.validate_stream(stream_a)
    assert len(res.accepted) + len(res.quarantined) == 500
    assert len(res.accepted) > 400
    assert len(res.quarantined) > 0

    tracemalloc.start()
    count = 0
    for _ in AdStreamSimulator(SimulatorConfig(seed=7)).stream_raw_events(25_000):
        count += 1
    current_bytes, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert count == 25_000
    assert peak_bytes < 5 * 1024 * 1024  # Generator streaming stays well under 5 MB peak
    assert current_bytes < 5 * 1024 * 1024


def test_structured_logger_persists_jsonl(tmp_path: Path) -> None:
    log_path = tmp_path / "adstream.log"
    store = StructuredLogStore(log_path=log_path)
    logger = configure_python_logger(store)
    logger.info("Validated batch of %d events", 500)

    entries = store.tail(level="INFO", limit=5)
    assert len(entries) == 1
    assert entries[0]["message"] == "Validated batch of 500 events"
    assert log_path.exists()
