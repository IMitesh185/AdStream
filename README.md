# AdStream — AdTech Data & Correctness Infrastructure (Stage A: Days 1–10)

AdStream is a platform-agnostic advertising data infrastructure platform built progressively from first principles.  
The project treats **financial and state correctness** as non-negotiable: binary floating-point money drift, dropped malformed payloads, `bool`-as-`int` validation bugs, and unbounded memory buffers are eliminated at the foundation before introducing databases, APIs, Kafka, or Spark.

> **Current Milestone:** **Stage A (Days 1–10) Complete** — Core Python foundations, integer-micros domain contracts, typed exceptions, JSONL quarantine boundary, structured logging, 6 ecosystem payload adapters, and an `O(1)`-memory relationally coherent streaming event simulator.

---

## Core Engineering Decisions (Days 1–10)

1. **Integer Micros (`$1.00 = 1,000,000`) Everywhere:** All budgets, bids, CPM/CPC/CPA math, and publisher revenue-share splits (`basis points`) use Python `StrictInt` / integer micros (`src/adstream/domain/metrics.py`) rather than IEEE-754 `float`, preventing `0.1 + 0.2 != 0.3` drift across millions of aggregations.
2. **Fail-Closed Validation + Quarantine (Never Silent Drops):** Malformed payloads, `bool` masquerading as `int` (`isinstance(True, int) == True`), and breaking schema versions (`schema_version=99`) are routed to `QuarantineSink` (`data/quarantine/*.jsonl`) with `reason_code` + original `raw_payload` preserved (`src/adstream/ingestion/quarantine.py`).
3. **Composition Over Deep Inheritance for Multi-Ecosystem Ingestion:** A lightweight `SourceAdapter` `Protocol` and `AdapterRegistry` normalize Google Ads, YouTube Ads, Amazon Ads, Meta Ads, Retail Media, and Programmatic RTB payloads into 10 canonical Pydantic v2 event contracts (`src/adstream/adapters/`).
4. **Backward-Compatible Schema Evolution (`v1` / `v2`):** Additive fields (`creative_format`, `trace_id`) are accepted seamlessly while unsupported schema versions fail closed into quarantine.
5. **Bounded `O(1)`-Memory Streaming Simulation:** The seeded generator (`src/adstream/simulator/generator.py`) yields relationally coherent `impression -> video -> click -> conversion` chains lazily with injected skew (70% traffic in top 20% advertisers/publishers), duplicate retries, late arrivals, fraud bursts, and malformed payloads.

---

## Verified Local Measurements (Python 3.14.10, Windows)

| Experiment / Suite | Verified Result | Source |
| :--- | :--- | :--- |
| Automated test suite (`python -m pytest -v`) | **8 passed in 3.80s** | [`tests/`](./tests) |
| Deduplication lookup (`1,000` probes in `100,000` IDs) | `list`: `3.014812s` vs `set`: `0.000498s` (**`6,051.4x` faster**) | [`foundations/day03_dedup_benchmark.py`](./foundations/day03_dedup_benchmark.py) |
| Streaming generator (`100,000` coherent raw events) | **`14,391 events/s`** (`6.949s`) at **`434.7 KB`** peak `tracemalloc` memory | [`src/adstream/simulator/generator.py`](./src/adstream/simulator/generator.py) |

---

## Repository Layout (Days 1–10)

```text
AdStream/
├── AboutAdStream.md                      # Platform specification & FinOps charter
├── AdStream-Complete-Curriculum.md       # 64-day engineering roadmap (Stages A-L)
├── pyproject.toml                        # Package metadata, pytest & strict mypy config
├── foundations/                          # Days 1-3 progressive Python exercises
│   ├── day01_campaign_basics.py          # Integer-micros CTR/CPC/CPM & budget math
│   ├── day02_budget_loop.py              # Fail-closed 20-event budget exhaustion loop
│   └── day03_dedup_benchmark.py          # Set vs list O(1) dedup benchmark (100K IDs)
├── src/adstream/
│   ├── domain/                           # Metrics, typed exceptions, strict Pydantic models
│   ├── ingestion/                        # IngestionValidator + JSONL QuarantineSink
│   ├── observability/                    # Structured JSONL logger (StructuredLogStore)
│   ├── adapters/                         # SourceAdapter protocol + 6 ecosystem adapters
│   └── simulator/                        # Seeded O(1)-memory coherent event stream
└── tests/                                # Domain, adapter/quarantine, and streaming tests
```

---

## Run Locally

```powershell
# Install package + dev dependencies in editable mode
pip install -e ".[dev]"

# Run the test suite
python -m pytest -v

# Run the Day 3 deduplication benchmark
python foundations/day03_dedup_benchmark.py
```

---

## Next Up (Stage B — Days 13–20)
* PostgreSQL 16 relational ledger schema (`BIGINT` micros, `CHECK` invariants, `UNIQUE (idempotency_key)`).
* Reproducing concurrent budget overspend under Read Committed vs fixing it with conditional atomic `UPDATE` and `SELECT ... FOR UPDATE`.
