# AdStream Engineering Kickoff — Complete Curriculum, Cost Strategy & Day 1

> **Repository Check Before Starting:** Inside [`./adstream - dev`](./adstream%20-%20dev), there is currently an early `contracts/` package, `metrics.py`, and tests (see [AboutAdStream.md](./AboutAdStream.md)). Per your instructions, we treat your **implementation learning path as starting from absolute zero**—so you build and understand every layer yourself from scratch rather than inheriting code you haven't written.

---

## Part A — My Understanding

1. **The Project (`AdStream`):** An end-to-end, realistic advertising technology and data infrastructure platform comparable in business concepts to Google Ads, Amazon Ads, and YouTube Ads. It spans advertiser/publisher management, bidding and ad serving, high-throughput event ingestion, fraud detection, concurrent budget control, billing correctness, real-time streaming, lakehouse analytics, observability, and FinOps—progressively scaling toward an architectural target of **5 million events/sec** (clearly separating **measured local throughput**, **projected capacity**, and **architectural target**).
2. **Your Learning Philosophy:** **Business drives engineering; engineering drives learning.** We never teach a framework or abstraction before you hit the concrete business or failure problem that makes it necessary. You will experience manual JSON validation before Pydantic, naive file storage before PostgreSQL, raw sockets/HTTP before FastAPI, single-process limits before Spark/Kafka, and race conditions before locks/idempotency.
3. **Zero-Assumed Implementation & Strict LLM Policy:** Even if you recognize terms, I will assume **zero prior implementation skill**. I will explain concepts, assign deliverables, share <=1-hour verified learning resources, and review your code—**never writing complete solutions for you** unless you explicitly request a reference after attempting it yourself.
4. **Strict Anti-Drift & Azure Free-Tier Discipline:** Every assignment has explicit in-scope/out-of-scope boundaries and a persistent progress ledger. Paid cloud services are forbidden unless verified free within strict consumption limits; local Docker + open-source tools are preferred wherever Azure lacks a permanent free tier.

---

## Part B — AdStream Business Introduction

**What AdStream does:** AdStream is a two-sided marketplace and measurement engine connecting **Advertisers** (who want to show ads and only pay for valid outcomes up to a fixed budget) with **Publishers** (websites, apps, and video platforms that have ad slots to sell) when **End Users** visit pages or watch videos.

**Core Business Participants & Value Loop:**
1. **Advertiser / Agency:** Creates **Campaigns** and **Ads**, sets targeting rules and a **Budget** (e.g., $1,000/day), and specifies how much they will pay per **Impression** (CPM) or **Click** (CPC).
2. **Publisher:** Owns **Websites / Apps / Placements** (inventory) and earns revenue share when valid ads are shown or clicked.
3. **AdStream Platform:**
   * **Decides & Serves:** Evaluates eligible campaigns under remaining budget and returns an ad in milliseconds.
   * **Ingests & Validates Events:** Captures billions of downstream events (**impressions**, **clicks**, **video views**, **conversions**) while rejecting/quarantining malformed payloads and filtering invalid/fraudulent traffic.
   * **Protects Money (Correctness):** Guarantees that concurrent requests never overspend a campaign budget and retried clicks never double-bill an advertiser.
   * **Reports & Reconciles:** Produces real-time operational metrics and historical Bronze/Silver/Gold lakehouse tables for billing, attribution, and ROI analysis.

---

## Part C — Complete Engineering Roadmap (Days 1–64)

> **Pacing note:** Each "Day" is one focused assignment (not a 24-hour clock). Do not skip ahead; you must pass Completion Criteria before advancing.

---

### STAGE A — Python Foundations (Days 1–12)

#### Day 1 — Advertiser & Campaign Entities (Variables, Data Types, Operators)
1. **Business Context:** AdStream must represent an advertiser's first campaign and compute basic spend metrics in memory before any files or APIs exist.
2. **Task — What I Must Do:** Create a Python script (`day01_campaign_basics.py`) storing advertiser ID, campaign name, daily budget in integer currency minor units (micros/cents—explain why vs float), impressions, clicks, and cost; compute CTR, CPC, CPM, and remaining budget; print a formatted summary.
3. **Why Are We Doing This?:** Every downstream billing, ledger, and analytics calculation depends on exact numeric types and avoiding floating-point money drift.
4. **How Should I Approach It? — HINT:** Use `int`, `float`, `str`, `bool`, arithmetic/comparison operators, and `f-strings`. Compare storing `$10.00` as `10.0` vs `10_000_000` micros (`int`). Handle `impressions == 0` or `clicks == 0` explicitly using basic conditions or guarded arithmetic later.
5. **Prerequisite Learning Resources (<=1 hr):** Official Python Tutorial — Ch. 3 *"An Informal Introduction to Python"* (https://docs.python.org/3/tutorial/introduction.html, ~40 mins).
6. **Completion Criteria:** Script runs cleanly with `python`; you can explain `int` vs `float` precision on money, `//` vs `/`, and `str` vs `int`.
7. **Concepts Introduced:** *New:* Variables, `int`, `float`, `str`, `bool`, arithmetic & comparison operators, f-strings, integer money representation. *Reused:* None.

#### Day 2 — Campaign Eligibility & Event Batch Simulation (Conditions & Loops)
1. **Business Context:** Before serving an ad or accepting an event, AdStream must check campaign status, budget thresholds, and process batches of incoming events.
2. **Task — What I Must Do:** Build a script simulating a sequence of 20 ad-event charges against a campaign budget using `if/elif/else`, `for`, and `while` loops—stopping when budget runs out or status is `PAUSED`, and counting served vs rejected events.
3. **Why Are We Doing This?:** Business rules (active status, positive remaining budget, max bid cap) gate every ad auction and billing event.
4. **How Should I Approach It? — HINT:** Combine boolean operators (`and`, `or`, `not`) with `for`/`while`, `break`, and `continue`. Trace edge cases: exact budget depletion (`remaining == 0`) vs insufficient budget (`remaining < charge`).
5. **Prerequisite Learning Resources (<=1 hr):** Official Python Tutorial — Ch. 4.1–4.5 (*`if`, `for`, `range`, `break`, `continue`*) (https://docs.python.org/3/tutorial/controlflow.html, ~45 mins).
6. **Completion Criteria:** Rejected events never drive `remaining_budget < 0`; you can trace loop termination and off-by-one boundaries aloud.
7. **Concepts Introduced:** *New:* `if/elif/else`, truthiness, `for`, `while`, `range()`, `break`, `continue`. *Reused:* Variables, operators, integer money.

#### Day 3 — Indexing Impressions, Publishers & Deduplicating IDs (Lists, Tuples, Sets, Dicts)
1. **Business Context:** Events arrive with duplicate event IDs, ordered impression trails, immutable coordinates, and per-campaign spend totals.
2. **Task — What I Must Do:** Model a batch of raw event records using `list` (ordered log), `tuple` (immutable `(campaign_id, country)` key), `set` (seen `event_id` deduplication), and `dict` (accumulated spend and click counts per campaign).
3. **Why Are We Doing This?:** Choosing the wrong collection turns `O(1)` duplicate detection into `O(n)` scans that collapse under high traffic.
4. **How Should I Approach It? — HINT:** Test membership lookup (`in`) on a `list` vs a `set` for 100,000 IDs and time both with `time.perf_counter()`. Use `dict.get()` for safe counter increments.
5. **Prerequisite Learning Resources (<=1 hr):** Official Python Tutorial — Ch. 5 (*Data Structures*) (https://docs.python.org/3/tutorial/datastructures.html, ~55 mins).
6. **Completion Criteria:** Duplicate IDs are counted once; benchmark clearly shows `set` vs `list` lookup time; you can explain hashability and mutability.
7. **Concepts Introduced:** *New:* `list`, `tuple`, `set`, `dict`, hashability, mutability, basic `O(1)` vs `O(n)` lookup intuition. *Reused:* Loops, conditions.

#### Day 4 — Reusable Validation & Pricing Rules (Functions, Arguments, Return Values & Scope)
1. **Business Context:** Multiple parts of AdStream (ad server, batch loader, billing) need the same fee, budget-check, and CTR logic without duplicating code.
2. **Task — What I Must Do:** Refactor Days 1–3 logic into small single-purpose functions (`calculate_ctr`, `can_afford_charge`, `deduplicate_events`, `aggregate_spend`) with positional/keyword arguments, default parameters, and explicit return values. Demonstrate a global-vs-local scope bug and fix it via pure parameters/returns.
3. **Why Are We Doing This?:** Shared mutable globals cause silent corruption when concurrent handlers run later.
4. **How Should I Approach It? — HINT:** Keep I/O (`print`) out of calculation functions. Avoid mutable default arguments (`def f(x=[])`).
5. **Prerequisite Learning Resources (<=1 hr):** Official Python Tutorial — Ch. 4.7–4.9 (*Defining Functions*) (https://docs.python.org/3/tutorial/controlflow.html#defining-functions, ~45 mins).
6. **Completion Criteria:** Zero global state mutations; you can explain LEGB scope and why mutable default arguments break across calls.
7. **Concepts Introduced:** *New:* `def`, parameters vs arguments, `*args`/`**kwargs`, return values, LEGB scope, pure functions, type hints basics. *Reused:* Collections, loops.

#### Day 5 — Persisting Raw Events & Quarantine Files (File I/O, CSV, JSON)
1. **Business Context:** AdStream receives daily partner dumps as CSV/JSONL files and must separate valid events from malformed ones into a quarantine file.
2. **Task — What I Must Do:** Write a script reading raw `.csv` and `.jsonl` ad-event files, parsing records, writing valid records to `clean_events.jsonl` and invalid records (with error reason + raw line) to `quarantine.jsonl`.
3. **Why Are We Doing This?:** Real ad feeds always contain malformed rows; silently dropping them loses financial auditability, while crashing the job halts the entire batch.
4. **How Should I Approach It? — HINT:** Use `pathlib.Path`, `with open(...)`, `csv.DictReader`, and `json.loads()` / `json.dumps()`. Preserve the original raw line on failure.
5. **Prerequisite Learning Resources (<=1 hr):** Official Python Tutorial — Ch. 7.2 (*Reading and Writing Files*) & `json`/`csv` docs (https://docs.python.org/3/tutorial/inputoutput.html, ~45 mins).
6. **Completion Criteria:** Malformed JSON line or missing `campaign_id` goes to `quarantine.jsonl` without crashing remaining rows.
7. **Concepts Introduced:** *New:* `pathlib`, file modes, UTF-8 encoding, `csv`, `json` serialization/deserialization, quarantine pattern. *Reused:* Functions, dicts.

#### Day 6 — Failing Safely & Observing Execution (Exceptions, Logging & Debugging)
1. **Business Context:** Operators must diagnose why specific partner events failed without reading `print()` statements scattered through production code.
2. **Task — What I Must Do:** Define custom domain exceptions (`InvalidEventError`, `InsufficientBudgetError`), replace `print` with Python's `logging` module (structured levels `INFO`/`WARNING`/`ERROR`), and debug an intentional off-by-one / `KeyError` bug using a breakpoint debugger (`pdb` or VS Code debugger).
3. **Why Are We Doing This?:** Silent `except Exception: pass` hides financial bugs; structured logs + debugger inspection are core daily skills.
4. **How Should I Approach It? — HINT:** Catch specific exceptions narrowly; never swallow unexpected bugs silently. Configure `logging.basicConfig` with timestamps and levels.
5. **Prerequisite Learning Resources (<=1 hr):** Official Python Tutorial — Ch. 8 (*Errors and Exceptions*) + Python Logging HOWTO (basic section) (https://docs.python.org/3/tutorial/errors.html, ~50 mins).
6. **Completion Criteria:** You inspect stack frames and local variables in a debugger and explain `try/except/else/finally`.
7. **Concepts Introduced:** *New:* `try/except/else/finally`, custom `Exception` subclasses, `logging`, interactive debugging. *Reused:* File I/O, validation functions.

#### Day 7 — Structuring the AdStream Package (Modules, Packages, Virtual Environments, `uv`/pip)
1. **Business Context:** Single scripts can't scale across ingestion, ledger, and reporting teams; dependencies and imports must be reproducible.
2. **Task — What I Must Do:** Reorganize your scripts into a clean `src/adstream/` package (`models.py`, `ingestion.py`, `ledger.py`), set up an isolated virtual environment with `pyproject.toml`, and run entry points via `python -m adstream...`.
3. **Why Are We Doing This?:** Resolves "works on my machine" dependency drift and teaches Python module resolution (`sys.path`, relative vs absolute imports).
4. **How Should I Approach It? — HINT:** Use `uv` or `python -m venv`, install editable (`pip install -e .` / `uv sync`), and understand `__init__.py` and `if __name__ == "__main__":`.
5. **Prerequisite Learning Resources (<=1 hr):** Official Python Tutorial — Ch. 6 (*Modules*) & Ch. 12 (*Virtual Environments and Packages*) (https://docs.python.org/3/tutorial/modules.html, ~50 mins).
6. **Completion Criteria:** Fresh venv reproduces the project and imports work cleanly from outside `src/`.
7. **Concepts Introduced:** *New:* Modules, packages, `__init__.py`, `sys.path`, `venv`, `pyproject.toml`, dependency pinning. *Reused:* Functions, exceptions, logging.

#### Day 8 — Modeling Campaign & Ledger State (Classes, Objects, `self`, `__init__`)
1. **Business Context:** Passing loose dictionaries around (`campaign["budget"]`) lets callers accidentally corrupt negative balances or skip invariants.
2. **Task — What I Must Do:** Implement `Campaign` and `LedgerEntry` classes with `__init__`, `self`, instance attributes, and methods (`reserve(amount)`, `commit()`, `remaining_budget()`). Enforce invariants inside methods so balances can never become negative.
3. **Why Are We Doing This?:** Encapsulation binds data and the invariants protecting it in one place.
4. **How Should I Approach It? — HINT:** Trace what `self` actually points to at runtime (`c.reserve(10)` == `Campaign.reserve(c, 10)`). Compare a class with invariants vs a plain `dict`.
5. **Prerequisite Learning Resources (<=1 hr):** Official Python Tutorial — Ch. 9.1–9.4 (*Classes*) (https://docs.python.org/3/tutorial/classes.html, ~50 mins).
6. **Completion Criteria:** Direct invariant violation raises `InsufficientBudgetError`; you can explain `self`, `__init__`, instance vs class attributes without notes.
7. **Concepts Introduced:** *New:* Classes, instances, `self`, `__init__`, methods, class vs instance attributes, encapsulation. *Reused:* Exceptions, integer money.

#### Day 9 — Multi-Platform Adapters (Composition, Inheritance & Abstract Interfaces)
1. **Business Context:** AdStream ingests events from Google Ads, Meta, and Amazon Ads, each with different raw JSON shapes, into one canonical `AdEvent` model.
2. **Task — What I Must Do:** Build a shared base/protocol (`EventAdapter` using `abc.ABC` or `typing.Protocol`), implement two concrete adapters (`GoogleAdsAdapter`, `MetaAdsAdapter`), and compose them into an `IngestionPipeline` class (preferring composition over deep inheritance).
3. **Why Are We Doing This?:** Ingestion pipelines must add new ad sources without rewriting core validation or billing logic.
4. **How Should I Approach It? — HINT:** Compare *is-a* inheritance vs *has-a* composition. Keep canonical fields minimal and preserve `raw_payload`.
5. **Prerequisite Learning Resources (<=1 hr):** Official Python Tutorial — Ch. 9.5 (*Inheritance*) + `abc` docs (https://docs.python.org/3/library/abc.html, ~45 mins).
6. **Completion Criteria:** Adding a 3rd mock adapter requires zero changes to `IngestionPipeline`; you explain composition vs inheritance trade-offs.
7. **Concepts Introduced:** *New:* Inheritance, `super()`, `ABC`/`Protocol`, polymorphism, composition. *Reused:* Classes, JSON parsing.

#### Day 10 — Streaming 1M Simulated Events Without OOM (Iterators, Generators, Memory & GC)
1. **Business Context:** Loading a 2 GB partner event file into a Python `list` crashes a constrained container with Out-Of-Memory (OOM).
2. **Task — What I Must Do:** Build a deterministic synthetic event generator (`yield`) producing 1,000,000 events, compare peak RSS memory (`tracemalloc`) between returning a `list` vs a generator pipeline, and inspect reference counting / garbage collection behavior.
3. **Why Are We Doing This?:** Streaming architectures exist specifically to bound memory (`O(1)` per record) regardless of total stream volume.
4. **How Should I Approach It? — HINT:** Write generator functions and generator expressions; measure peak memory using `tracemalloc.get_traced_memory()`.
5. **Prerequisite Learning Resources (<=1 hr):** Official Python Tutorial — Ch. 9.8–9.10 (*Iterators & Generators*) + `tracemalloc` docs (https://docs.python.org/3/library/tracemalloc.html, ~45 mins).
6. **Completion Criteria:** Measured memory comparison shows generator stays flat while list scales linearly; you explain `yield` and CPython refcounting/GC cycles.
7. **Concepts Introduced:** *New:* Iterator protocol (`__iter__`/`__next__`), generators (`yield`), lazy evaluation, `tracemalloc`, refcounting & GC. *Reused:* File I/O, adapters.

#### Day 11 — Timing & Resource Guards (Decorators & Context Managers)
1. **Business Context:** AdStream needs automatic latency timing on critical functions and guaranteed cleanup/rollback when file or resource handles fail mid-operation.
2. **Task — What I Must Do:** Write a custom timing/retry decorator (`@measure_latency` using `functools.wraps`) and a custom context manager (`__enter__`/`__exit__` and `@contextmanager`) that writes safely to a temporary file and atomically replaces the target only on success.
3. **Why Are We Doing This?:** Prevents partial corrupted output files on crash and forms the foundation for transaction context managers and FastAPI decorators.
4. **How Should I Approach It? — HINT:** Test what happens when an exception is raised *inside* the `with` block—verify partial temp data does not overwrite the good file.
5. **Prerequisite Learning Resources (<=1 hr):** Python `contextlib` & `functools.wraps` official docs (https://docs.python.org/3/library/contextlib.html, ~45 mins).
6. **Completion Criteria:** Simulated crash inside `with` leaves original file untouched; `@measure_latency` preserves function metadata.
7. **Concepts Introduced:** *New:* Closures, decorators, `functools.wraps`, context managers (`__enter__`/`__exit__`), atomic temp-file swap. *Reused:* Exceptions, file I/O.

#### Day 12 — Automated Testing, Profiling & First HTTP Client (`pytest`, `cProfile`, `urllib`/`httpx`)
1. **Business Context:** Manual script runs cannot catch regressions across billing rules, and AdStream must also fetch partner campaign configs over HTTP and profile hot loops.
2. **Task — What I Must Do:** Write a `pytest` suite (fixtures, `parametrize`, edge cases) for all `Campaign` & adapter invariants; profile the 1M-event simulator with `cProfile` to find the slowest function; write a small Python HTTP client calling a public test endpoint (`httpbin.org/get` or local Python `http.server`) inspecting status/headers/timeouts.
3. **Why Are We Doing This?:** Establishes the test + benchmark discipline required for every remaining stage.
4. **How Should I Approach It? — HINT:** Test failure paths (`pytest.raises`), not only happy paths. Always pass explicit `timeout=` on HTTP requests.
5. **Prerequisite Learning Resources (<=1 hr):** `pytest` Getting Started (https://docs.pytest.org/en/stable/getting-started.html, ~40 mins) + Python `cProfile` docs (~20 mins).
6. **Completion Criteria:** `pytest` passes all positive + negative tests; `cProfile` output identifies the top hotspot with measured baseline time.
7. **Concepts Introduced:** *New:* `pytest`, fixtures, `parametrize`, `cProfile`, Python HTTP client & timeouts. *Reused:* Entire Stage A codebase.

---

### STAGE B — SQL and Database Engineering (Days 13–20)

#### Day 13 — Relational Modeling for AdStream (Tables, Keys, Constraints)
1. **Business Context:** In-memory Python objects disappear on restart and cannot enforce multi-table integrity across advertisers, campaigns, and ledger entries.
2. **Task — What I Must Do:** Stand up local PostgreSQL via Docker Compose; design and run DDL (`CREATE TABLE`) for `advertisers`, `campaigns`, `ad_events`, and `ledger_entries` with primary keys, foreign keys, `NOT NULL`, `CHECK (budget_micros >= 0)`, and `UNIQUE` idempotency constraints.
3. **Why Are We Doing This?:** Let the database enforce structural and financial invariants that application memory cannot guarantee across restarts.
4. **How Should I Approach It? — HINT:** Use `BIGINT` (not `FLOAT`/`REAL`) for micros, `TIMESTAMPTZ` for UTC timestamps, and `psql` to inspect `\d table_name`.
5. **Prerequisite Learning Resources (<=1 hr):** PostgreSQL Official Tutorial — Ch. 1–2 & DDL Constraints (https://www.postgresql.org/docs/current/ddl-constraints.html, ~50 mins).
6. **Completion Criteria:** Attempting to insert a negative budget or orphan campaign fails at the DB constraint layer.
7. **Concepts Introduced:** *New:* Relational tables, PK/FK, `CHECK`/`UNIQUE`/`NOT NULL`, `BIGINT` vs `NUMERIC` vs `FLOAT`, Docker Postgres. *Reused:* Integer money model.

#### Day 14 — CRUD, Filtering & Multi-Table Joins
1. **Business Context:** Account managers need to insert campaigns, update statuses, and pull advertiser-level spend reports combining advertisers, campaigns, and events.
2. **Task — What I Must Do:** Seed realistic data and write SQL queries covering `INSERT`, `UPDATE`, `DELETE`, `WHERE` filtering, `INNER JOIN`, and `LEFT JOIN` (finding campaigns with zero clicks).
3. **Why Are We Doing This?:** Misusing `INNER` vs `LEFT JOIN` silently drops zero-conversion campaigns from billing/analytics reports.
4. **How Should I Approach It? — HINT:** Compare `WHERE` filters on the right table of a `LEFT JOIN` vs `ON` conditions—observe how `WHERE` accidentally turns a `LEFT JOIN` into an `INNER JOIN`.
5. **Prerequisite Learning Resources (<=1 hr):** PostgreSQL Tutorial — Ch. 2.5–2.6 & Joins (https://www.postgresql.org/docs/current/tutorial-join.html, ~45 mins).
6. **Completion Criteria:** Queries accurately report 0-click campaigns without dropping them.
7. **Concepts Introduced:** *New:* SQL CRUD, `INNER`/`LEFT` joins, `NULL` three-valued logic. *Reused:* Schema from Day 13.

#### Day 15 — Reporting Metrics, Rollups & Deduplication Queries (Aggregations, Window Functions, CTEs)
1. **Business Context:** Finance needs daily spend per advertiser, running cumulative spend per campaign, and top-N creatives per country without double-counting duplicate clicks.
2. **Task — What I Must Do:** Write readable queries using `GROUP BY`, `HAVING`, CTEs (`WITH`), and window functions (`ROW_NUMBER()`, `SUM() OVER (PARTITION BY ... ORDER BY ...)`, `RANK()`).
3. **Why Are We Doing This?:** Window functions compute running balances and deduplicate (`ROW_NUMBER() = 1`) in a single pass without self-joins.
4. **How Should I Approach It? — HINT:** Compare `WHERE` (pre-aggregation) vs `HAVING` (post-aggregation) and `GROUP BY` (collapses rows) vs window functions (preserves rows).
5. **Prerequisite Learning Resources (<=1 hr):** PostgreSQL Docs — Window Functions Tutorial (https://www.postgresql.org/docs/current/tutorial-window.html, ~50 mins).
6. **Completion Criteria:** Running cumulative campaign spend matches ledger sums; duplicate event query keeps earliest event cleanly.
7. **Concepts Introduced:** *New:* `GROUP BY`, `HAVING`, CTEs, window functions (`OVER`, `PARTITION BY`, `ROW_NUMBER`). *Reused:* Joins, filtering.

#### Day 16 — Normalization vs Denormalization & Indexing
1. **Business Context:** Querying 1,000,000 simulated `ad_events` for one campaign's last-hour clicks takes seconds via full sequential scan.
2. **Task — What I Must Do:** Load 1M rows into `ad_events`, explain why campaign metadata is normalized out of `ad_events`, measure baseline query latency, add targeted single and composite B-tree indexes `(campaign_id, event_time)`, and compare read vs write overhead.
3. **Why Are We Doing This?:** Every index speeds up specific reads while slowing down every `INSERT`; blind indexing destroys ingestion throughput.
4. **How Should I Approach It? — HINT:** Test column order in a composite index: `(campaign_id, event_time)` vs `(event_time, campaign_id)`. Measure bulk insert speed before and after adding 4 indexes.
5. **Prerequisite Learning Resources (<=1 hr):** PostgreSQL Docs — Ch. 11 Indexes (11.1–11.5) (https://www.postgresql.org/docs/current/indexes.html, ~50 mins).
6. **Completion Criteria:** Recorded baseline vs indexed query latency AND measured insert slowdown.
7. **Concepts Introduced:** *New:* 1NF–3NF normalization, B-tree indexes, composite index column order, read/write trade-off. *Reused:* 1M row generator, SQL queries.

#### Day 17 — Reading Execution Plans (`EXPLAIN ANALYZE` & Query Optimization)
1. **Business Context:** A reporting query slows down unpredictably when data distribution is skewed (one giant advertiser has 60% of all clicks).
2. **Task — What I Must Do:** Run `EXPLAIN (ANALYZE, BUFFERS)` on filtered, joined, and skewed queries; identify `Seq Scan` vs `Index Scan` vs `Bitmap Heap Scan`, buffer hits, and nested-loop vs hash-join choices; fix a non-indexable predicate (e.g., `DATE(event_time) = ...` vs range filter).
3. **Why Are We Doing This?:** Guessing why SQL is slow wastes hours; `EXPLAIN (ANALYZE, BUFFERS)` shows exact I/O and row-estimate errors.
4. **How Should I Approach It? — HINT:** Seed skewed data (80/20), run `ANALYZE`, and compare estimated rows vs actual rows.
5. **Prerequisite Learning Resources (<=1 hr):** PostgreSQL Docs — Ch. 14.1 Using `EXPLAIN` (https://www.postgresql.org/docs/current/using-explain.html, ~50 mins).
6. **Completion Criteria:** You rewrite a non-sargable predicate to use an index and prove buffer reads + execution time dropped.
7. **Concepts Introduced:** *New:* `EXPLAIN (ANALYZE, BUFFERS)`, sargability, cardinality estimation, `Seq Scan`/`Index Scan`/Join strategies. *Reused:* Indexes, joins.

#### Day 18 — Transactions, ACID & Isolation Levels
1. **Business Context:** Charging an advertiser requires two writes: deducting `campaigns.remaining_budget` and inserting an immutable row into `ledger_entries`. Crashing between them corrupts money.
2. **Task — What I Must Do:** Demonstrate partial failure without a transaction (`autocommit`), wrap both writes in `BEGIN ... COMMIT` / `ROLLBACK`, and reproduce a Read Committed lost-update anomaly across two `psql` sessions—then test `REPEATABLE READ` and `SERIALIZABLE`.
3. **Why Are We Doing This?:** Understanding isolation levels prevents silent double-spend bugs that only happen under concurrency.
4. **How Should I Approach It? — HINT:** Open two terminal `psql` windows side-by-side and step through `BEGIN`, `SELECT`, `UPDATE`, `COMMIT` interleaved.
5. **Prerequisite Learning Resources (<=1 hr):** PostgreSQL Docs — Ch. 13.2 Transaction Isolation (https://www.postgresql.org/docs/current/transaction-iso.html, ~50 mins).
6. **Completion Criteria:** You physically reproduce a lost update in Read Committed and explain why `SERIALIZABLE` throws a serialization failure (`40001`).
7. **Concepts Introduced:** *New:* ACID, transactions, MVCC basics, Read Committed vs Repeatable Read vs Serializable, lost update. *Reused:* Ledger/campaign tables.

#### Day 19 — Reproducing & Fixing Concurrent Double-Spend (Locks, Deadlocks & Atomic Updates)
1. **Business Context:** 50 concurrent workers try to charge $10 each against a $100 campaign balance simultaneously.
2. **Task — What I Must Do:** Write a Python script spawning concurrent threads against Postgres doing naive `SELECT balance` -> `UPDATE balance` (proving overspend > $100), then fix it using both (a) conditional atomic `UPDATE ... WHERE remaining >= %s RETURNING remaining` and (b) `SELECT ... FOR UPDATE`, plus reproduce and resolve a 2-row deadlock via consistent lock ordering.
3. **Why Are We Doing This?:** Directly proves concurrency control with real failing/passing tests—essential for every financial/quota system.
4. **How Should I Approach It? — HINT:** Measure `overspend_count` and `p95` latency for naive vs conditional atomic `UPDATE` vs `FOR UPDATE`.
5. **Prerequisite Learning Resources (<=1 hr):** PostgreSQL Docs — Ch. 13.3 Explicit Locking (https://www.postgresql.org/docs/current/explicit-locking.html, ~45 mins).
6. **Completion Criteria:** Naive implementation overspends; atomic `UPDATE` & `FOR UPDATE` produce `$0` overspend across 100+ concurrent attempts; deadlock test succeeds.
7. **Concepts Introduced:** *New:* Row-level locks, `SELECT ... FOR UPDATE`, atomic conditional `UPDATE`, deadlocks, lock ordering. *Reused:* Transactions, Python threading.

#### Day 20 — Upserts, Idempotent Writes, Connection Pooling & Pagination
1. **Business Context:** Retried click webhooks arrive multiple times, opening a fresh TCP+Postgres connection per event exhausts `max_connections`, and `OFFSET 1000000` slows partner reporting pages to a crawl.
2. **Task — What I Must Do:** Implement idempotent event insertion via `INSERT ... ON CONFLICT (event_id) DO NOTHING`, benchmark pooled vs unpooled connections (`psycopg_pool`), and replace `OFFSET` pagination with keyset (cursor) pagination `(event_time, event_id) > (...)`.
3. **Why Are We Doing This?:** Makes ingestion safe under retries, keeps DB connections bounded, and gives `O(1)` page traversal.
4. **How Should I Approach It? — HINT:** Compare latency of `OFFSET 500000 LIMIT 50` vs keyset pagination using `EXPLAIN ANALYZE`.
5. **Prerequisite Learning Resources (<=1 hr):** PostgreSQL `INSERT ... ON CONFLICT` docs + Hussein Nasser connection pooling playlists (https://www.youtube.com/@hnasr/playlists & https://www.postgresql.org/docs/current/sql-insert.html, ~50 mins).
6. **Completion Criteria:** Duplicate insert causes zero duplicate ledger rows; keyset pagination outperforms `OFFSET` with measured numbers.
7. **Concepts Introduced:** *New:* `ON CONFLICT` upserts, connection pooling, keyset/cursor vs offset pagination. *Reused:* Indexes, `EXPLAIN ANALYZE`, transactions.

---

### STAGE C — HTTP, Networking and API Engineering (Days 21–26)

#### Day 21 — Network Plumbing Under HTTP (Client-Server, IP, Ports, DNS, TCP, TLS)
1. **Business Context:** External publishers in different regions send ad events to AdStream over the public internet—engineers must know what happens before a single line of API code executes.
2. **Task — What I Must Do:** Inspect DNS resolution (`nslookup`/`dig`), TCP connections (`ss`/`netstat` or Python `socket`), and TLS handshakes (`curl -v`); write a tiny raw Python `socket` client/server exchanging a minimal HTTP/1.1 `GET /health` response over localhost.
3. **Why Are We Doing This?:** When timeouts, TLS errors, or port conflicts happen in Docker or Azure, you cannot debug what you treat as magic.
4. **How Should I Approach It? — HINT:** Observe the raw text bytes of an HTTP request (`GET / HTTP/1.1\r\nHost: ...\r\n\r\n`). Note why TCP is a byte stream and HTTP adds framing.
5. **Prerequisite Learning Resources (<=1 hr):** Hussein Nasser — HTTP Playlist (early HTTP/TCP/TLS lectures) (https://www.youtube.com/playlist?list=PLQnljOFTspQU6zO0drAYHFtkkyfNJw1IO, ~55 mins).
6. **Completion Criteria:** Your raw socket server responds to `curl` with a valid `200 OK`; you explain DNS -> TCP 3-way handshake -> TLS -> HTTP.
7. **Concepts Introduced:** *New:* Client-server, IP, ports, DNS, TCP, TLS, raw HTTP framing. *Reused:* Python scripting.

#### Day 22 — HTTP Semantics: Methods, Status Codes & Where Data Belongs
1. **Business Context:** A publisher calls `GET` to record a click (causing browser prefetch false clicks) or puts secret API tokens in URL query strings (leaking secrets in proxy logs).
2. **Task — What I Must Do:** Build a minimal standard-library `http.server` handler for AdStream supporting `GET /campaigns/{id}` (path param + query filter `?status=active`), `POST /events/impressions` (JSON body + `202`/`201`), returning proper `400`, `401`, `404`, `409`, `422`, `429`, `500`, `503` status codes.
3. **Why Are We Doing This?:** Misusing methods or status codes breaks client retry logic (`5xx` retries vs `4xx` stop) and leaks credentials.
4. **How Should I Approach It? — HINT:** Document explicitly what belongs in **Path** (resource identity), **Query** (filtering/sorting/pagination), **Headers** (metadata/auth/content negotiation/idempotency key), and **Body** (payload).
5. **Prerequisite Learning Resources (<=1 hr):** MDN HTTP Overview, Methods & Status Codes (https://developer.mozilla.org/en-US/docs/Web/HTTP, ~50 mins).
6. **Completion Criteria:** `curl` tests verify every status code and demonstrate why `GET` must be safe/idempotent.
7. **Concepts Introduced:** *New:* HTTP methods (`GET/POST/PUT/PATCH/DELETE`), status code semantics, path vs query vs headers vs body. *Reused:* Python `json`, HTTP basics.

#### Day 23 — Payloads, Serialization & Headers (`JSON` vs Protobuf/Avro, `Content-Type`, `Accept`)
1. **Business Context:** AdStream needs human-debuggable external HTTP JSON APIs today while preparing for higher-density internal serialization later.
2. **Task — What I Must Do:** Implement `Content-Type` / `Accept` header checks and `Content-Length` parsing in your raw Python HTTP server; benchmark payload size & encode/decode speed of 10,000 `AdEvent` records in JSON vs gzipped JSON / compact binary encoding.
3. **Why Are We Doing This?:** Explains *why* JSON is chosen for external partner APIs (ubiquity, debuggability, schema flexibility) vs binary/columnar formats internally (CPU/network cost).
4. **How Should I Approach It? — HINT:** Reject non-`application/json` bodies with `415 Unsupported Media Type` and check what happens when `Content-Length` mismatches.
5. **Prerequisite Learning Resources (<=1 hr):** MDN HTTP Headers & Content Negotiation (https://developer.mozilla.org/en-US/docs/Web/HTTP/Content_negotiation, ~45 mins).
6. **Completion Criteria:** Recorded byte-size & serialization speed comparison; wrong `Content-Type` returns `415`.
7. **Concepts Introduced:** *New:* `Content-Type`, `Accept`, `Content-Length`, `415`, serialization trade-offs (JSON vs binary/Protobuf/Avro). *Reused:* `http.server`, benchmarking.

#### Day 24 — AuthN vs AuthZ, API Keys, Bearer Tokens & Stateless Design
1. **Business Context:** Advertiser A must never read or pause Advertiser B's campaigns, and AdStream must scale horizontally without pinning users to one server.
2. **Task — What I Must Do:** Implement hashed API-key authentication (`Authorization: Bearer ...` / `X-API-Key`) and tenant-scoped authorization checks in Python; compare stateful session cookies + sticky sessions vs stateless bearer tokens.
3. **Why Are We Doing This?:** Confusing Authentication (*who are you?*) with Authorization (*can you touch Campaign X?*) causes critical multi-tenant data leaks.
4. **How Should I Approach It? — HINT:** Never store raw API keys in Postgres—store SHA-256/HMAC hashes and compare in constant time (`hmac.compare_digest`).
5. **Prerequisite Learning Resources (<=1 hr):** MDN HTTP Authentication (https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication, ~45 mins).
6. **Completion Criteria:** Unauthenticated requests return `401`; Advertiser A modifying Advertiser B's campaign returns `403`.
7. **Concepts Introduced:** *New:* AuthN vs AuthZ, API keys, Bearer tokens, sessions vs cookies vs sticky sessions, stateless APIs, constant-time comparison. *Reused:* Headers, Postgres.

#### Day 25 — Manual Request Validation Pain -> Schema Contracts & Pydantic
1. **Business Context:** Publishers send strings where integers belong (`"cost": "free"`), negative bids, invalid country codes, and extra unknown fields.
2. **Task — What I Must Do:** First write **manual** dictionary validation (`isinstance`, missing keys, type conversion, error collection) for `ImpressionEvent` and `ClickEvent`—feel the boilerplate pain—then refactor the exact same contract into **Pydantic v2** models with strict types and custom validators.
3. **Why Are We Doing This?:** You understand what Pydantic abstracts (parsing, coercion/strictness, structured error paths) and what it does *not* abstract (cross-system business rules like budget existence).
4. **How Should I Approach It? — HINT:** Watch out for `isinstance(True, int) == True` in Python (`StrictInt` vs `int`!).
5. **Prerequisite Learning Resources (<=1 hr):** Official Pydantic Models & Validators Docs (https://docs.pydantic.dev/latest/concepts/models/, ~50 mins).
6. **Completion Criteria:** Both manual and Pydantic validators reject identical invalid inputs and collect structured field errors.
7. **Concepts Introduced:** *New:* API contracts, schema validation, Pydantic models, strict types vs coercion, `bool`-is-`int` pitfall. *Reused:* Exceptions, JSON, `pytest`.

#### Day 26 — Defensive API Controls (Rate Limiting, Timeouts, Retries, Pagination & Versioning)
1. **Business Context:** A buggy publisher script loops and blasts 5,000 requests/sec, threatening to take down AdStream for every other customer.
2. **Task — What I Must Do:** Implement an in-memory per-API-key rate limiter (`429 Too Many Requests` + `Retry-After` header), URL path versioning (`/v1/...`), standardized cursor pagination envelopes, and an HTTP client demonstrating timeouts + bounded retries with `Idempotency-Key`.
3. **Why Are We Doing This?:** Protects availability under abusive/buggy clients and prevents breaking downstream integrations when schemas evolve.
4. **How Should I Approach It? — HINT:** Only retry `5xx`/network errors, never `400`/`422`. Explain why `Idempotency-Key` belongs in a header.
5. **Prerequisite Learning Resources (<=1 hr):** MDN `429 Too Many Requests` (https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429, ~40 mins).
6. **Completion Criteria:** Burst exceeds limit -> `429` with `Retry-After`; client retry with same `Idempotency-Key` returns cached result without double-charging.
7. **Concepts Introduced:** *New:* Rate limiting, `429` + `Retry-After`, API versioning, `Idempotency-Key`, safe retry policies. *Reused:* Auth, headers, HTTP client.

---

### STAGE D — Backend and Application Engineering (Days 27–32)

#### Day 27 — Transitioning to FastAPI (App Structure, Routing & OpenAPI Docs)
1. **Business Context:** Maintaining raw `http.server` routing, JSON parsing, and header boilerplate slows down adding new AdStream endpoints.
2. **Task — What I Must Do:** Build the `adstream` FastAPI application (`app/main.py`, `routers/campaigns.py`, `routers/events.py`), wire Pydantic models, and inspect the auto-generated `/docs` OpenAPI schema.
3. **Why Are We Doing This?:** FastAPI gives routing, Pydantic validation, and OpenAPI contracts out of the box—building directly on Stage C fundamentals.
4. **How Should I Approach It? — HINT:** Keep route handlers thin; push business logic into service functions (`services/`), never inside route functions.
5. **Prerequisite Learning Resources (<=1 hr):** FastAPI Official Tutorial — First Steps & Path/Query/Body (https://fastapi.tiangolo.com/tutorial/first-steps/, ~50 mins).
6. **Completion Criteria:** `/v1/campaigns` and `/v1/events/impressions` work via `uvicorn`, returning clean OpenAPI schema.
7. **Concepts Introduced:** *New:* FastAPI, ASGI/`uvicorn`, `APIRouter`, OpenAPI docs. *Reused:* Pydantic, HTTP methods/status codes.

#### Day 28 — Request Lifecycle, Middleware & Structured Error Handling
1. **Business Context:** Every incoming request needs a `request_id` correlation header, latency measurement, and uniform JSON error payloads—even on unhandled exceptions.
2. **Task — What I Must Do:** Add FastAPI middleware injecting/propagating `X-Request-ID` and logging request duration; add global `@app.exception_handler` handlers mapping domain exceptions (`InsufficientBudgetError`, `UnauthorizedError`) to clean HTTP responses without leaking stack traces.
3. **Why Are We Doing This?:** Correlation IDs trace a single failed ad request across API, database, and logs.
4. **How Should I Approach It? — HINT:** Keep exception-to-HTTP mapping in the API layer, not inside domain/ledger classes.
5. **Prerequisite Learning Resources (<=1 hr):** FastAPI Docs — Middleware & Handling Errors (https://fastapi.tiangolo.com/tutorial/handling-errors/, ~45 mins).
6. **Completion Criteria:** Every response contains `X-Request-ID`; domain errors return clean JSON (`error_code`, `message`, `request_id`).
7. **Concepts Introduced:** *New:* Middleware, request lifecycle, exception handlers, correlation IDs. *Reused:* Logging, custom exceptions.

#### Day 29 — Dependency Injection, Configuration & Secrets Management
1. **Business Context:** Database URLs and API-key salts cannot be hardcoded in Python files or committed to Git, and tests need to swap real Postgres or clocks cleanly.
2. **Task — What I Must Do:** Implement `pydantic-settings` configuration reading from environment variables / `.env` (gitignored), and use FastAPI `Depends()` to inject settings, authenticated `AdvertiserContext`, and DB connections into endpoints.
3. **Why Are We Doing This?:** Separates configuration from code (12-Factor App) and enables clean unit/integration test overrides.
4. **How Should I Approach It? — HINT:** Check `.gitignore` includes `.env`. Explain how `Depends()` constructs and cleans up per-request dependencies (`yield`).
5. **Prerequisite Learning Resources (<=1 hr):** FastAPI Docs — Dependencies & Settings (https://fastapi.tiangolo.com/tutorial/dependencies/, ~50 mins).
6. **Completion Criteria:** App fails fast at startup if required env var is missing; zero secrets in repo.
7. **Concepts Introduced:** *New:* Dependency injection (`Depends`), `pydantic-settings`, 12-factor config, secrets hygiene. *Reused:* FastAPI, auth, context managers.

#### Day 30 — Database Integration & Synchronous Budget-Reservation Endpoint
1. **Business Context:** AdStream needs a real `POST /v1/bids/reserve` and `POST /v1/events/clicks` API backed by Postgres connection pooling and idempotent ledger writes.
2. **Task — What I Must Do:** Connect FastAPI lifespan startup/shutdown to `psycopg_pool`, implement `POST /v1/events/clicks` with `Idempotency-Key` + transactional budget deduction + ledger row + `ON CONFLICT`, and prove zero overspend under concurrent HTTP requests.
3. **Why Are We Doing This?:** Combines API engineering with Stage B database correctness under real HTTP concurrency.
4. **How Should I Approach It? — HINT:** Ensure DB connections are always returned to the pool even on exception; run 50 concurrent HTTP requests against a $100 budget.
5. **Prerequisite Learning Resources (<=1 hr):** FastAPI Lifespan Events (https://fastapi.tiangolo.com/advanced/events/) + `psycopg_pool` docs (~45 mins).
6. **Completion Criteria:** Concurrent HTTP load test produces exact `$100` spent, `0` overspend, `0` duplicate charges on retry.
7. **Concepts Introduced:** *New:* App lifespan hooks, DB pool injection, HTTP-to-DB idempotency end-to-end. *Reused:* Transactions, atomic SQL, `Depends`.

#### Day 31 — AsyncIO, Threading, Multiprocessing & the GIL
1. **Business Context:** FastAPI runs an `async` event loop—calling a blocking synchronous `time.sleep()` or CPU-heavy loop inside an `async def` route freezes every other concurrent user.
2. **Task — What I Must Do:** Run controlled experiments comparing `def` vs `async def` endpoints under blocking I/O vs non-blocking `asyncio` I/O vs CPU-bound work (`multiprocessing`), measuring throughput and tail latency across all three.
3. **Why Are We Doing This?:** Misunderstanding Python's event loop and GIL is the #1 cause of mysteriously stalled FastAPI services in production.
4. **How Should I Approach It? — HINT:** Explain *why* FastAPI runs sync `def` routes in a threadpool while `async def` runs directly on the event loop.
5. **Prerequisite Learning Resources (<=1 hr):** FastAPI Concurrency & `async`/`await` guide (https://fastapi.tiangolo.com/async/, ~45 mins).
6. **Completion Criteria:** You demonstrate event-loop starvation in `async def` with a blocking call, fix it, and explain GIL vs `asyncio` vs `multiprocessing`.
7. **Concepts Introduced:** *New:* Event loop, `async`/`await`, threadpool offload, GIL, `multiprocessing`. *Reused:* FastAPI, benchmarking.

#### Day 32 — FastAPI `TestClient`, Integration Testing & CI
1. **Business Context:** Every PR to AdStream must automatically run unit and Postgres integration tests before merge.
2. **Task — What I Must Do:** Build a full `pytest` + `httpx`/`TestClient` integration test suite (covering auth, 422 validation, 409/402 budget exhaustion, idempotent retries, and DB state verification) plus a GitHub Actions workflow running `pytest` on push.
3. **Why Are We Doing This?:** Turns AdStream into an inspectable, regression-tested backend engineering artifact.
4. **How Should I Approach It? — HINT:** Roll back or truncate test DB tables cleanly between test functions using pytest fixtures.
5. **Prerequisite Learning Resources (<=1 hr):** FastAPI Testing Docs (https://fastapi.tiangolo.com/tutorial/testing/, ~40 mins).
6. **Completion Criteria:** `pytest` passes locally and in CI with isolated test fixtures.
7. **Concepts Introduced:** *New:* `TestClient`, API integration tests, fixture DB isolation, CI test runner. *Reused:* `pytest`, Stage D endpoints.

---

### STAGE E — Data Engineering and Ingestion (Days 33–37)

#### Day 33 — Source Systems, Extraction & Full vs Incremental Watermarks
1. **Business Context:** Partner platforms export campaign and conversion tables hourly; re-reading the entire historical database every hour wastes network and compute.
2. **Task — What I Must Do:** Simulate a source OLTP Postgres database (`source_conversions`), implement an extractor supporting `FULL` load and `INCREMENTAL` load using a persistent `watermark` table (`last_updated_at, last_id`), and handle tie-breaking when two rows share the same timestamp.
3. **Why Are We Doing This?:** Naive `WHERE updated_at > last_watermark` silently drops rows sharing the boundary second (`>=` causes duplicates unless paired with deduplication).
4. **How Should I Approach It? — HINT:** Test the exact boundary tie bug (`updated_at == watermark`) and solve it with `>=` + downstream idempotency/dedupe or composite `(updated_at, id)`.
5. **Prerequisite Learning Resources (<=1 hr):** Arpit Bhayani system design & ingestion concepts (https://www.youtube.com/c/ArpitBhayani, ~45 mins).
6. **Completion Criteria:** Boundary-second rows are never lost and never duplicated after re-runs.
7. **Concepts Introduced:** *New:* Source-to-target mapping, ETL vs ELT, full vs incremental loads, watermarks, boundary tie-breaking. *Reused:* Postgres, Python SQL.

#### Day 34 — Change Data Capture (CDC) Fundamentals & Debezium-Style Events
1. **Business Context:** Polling `updated_at` misses hard `DELETE`s and adds query load to production OLTP tables.
2. **Task — What I Must Do:** Enable Postgres logical replication (`wal_level = logical`), create a logical replication slot (`pgoutput`/`test_decoding`), and write a Python script consuming `INSERT`/`UPDATE`/`DELETE` WAL change records into AdStream's event model, handling initial snapshot -> stream handoff.
3. **Why Are We Doing This?:** Connects your enterprise Debezium/Kafka exposure to the actual Postgres WAL mechanism underneath it.
4. **How Should I Approach It? — HINT:** Observe what LSN (Log Sequence Number) means and why `DELETE` events need `REPLICA IDENTITY` if you want old column values.
5. **Prerequisite Learning Resources (<=1 hr):** PostgreSQL Docs — Logical Decoding Concepts (https://www.postgresql.org/docs/current/logicaldecoding-explanation.html, ~45 mins).
6. **Completion Criteria:** Inserting, updating, and deleting a campaign emits ordered WAL change records captured by your Python reader.
7. **Concepts Introduced:** *New:* WAL, LSN, logical replication slots, CDC (`INSERT`/`UPDATE`/`DELETE`), `REPLICA IDENTITY`, snapshot-to-stream handoff. *Reused:* Postgres, Docker.

#### Day 35 — Data Quality, Quarantine & Idempotent Checkpointed Loaders
1. **Business Context:** An ingestion batch of 100,000 events crashes at record 72,000—re-running from 0 must neither double-load the first 72,000 nor lose the remaining 28,000.
2. **Task — What I Must Do:** Build a checkpointed batch loader committing chunked progress + data quality checks (null rates, referential checks, duplicate rates) and routing bad rows to a quarantine store with reason codes.
3. **Why Are We Doing This?:** Separates ingestion resilience from "all-or-nothing" brittle scripts.
4. **How Should I Approach It? — HINT:** Kill the process mid-run (`SIGINT`), re-run it, and verify final row counts and financial totals equal an uninterrupted run.
5. **Prerequisite Learning Resources (<=1 hr):** Martin Kleppmann / Confluent stream & data-correctness talks on idempotency and checkpoints (~50 mins).
6. **Completion Criteria:** Crash-and-restart test produces exact expected counts with zero duplicates and full quarantine audit trail.
7. **Concepts Introduced:** *New:* Checkpointing, crash recovery, data quality assertions, quarantine tables/files. *Reused:* Idempotency, transactions.

#### Day 36 — Schema Evolution Without Breaking Consumers
1. **Business Context:** A partner adds `creative_format`, renames a nullable field, or sends an unexpected enum value at 2 AM.
2. **Task — What I Must Do:** Implement `schema_version` handling in AdStream's ingestion layer supporting backward-compatible additive fields, rejecting breaking changes to quarantine, and testing mixed v1 + v2 batches.
3. **Why Are We Doing This?:** Upstream schemas always drift; unguarded pipelines corrupt sinks or halt overnight operations.
4. **How Should I Approach It? — HINT:** Distinguish backward compatibility, forward compatibility, and breaking changes.
5. **Prerequisite Learning Resources (<=1 hr):** Confluent Schema Evolution concepts (https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html, ~40 mins).
6. **Completion Criteria:** v1 + v2 events process cleanly; unknown breaking v99 payloads quarantine cleanly without halting v1/v2.
7. **Concepts Introduced:** *New:* Schema evolution, backward/forward compatibility, schema versioning. *Reused:* Pydantic, quarantine.

#### Day 37 — Columnar Formats, Compression, Partitioning & Throughput (CSV vs JSON vs Parquet)
1. **Business Context:** Storing 500M daily events as raw JSON burns storage and forces queries to scan every field of every row.
2. **Task — What I Must Do:** Write 500,000 simulated `AdEvent` rows to CSV, JSONL, gzipped JSONL, and Apache Parquet (Snappy & Zstd) using `pyarrow`; partition by `event_date` and `country`; measure file sizes, write throughput (events/sec, MB/sec), and single-column projection read time.
3. **Why Are We Doing This?:** Establishes concrete FinOps math for storage and scan cost before touching Azure or Spark.
4. **How Should I Approach It? — HINT:** Test batch sizes (1,000 vs 50,000 vs 250,000 rows per Parquet file) to see the "small files" overhead firsthand.
5. **Prerequisite Learning Resources (<=1 hr):** Apache Parquet Overview & PyArrow docs (https://parquet.apache.org/docs/overview/, ~45 mins).
6. **Completion Criteria:** Measured benchmark table comparing size, compression ratio, write MB/s, and column-filtered read latency.
7. **Concepts Introduced:** *New:* Row vs columnar storage, Parquet, Snappy/Zstd compression, Hive-style partitioning, batch sizing, throughput measurement. *Reused:* Generator, benchmarking.

---

### STAGE F — Azure and Cloud Fundamentals (Days 38–40)

#### Day 38 — Azure Free Account Setup, Cost Guardrails & Resource Groups
1. **Business Context:** Moving selected AdStream components to Azure requires strict financial safety so an idle cluster or runaway script never triggers a surprise bill.
2. **Task — What I Must Do:** Verify Azure Free Account eligibility, create a dedicated Resource Group (`rg-adstream-dev`), configure Azure Budgets + email cost alerts ($1 / $5 thresholds), and practice resource tagging and clean deletion.
3. **Why Are We Doing This?:** Cloud engineering without cost guardrails violates FinOps and risks accidental charges.
4. **How Should I Approach It? — HINT:** Review India-specific Free Account vs Pay-As-You-Go rules (see Part D) before provisioning anything.
5. **Prerequisite Learning Resources (<=1 hr):** Microsoft Learn — Azure Budgets (https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/tutorial-acm-create-budgets, ~40 mins).
6. **Completion Criteria:** Budget alert configured; resource group created and verifiable via Azure CLI (`az group list`).
7. **Concepts Introduced:** *New:* Azure subscription, resource groups, regions, budgets/alerts, `az` CLI. *Reused:* None.

#### Day 39 — Azure Storage: Blob Storage vs ADLS Gen2, Containers & Access Control
1. **Business Context:** AdStream needs durable cloud object storage for Bronze/Silver/Gold Parquet files without paying for hierarchical namespace transaction surprises.
2. **Task — What I Must Do:** Compare local MinIO/Azurite vs Azure Blob Storage (5 GB LRS 12-mo free allowance) and ADLS Gen2 (hierarchical namespace billing difference); provision a single low-cost Standard LRS storage account, create `bronze`/`silver`/`gold` containers, and upload Parquet files from Day 37 via Python SDK using short-lived SAS tokens vs Entra RBAC.
3. **Why Are We Doing This?:** Teaches cloud object storage, POSIX ACLs vs RBAC, and why ADLS Gen2 charges extra metadata operations.
4. **How Should I Approach It? — HINT:** Prefer Azurite locally for iterative testing; upload only small test Parquet samples to Azure and delete/clean up when done.
5. **Prerequisite Learning Resources (<=1 hr):** Microsoft Learn — ADLS Gen2 Intro (https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-introduction, ~50 mins).
6. **Completion Criteria:** Parquet partition uploaded and read back via Python; you explain Blob vs ADLS Gen2 cost & ACL differences.
7. **Concepts Introduced:** *New:* Blob Storage, ADLS Gen2, LRS redundancy, containers, RBAC, ACLs, SAS tokens, Azurite. *Reused:* Parquet, Python SDK.

#### Day 40 — Cloud Identity, Networking & Monitoring (Entra ID, Service Principals, VNets, Monitor)
1. **Business Context:** Production pipelines cannot use developer personal logins or wide-open `0.0.0.0/0` storage firewalls.
2. **Task — What I Must Do:** Create a least-privilege Service Principal (`Storage Blob Data Contributor` scoped only to one container), test Azure Storage firewall rules (allowed IP vs denied IP), inspect Private Endpoint pricing (do *not* leave paid Private Endpoints running—document cost!), and explore Azure Monitor metrics/logs + Azure Functions free-grant eligibility.
3. **Why Are We Doing This?:** Establishes cloud security boundaries and teaches which networking features (like Private Endpoints / NAT Gateways) cost money per hour.
4. **How Should I Approach It? — HINT:** Verify Private Endpoint hourly + GB charges before creating; delete any temporary network test resources immediately after verifying.
5. **Prerequisite Learning Resources (<=1 hr):** Microsoft Learn — Managed Identities & Service Principals (https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview, ~45 mins).
6. **Completion Criteria:** Service Principal accesses only its scoped container; unauthorized container returns `403`.
7. **Concepts Introduced:** *New:* Microsoft Entra ID, Service Principals, Managed Identities, VNets, firewalls, Private Endpoints (cost trade-off), Azure Monitor. *Reused:* RBAC, AuthZ.

---

### STAGE G — On-Premises to Azure Integration (Days 41–43)

#### Day 41 — Simulating On-Premises Systems & Setting Up Self-Hosted Integration Runtime (SHIR)
1. **Business Context:** A retail-media partner runs an on-premises database and local CSV drop folder behind a private network that Azure cannot reach directly.
2. **Task — What I Must Do:** Prepare local on-premises Postgres + local drop directory, create an Azure Data Factory instance (free tier: first 1,000 orchestration activity runs/mo free), install/register a Self-Hosted Integration Runtime (free up to 5 nodes) on your Windows host, and configure Linked Services & Datasets.
3. **Why Are We Doing This?:** Physically configures hybrid cloud connectivity without opening inbound corporate firewall ports.
4. **How Should I Approach It? — HINT:** Keep ADF triggers paused/manual—never leave polling schedule triggers running (`$1/1,000` runs if exceeded!). Avoid ADF Mapping Data Flows (`$0.273/vCore-hour`—not free!).
5. **Prerequisite Learning Resources (<=1 hr):** Microsoft Learn — Create & Configure Self-Hosted IR (https://learn.microsoft.com/en-us/azure/data-factory/create-self-hosted-integration-runtime, ~45 mins).
6. **Completion Criteria:** ADF Portal shows SHIR status `Running (Connected)` and Linked Service `Test Connection` succeeds to your local Postgres/files.
7. **Concepts Introduced:** *New:* On-prem simulation, ADF, Linked Services, Datasets, Self-Hosted IR vs Azure IR. *Reused:* Local Postgres, Azure Storage.

#### Day 42 — Hybrid Full & Incremental Copy Pipelines in ADF
1. **Business Context:** AdStream must reliably copy both small reference tables (full load) and growing conversion logs (incremental watermark) from on-premises to Azure Storage.
2. **Task — What I Must Do:** Build two ADF pipelines using Copy Activity: (a) Full Copy of local `campaigns` table to Bronze Parquet, (b) Incremental Watermark Copy using Lookup + Copy + watermark update against Azure SQL Free Offer (100,000 vCore-sec/mo, 32 GB) or local metadata.
3. **Why Are We Doing This?:** Proves real hybrid cloud ingestion and teaches why ADF Copy DIUs and run counts matter for cost.
4. **How Should I Approach It? — HINT:** Explicitly cap Copy Activity DIUs to minimum (2 DIUs / SHIR local compute) and track run count well below 1,000/month.
5. **Prerequisite Learning Resources (<=1 hr):** Microsoft Learn — Incrementally Copy Data via Watermark in ADF (https://learn.microsoft.com/en-us/azure/data-factory/tutorial-incremental-copy-portal, ~50 mins).
6. **Completion Criteria:** Only newly inserted local rows copy on Pipeline Run #2; Azure Storage contains valid partitioned Bronze files.
7. **Concepts Introduced:** *New:* ADF Pipelines, Copy/Lookup activities, Azure SQL Free Offer, SHIR data transfer. *Reused:* Watermarks, Parquet, incremental loads.

#### Day 43 — Hybrid Failure Recovery, Monitoring, Network Limits & Cost Audit
1. **Business Context:** Mid-transfer, the local machine loses connectivity or a schema mismatch occurs—we must recover cleanly and quantify cloud vs local cost.
2. **Task — What I Must Do:** Inject a mid-pipeline failure (stop local Postgres or drop network during copy), inspect ADF Monitor logs & retry behavior, re-run from failure without duplicating target files, measure transfer throughput (MB/s), and calculate exact monthly ADF + Storage cost at 1x and 100x scale.
3. **Why Are We Doing This?:** Proves operational mastery and prevents cloud bill surprises before moving heavy transforms to local Spark.
4. **How Should I Approach It? — HINT:** Compare ADF Cloud IR DIU-hour billing (`$0.25/DIU-hr`) vs SHIR local compute + egress/transaction costs.
5. **Prerequisite Learning Resources (<=1 hr):** Microsoft Learn — Monitor ADF Pipelines (https://learn.microsoft.com/en-us/azure/data-factory/monitor-visually, ~40 mins).
6. **Completion Criteria:** Post-failure recovery yields zero duplicates; cost table written and verified against `Cost Management` showing $0.00 (or exact micro-cents).
7. **Concepts Introduced:** *New:* Pipeline monitoring, restartability, network bottlenecks, ADF FinOps cost modeling. *Reused:* ADF pipelines, failure injection.

---

### STAGE H — Data Warehousing and Delta Lake (Days 44–47)

#### Day 44 — OLTP vs OLAP & Dimensional Modeling (Grain, Facts, Dimensions, Surrogate Keys)
1. **Business Context:** Running analytical attribution queries directly on AdStream's live transactional `campaigns`/`ledger` Postgres tables locks operational writes and scans poorly.
2. **Task — What I Must Do:** Define AdStream's analytical star schema: declare explicit **grain** (`1 row per validated click/impression`, `1 row per daily campaign summary`), design `fact_ad_events`, `fact_billing_ledger`, `dim_advertiser`, `dim_campaign`, `dim_publisher`, `dim_date` with surrogate keys, and populate them locally in DuckDB/Postgres.
3. **Why Are We Doing This?:** Mixing grains inside one fact table double-counts revenue and breaks BI/finance dashboards.
4. **How Should I Approach It? — HINT:** Clearly separate natural/business keys (`campaign_id`) from warehouse surrogate keys (`campaign_sk`).
5. **Prerequisite Learning Resources (<=1 hr):** DuckDB Analytical SQL Docs (https://duckdb.org/docs/sql/introduction, ~45 mins).
6. **Completion Criteria:** Analytical queries aggregate revenue accurately without double-counting; you can state the exact grain of every fact table.
7. **Concepts Introduced:** *New:* OLTP vs OLAP, star schema, fact vs dimension tables, grain, surrogate keys. *Reused:* SQL aggregations, joins.

#### Day 45 — Medallion Architecture (Bronze / Silver / Gold) & Slowly Changing Dimensions (SCD 0–3)
1. **Business Context:** An advertiser changes their campaign's `pricing_model` or `country_tier` mid-month—historical reports from last month must still reflect what was true *then*, not overwrite history.
2. **Task — What I Must Do:** Implement AdStream's local Bronze (raw immutable) -> Silver (cleaned, deduplicated, conformed) -> Gold (business aggregates) pipeline, and implement SCD Type 0, Type 1, Type 2 (`effective_from`, `effective_to`, `is_current`), and Type 3 (`previous_tier`) on `dim_campaign`.
3. **Why Are We Doing This?:** Without SCD Type 2, historical financial audits and attribution break whenever campaign metadata changes.
4. **How Should I Approach It? — HINT:** Join an event from Day 1 against `dim_campaign` on `event_time BETWEEN effective_from AND effective_to`.
5. **Prerequisite Learning Resources (<=1 hr):** Databricks Medallion Architecture Glossary (https://www.databricks.com/glossary/medallion-architecture, ~40 mins).
6. **Completion Criteria:** Changing a campaign tier preserves old historical attribution while new events map to the new version.
7. **Concepts Introduced:** *New:* Medallion (Bronze/Silver/Gold), SCD Types 0, 1, 2, 3, point-in-time dimension joins. *Reused:* CDC events, star schema.

#### Day 46 — Delta Lake Internals (`_delta_log`, ACID, `MERGE`, Schema Enforcement & Time Travel)
1. **Business Context:** Writing raw Parquet folders leaves partial corrupt files on job failure and makes updating late-arriving conversions painful.
2. **Task — What I Must Do:** Set up Delta Lake locally (`delta-spark` or `deltalake` Python package), inspect the JSON/checkpoint files inside `_delta_log/`, run atomic `MERGE INTO` for idempotent upserts & late conversions, test schema enforcement vs `mergeSchema`, and query an earlier snapshot via Time Travel (`VERSION AS OF`).
3. **Why Are We Doing This?:** Explains *how* Delta Lake adds ACID transactions on top of immutable Parquet files in object storage.
4. **How Should I Approach It? — HINT:** Open a `_delta_log/00000...json` file in a text editor after an insert and a `MERGE`—see `add` and `remove` file actions directly.
5. **Prerequisite Learning Resources (<=1 hr):** Delta Lake Official Docs — Deletes/Updates/Merges & Time Travel (https://docs.delta.io/latest/delta-update.html, ~50 mins).
6. **Completion Criteria:** You inspect `_delta_log` JSON actions, perform an idempotent `MERGE`, and roll back/query a prior table version.
7. **Concepts Introduced:** *New:* Delta Lake, `_delta_log` transaction log, optimistic concurrency, `MERGE`, schema enforcement/evolution, time travel. *Reused:* Parquet, SCD/CDC.

#### Day 47 — Delta Optimization, Small Files, Compaction, Skew & Late-Arriving Corrections
1. **Business Context:** Micro-batch ingestion writes thousands of tiny 50 KB Parquet files, slowing queries by 20x, while late conversions arrive 6 hours late.
2. **Task — What I Must Do:** Intentionally create a "small files problem" (500 tiny appends), measure query scan time, run `OPTIMIZE` compaction + `VACUUM`, apply partition pruning, and process a 6-hour late-arriving conversion correction cleanly.
3. **Why Are We Doing This?:** Small files and uncompacted metadata silently destroy lakehouse performance and storage costs.
4. **How Should I Approach It? — HINT:** Measure file count and query latency before and after compaction; check why `VACUUM` retention prevents breaking concurrent readers/time travel.
5. **Prerequisite Learning Resources (<=1 hr):** Delta Lake Docs — Optimizations & File Compaction (https://docs.delta.io/latest/optimizations-oss.html, ~45 mins).
6. **Completion Criteria:** Measurable drop in file count and scan latency post-compaction; late conversion correctly updates Gold metrics.
7. **Concepts Introduced:** *New:* Small-files problem, compaction (`OPTIMIZE`), `VACUUM`, partition pruning, late-arriving corrections. *Reused:* Delta Lake, benchmarking.

---

### STAGE I — Apache Spark and PySpark (Days 48–52)

#### Day 48 — Why Distributed Compute? Spark Architecture, Driver, Executors, RDDs vs DataFrames
1. **Business Context:** Single-node Python/DuckDB hits memory and CPU walls when joining and aggregating tens of millions of ad events.
2. **Task — What I Must Do:** Run Apache Spark locally via Docker (Driver + 2 Worker Executors, zero Azure Databricks cost), compare RDD vs DataFrame API on 5M simulated events, inspect `Jobs` / `Stages` / `Tasks` in the Spark UI (`localhost:4040`), and demonstrate **lazy evaluation** (transformations vs actions).
3. **Why Are We Doing This?:** If you don't know where code runs (Driver vs Executor), you accidentally `collect()` gigabytes onto the Driver and OOM it.
4. **How Should I Approach It? — HINT:** Watch Spark UI remain idle during `.filter()` / `.withColumn()` until `.count()` or `.write` executes.
5. **Prerequisite Learning Resources (<=1 hr):** Apache Spark Cluster Overview (https://spark.apache.org/docs/latest/cluster-overview.html, ~45 mins).
6. **Completion Criteria:** Spark UI metrics confirm distributed tasks; you explain Driver, Executors, Cluster Manager, DAG, and lazy evaluation.
7. **Concepts Introduced:** *New:* Distributed compute, Driver, Executors, Cluster Manager, RDD vs DataFrame, Jobs/Stages/Tasks, DAG, lazy evaluation. *Reused:* Parquet, 5M simulator.

#### Day 49 — Transformations, Shuffles, Partitions & Joins (Broadcast vs Sort-Merge vs Shuffle Hash)
1. **Business Context:** Joining 10M click events with 5,000 campaigns triggers a massive network shuffle unless Spark chooses the right join plan.
2. **Task — What I Must Do:** Inspect `df.explain(True)` across narrow (`map`/`filter`) vs wide (`groupBy`/`join`) transformations; compare **Broadcast Hash Join** vs **Sort-Merge Join** vs **Shuffle Hash Join** on `ad_events` x `campaigns`; compare `repartition()` vs `coalesce()`.
3. **Why Are We Doing This?:** Shuffles write data to disk and move bytes across the network—90% of Spark latency comes from wide shuffles.
4. **How Should I Approach It? — HINT:** Force Broadcast off (`spark.sql.autoBroadcastJoinThreshold = -1`) vs on, and measure shuffle bytes & execution time in Spark UI.
5. **Prerequisite Learning Resources (<=1 hr):** Spark SQL Performance Tuning Docs (https://spark.apache.org/docs/latest/sql-performance-tuning.html, ~50 mins).
6. **Completion Criteria:** Measured shuffle bytes + duration prove Broadcast Join speedup; you explain when `coalesce` avoids a shuffle vs `repartition`.
7. **Concepts Introduced:** *New:* Narrow vs wide transformations, shuffles, `repartition` vs `coalesce`, Broadcast / Sort-Merge / Shuffle Hash joins. *Reused:* Spark UI, star schema.

#### Day 50 — Inside Spark: Catalyst Optimizer, Tungsten, Memory Management & Caching
1. **Business Context:** Repeatedly scanning the same Silver event dataset across Fraud, Billing, and Analytics jobs wastes I/O, while inefficient Python UDFs bypass Spark's fast JVM engine.
2. **Task — What I Must Do:** Compare a native Spark SQL expression vs a Python row-by-row UDF vs a Pandas/Arrow vectorized UDF; inspect Catalyst's logical -> physical plan (`explain("extended")`); measure `cache()` / `persist(MEMORY_AND_DISK)` vs `checkpoint()` when reusing an intermediate DataFrame.
3. **Why Are We Doing This?:** Python UDFs force expensive JVM <-> Python serialization per row and blind Catalyst optimizations like predicate pushdown.
4. **How Should I Approach It? — HINT:** Check Spark UI Storage tab and execution time across SQL built-in vs Python UDF vs Pandas UDF.
5. **Prerequisite Learning Resources (<=1 hr):** Spark PySpark Arrow/Pandas UDF Docs (https://spark.apache.org/docs/latest/api/python/user_guide/sql/arrow_pandas.html, ~50 mins).
6. **Completion Criteria:** Measured runtime confirms why native SQL/Arrow beats row-by-row Python UDFs; you explain Catalyst, Tungsten, `cache` vs `checkpoint`.
7. **Concepts Introduced:** *New:* Catalyst optimizer, Tungsten, JVM-Python serialization, predicate pushdown, `cache`/`persist`/`checkpoint`. *Reused:* DataFrames, Parquet.

#### Day 51 — Fixing Data Skew, Spill to Disk & Adaptive Query Execution (AQE)
1. **Business Context:** One mega-advertiser generates 60% of all clicks—99 Spark tasks finish in 3 seconds while 1 straggler task runs for 4 minutes and spills to disk.
2. **Task — What I Must Do:** Generate a heavily skewed dataset (`advertiser_id = "mega"` = 60% rows), observe the straggler task + spill metrics in Spark UI, fix it via **salting** (manual key salting + two-stage aggregation) AND compare against Spark **Adaptive Query Execution (AQE)** skew-join handling.
3. **Why Are We Doing This?:** Turns conceptual skew/spill knowledge into proven diagnostic & implementation skill.
4. **How Should I Approach It? — HINT:** Turn `spark.sql.adaptive.enabled` `false` vs `true`, record task max duration and disk spill bytes.
5. **Prerequisite Learning Resources (<=1 hr):** Spark Adaptive Query Execution Docs (https://spark.apache.org/docs/latest/sql-performance-tuning.html#adaptive-query-execution, ~45 mins).
6. **Completion Criteria:** Both salting and AQE eliminate the straggler bottleneck with recorded before/after Spark UI numbers.
7. **Concepts Introduced:** *New:* Data skew, straggler tasks, memory pressure & disk spill, key salting, AQE. *Reused:* Shuffles, aggregations, Spark UI.

#### Day 52 — Fault Tolerance, Speculative Execution, Profiling & Cluster Cost Optimization
1. **Business Context:** An executor crashes mid-shuffle on spot/preemptible compute, and finance asks how much compute our daily Spark batch actually needs.
2. **Task — What I Must Do:** Kill a Docker Spark Worker mid-stage to observe RDD lineage task retries; experiment with `spark.speculation`, `spark.sql.shuffle.partitions`, and executor memory/core sizing (`job cluster` sizing math); document cost-per-million-events for the batch pipeline.
3. **Why Are We Doing This?:** Builds operational confidence in Spark fault recovery, autoscaling concepts, and FinOps sizing.
4. **How Should I Approach It? — HINT:** Observe lineage recomputation and stage retries in Spark UI when a worker container stops.
5. **Prerequisite Learning Resources (<=1 hr):** Spark Configuration & Tuning Docs (https://spark.apache.org/docs/latest/tuning.html, ~45 mins).
6. **Completion Criteria:** Job completes despite killed executor; FinOps report compares partition/memory settings and cost per TB/million events.
7. **Concepts Introduced:** *New:* Executor failures, task retries, speculative execution, job clusters vs all-purpose clusters, autoscaling concepts, Spark FinOps. *Reused:* Spark architecture, Spark UI.

---

### STAGE J — Apache Kafka and Streaming (Days 53–56)

#### Day 53 — Asynchronous Messaging, Topics, Partitions, Brokers & Offsets
1. **Business Context:** During traffic spikes, making the ad-serving API wait synchronously for downstream analytics, fraud scoring, and lakehouse writes causes cascading timeouts.
2. **Task — What I Must Do:** Run a multi-broker Apache Kafka cluster in Docker Compose (KRaft mode—no paid Event Hubs needed); design topics (`ad.impressions`, `ad.clicks`, `ad.quarantine`) with explicit partition keys (`campaign_id`), replication factor, and ISR; produce/consume events and inspect offsets per partition.
3. **Why Are We Doing This?:** Decouples synchronous low-latency ad serving from heavy asynchronous downstream processing while preserving per-campaign ordering within partitions.
4. **How Should I Approach It? — HINT:** Prove empirically that ordering holds *within* one partition (`campaign_id` key) and does *not* hold globally across partitions.
5. **Prerequisite Learning Resources (<=1 hr):** Apache Kafka Documentation — Introduction & Design (https://kafka.apache.org/documentation/#intro, ~50 mins).
6. **Completion Criteria:** Multi-broker topic created; partition distribution & per-key ordering verified.
7. **Concepts Introduced:** *New:* Sync vs async, event-driven architecture, Kafka brokers, topics, partitions, offsets, replication, leader/follower, ISR. *Reused:* Docker, event schemas.

#### Day 54 — Producers, Consumers, Consumer Groups, Rebalancing & Lag
1. **Business Context:** One Python consumer cannot keep up with 20,000 events/sec—and when a second consumer joins or crashes, consumption briefly pauses and duplicates appear.
2. **Task — What I Must Do:** Implement Python Kafka producers tuning `acks` (`0`, `1`, `all`), `linger.ms`/`batch.size`, compression (`lz4`/`zstd`), and `enable.idempotence=True`; run a consumer group of 3 consumers across 6 partitions; kill 1 consumer mid-run to observe **rebalancing**, **consumer lag**, and duplicate reprocessing.
3. **Why Are We Doing This?:** Exposes what actually happens when a Kafka consumer loses its connection during a rebalance.
4. **How Should I Approach It? — HINT:** Monitor consumer group lag (`kafka-consumer-groups.sh`) while killing a consumer before it commits offsets.
5. **Prerequisite Learning Resources (<=1 hr):** Kafka Producer & Consumer Config Docs (https://kafka.apache.org/documentation/#producerconfigs, ~55 mins).
6. **Completion Criteria:** Measured throughput across batch/compression settings; observed rebalance lag & uncommitted-offset replay.
7. **Concepts Introduced:** *New:* Consumer groups, partition assignment, rebalancing, `acks`, batching, compression, idempotent producers, consumer lag, backpressure. *Reused:* Kafka topics/partitions.

#### Day 55 — Delivery Semantics, Transactions, Deduplication & Kafka Connect / Schema Registry
1. **Business Context:** At-least-once delivery during consumer crashes would double-bill advertisers unless AdStream pairs Kafka delivery with end-to-end idempotency or transactions.
2. **Task — What I Must Do:** Contrast at-most-once (auto-commit before process), at-least-once (manual commit after process), and exactly-once business effects (Kafka transactions + idempotent Postgres ledger sink); add a local Schema Registry container + Kafka Connect JDBC/CDC connector demo.
3. **Why Are We Doing This?:** Proves why "Kafka EOS" only covers Kafka-to-Kafka unless the external database sink itself is idempotent.
4. **How Should I Approach It? — HINT:** Inject a crash *after* writing to Postgres and *before* committing the Kafka offset—verify zero duplicate billing.
5. **Prerequisite Learning Resources (<=1 hr):** Confluent Kafka Connect & Semantics Docs (https://docs.confluent.io/platform/current/connect/index.html, ~50 mins).
6. **Completion Criteria:** Crash between DB write and Kafka offset commit yields `0` duplicate billing rows.
7. **Concepts Introduced:** *New:* At-most-once / at-least-once / EOS, Kafka transactions, end-to-end idempotent sinks, Schema Registry, Kafka Connect. *Reused:* Upserts, CDC, consumer groups.

#### Day 56 — Stateful Stream Processing, Event Time, Watermarks & Late Events
1. **Business Context:** Clicks and impressions arrive out of order (mobile offline delays) up to several minutes after `event_time`, yet AdStream needs 1-minute sliding/tumbling campaign windows into Delta Lake.
2. **Task — What I Must Do:** Implement a **PySpark Structured Streaming** job reading from Kafka, computing 1-minute `event_time` campaign aggregations with `withWatermark`, writing to Delta Lake via checkpointing, and testing late events arriving *within* vs *past* the watermark (routing ultra-late events to a late-reconciliation path).
3. **Why Are We Doing This?:** Explains event time vs processing time and why unbounded state without watermarks OOMs streaming clusters.
4. **How Should I Approach It? — HINT:** Inject an event timestamped 2 minutes ago vs 20 minutes ago against a 5-minute watermark and inspect state store behavior.
5. **Prerequisite Learning Resources (<=1 hr):** Spark Structured Streaming Guide — Event Time & Watermarking (https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html#handling-late-data-and-watermarking, ~50 mins).
6. **Completion Criteria:** On-time & within-watermark late events update windows accurately; stream restarts cleanly from checkpoint.
7. **Concepts Introduced:** *New:* Structured Streaming, event time vs processing time, watermarks, late events, stateful stream checkpointing. *Reused:* Spark, Kafka, Delta Lake.

---

### STAGE K — Distributed Systems and Production Engineering (Days 57–60)

#### Day 57 — Containers, Horizontal Scaling, Reverse Proxies & Load Balancing
1. **Business Context:** One FastAPI container caps out under concurrent bidding traffic—we need multiple stateless API replicas behind a reverse proxy.
2. **Task — What I Must Do:** Containerize the AdStream API cleanly (multi-stage `Dockerfile`), run 3 stateless replicas behind Nginx (testing `round_robin` vs `least_conn` and explaining why sticky sessions break horizontal scaling and where CDNs apply—static ad creatives vs dynamic bidding).
3. **Why Are We Doing This?:** Teaches container networking, stateless scale-out, and load balancing without premature Kubernetes complexity.
4. **How Should I Approach It? — HINT:** Stop 1 of the 3 backend replicas during load and watch Nginx route around the dead instance.
5. **Prerequisite Learning Resources (<=1 hr):** Nginx HTTP Load Balancing Docs (https://docs.nginx.com/nginx/admin-guide/load-balancer/http-load-balancer/, ~45 mins).
6. **Completion Criteria:** 3 replicas share traffic; killing 1 replica causes minimal dropped requests and zero lost state.
7. **Concepts Introduced:** *New:* Dockerfiles, horizontal vs vertical scaling, reverse proxies, API gateways, round-robin/least-connections, stateless vs sticky sessions, CDN boundaries. *Reused:* FastAPI, Docker Compose.

#### Day 58 — Redis Caching, Distributed Locks, Rate Limiting & Cache Invalidation
1. **Business Context:** Checking active campaign metadata in Postgres on every bid request adds DB latency, while distributed rate limiting must span all 3 API replicas.
2. **Task — What I Must Do:** Add Redis to Compose: cache active campaign configs with TTL + explicit invalidation on campaign pause/edit; implement a distributed **Token Bucket** / **Leaky Bucket** rate limiter in Redis Lua/atomic ops; explore Redis distributed lock pitfalls (lease expiry vs fencing tokens).
3. **Why Are We Doing This?:** Shows both the massive `p95` speedup of caching AND the real failure modes (stale cache serving paused campaigns, lock expiry split-brain).
4. **How Should I Approach It? — HINT:** Measure `p95` bid-lookup latency DB-direct vs Redis-cached; test what happens if a campaign pauses while cached without invalidation.
5. **Prerequisite Learning Resources (<=1 hr):** Martin Kleppmann *"How to do distributed locking"* (https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html, ~45 mins).
6. **Completion Criteria:** Cache invalidation propagates immediately on pause; distributed rate limit blocks across all 3 API replicas; fencing-token risk documented.
7. **Concepts Introduced:** *New:* Redis, cache invalidation, Token Bucket / Leaky Bucket, distributed locks, CAP theorem & eventual consistency trade-offs. *Reused:* FastAPI, rate limiting, concurrency.

#### Day 59 — Resilience Patterns & Full Observability (Circuit Breakers, Backoff, Metrics/Logs/Traces)
1. **Business Context:** When Postgres or Redis degrades, blind immediate retries create a retry storm that prevents recovery—and without dashboards/traces, engineers fly blind.
2. **Task — What I Must Do:** Implement exponential backoff with jitter + a **Circuit Breaker** (Closed -> Open -> Half-Open) with graceful degradation; wire **Prometheus** metrics (`events_ingested_total`, `budget_overspend_total`, latency histograms), **Grafana** dashboards, structured JSON logs, and OpenTelemetry trace spans + alert rule thresholds.
3. **Why Are We Doing This?:** Proves production reliability engineering—detecting degradation and failing gracefully instead of melting down.
4. **How Should I Approach It? — HINT:** Pause Redis/Kafka via Docker and verify circuit opens fast (`<5ms` fallback/503) instead of piling up 30s hanging requests.
5. **Prerequisite Learning Resources (<=1 hr):** Prometheus Overview (https://prometheus.io/docs/introduction/overview/, ~45 mins).
6. **Completion Criteria:** Grafana shows live latency percentiles (`p50/p95/p99`), error rate, and circuit-breaker state transitions under injected failure.
7. **Concepts Introduced:** *New:* Circuit breakers, exponential backoff + jitter, graceful degradation, metrics/logs/traces, alerting. *Reused:* Logging, Nginx/FastAPI, Docker.

#### Day 60 — Load Testing (`k6`), Chaos Injection, CI/CD & Kubernetes Fundamentals
1. **Business Context:** We need reproducible evidence of system limits, safe automated deployments/rollbacks, and an understanding of when Kubernetes actually becomes justified.
2. **Task — What I Must Do:** Write `k6` load-test scripts (ramp-up, spike, soak) measuring `p50/p95/p99` and max sustainable RPS locally; inject container kills & latency; add a CI/CD build/test/rollback pipeline; author declarative Kubernetes manifests (`Deployment`, `Service`, `HPA`) tested on local `kind`/`k3d` (and write an ADR explaining why Compose sufficed until multi-node scheduling was needed).
3. **Why Are We Doing This?:** Prevents both under-tested systems and resume-driven premature Kubernetes complexity.
4. **How Should I Approach It? — HINT:** Never extrapolate `5M/s` from a laptop—measure exact local RPS and CPU/RAM saturation first.
5. **Prerequisite Learning Resources (<=1 hr):** Grafana k6 Getting Started (https://grafana.com/docs/k6/latest/get-started/) + Kubernetes Basics (https://kubernetes.io/docs/tutorials/kubernetes-basics/, ~55 mins).
6. **Completion Criteria:** Reproducible `k6` baseline + chaos run report; local `kind`/`k3d` deployment + rollback verified.
7. **Concepts Introduced:** *New:* `k6` load testing, chaos/fault injection, CI/CD & rollbacks, Kubernetes fundamentals (Pods, Deployments, Services, HPA). *Reused:* Docker, Prometheus/Grafana.

---

### STAGE L — AdStream Integration and Production Evolution (Days 61–64)

#### Day 61 — Full Pipeline Integration & Realistic Skewed Traffic Simulator
1. **Business Context:** Connect the complete end-to-end AdStream flow: Simulator -> Nginx Gateway -> FastAPI Bidder/Ingestor -> Redis/Postgres Ledger -> Kafka -> Fraud/Streaming/Lakehouse (Bronze/Silver/Gold) -> Billing & Reporting.
2. **Task — What I Must Do:** Wire all services into one reproducible Docker Compose stack with a seeded traffic simulator generating normal, skewed (80/20), duplicate (10%), out-of-order, late, and invalid/fraudulent events simultaneously.
3. **Why Are We Doing This?:** Isolated components often pass unit tests yet fail at integration boundaries (backpressure, serialization, lag).
4. **How Should I Approach It? — HINT:** Run a 10-minute end-to-end soak test and verify an automated reconciliation script compares `Postgres Ledger Spend == Gold Billing Spend`.
5. **Prerequisite Learning Resources (<=1 hr):** Review your own `ARCHITECTURE.md` and `DECISIONS.md` (~30 mins).
6. **Completion Criteria:** Single-command startup; end-to-end invariant check passes (`overspend == 0`, `duplicate_charges == 0`, `quarantined + valid == total_sent`).
7. **Concepts Introduced:** *New:* Full-system integration reconciliation. *Reused:* Every Stage A–K subsystem.

#### Day 62 — End-to-End Chaos Suite (Network Partitions, Broker Kills & Crash Recovery)
1. **Business Context:** Prove that under real partial failures—Kafka broker restart, Spark streaming kill, Redis flush, DB connection saturation—AdStream never loses money or silently corrupts billing.
2. **Task — What I Must Do:** Execute 5 scripted failure scenarios during active `k6` + simulator load, record Recovery Time Objective (RTO), consumer lag recovery, error rates, and post-recovery financial reconciliation variance.
3. **Why Are We Doing This?:** Separates theoretical architecture diagrams from verified fault-tolerant systems.
4. **How Should I Approach It? — HINT:** Log exact timestamps when each fault starts, heals, and when lag returns to `0`.
5. **Prerequisite Learning Resources (<=1 hr):** Principles of Chaos Engineering (https://principlesofchaos.org/, ~30 mins).
6. **Completion Criteria:** All 5 chaos runs recover automatically with `0` financial drift and documented RTO numbers.
7. **Concepts Introduced:** *New:* End-to-end RTO measurement, chaos verification matrix. *Reused:* Chaos injection, Kafka/Spark/Postgres recovery.

#### Day 63 — Bottleneck Hunting & Measured Optimization Loop
1. **Business Context:** Identify the exact first bottleneck limiting local throughput—whether Postgres lock contention, Python JSON parsing, Kafka batching, or Spark shuffle—and prove a measured improvement.
2. **Task — What I Must Do:** Run progressive `k6` load steps until `p99` degrades or errors appear; capture CPU, RAM, disk I/O, Postgres waits, and Kafka lag; change **one variable at a time** (e.g., batch commit / Redis pre-reservation + async ledger / Parquet batching); publish before/after benchmarks.
3. **Why Are We Doing This?:** Demonstrates systematic performance engineering grounded in profiling evidence.
4. **How Should I Approach It? — HINT:** Follow the benchmark checklist: hardware spec, dataset size, concurrency, duration, p50/p95/p99, baseline vs optimized, bottleneck & limitation.
5. **Prerequisite Learning Resources (<=1 hr):** Brendan Gregg USE Method summary (https://www.brendangregg.com/usemethod.html, ~40 mins).
6. **Completion Criteria:** Reproducible benchmark report with at least 2 measured bottleneck-to-fix improvements.
7. **Concepts Introduced:** *New:* USE method (Utilization, Saturation, Errors), one-variable-at-a-time benchmarking. *Reused:* `k6`, `cProfile`, `EXPLAIN ANALYZE`, Prometheus.

#### Day 64 — Capacity Planning & FinOps Math to 5 Million Events/Sec
1. **Business Context:** Leadership asks: *"Your laptop processed `[X]` events/sec. What exact architecture, partition count, cluster size, and monthly dollar cost are required to handle 5,000,000 events/sec at peak—without overpaying?"*
2. **Task — What I Must Do:** Build a math-backed capacity & FinOps model extrapolating from your measured local bytes/event, CPU-ms/event, Postgres TPS/core, Kafka MB/s/broker, Spark cores/GB, and Parquet storage compression—distinguishing **measured local throughput**, **projected cluster capacity**, and **5M/s architectural target** (including caching, batching, partitioning, and regional edge considerations).
3. **Why Are We Doing This?:** Completes the loop from beginner Python to staff-level engineering economics and interview-ready system design defense.
4. **How Should I Approach It? — HINT:** Never extrapolate linearly past lock/network bottlenecks—identify which components scale horizontally (stateless ingestors, Kafka partitions) vs which require sharding/hot-key splitting (single mega-advertiser budget!).
5. **Prerequisite Learning Resources (<=1 hr):** Review your measured Day 37, Day 43, Day 52, Day 63 metrics (~45 mins).
6. **Completion Criteria:** Complete, defensible `CAPACITY_AND_FINOPS.md` report with zero invented measurements; you can defend the entire AdStream design aloud end-to-end.
7. **Concepts Introduced:** *New:* Capacity planning, horizontal sharding math, hot-key splitting, FinOps unit economics ($/1M events). *Reused:* All prior measurements.

---

### Roadmap Completeness Audit

- **Prerequisites verified:** Python (`Days 1–12`) -> SQL/Postgres (`13–20`) -> HTTP/Networking (`21–26`) -> FastAPI/Async (`27–32`) -> Ingestion/CDC/Parquet (`33–37`) -> Azure Basics (`38–40`) -> Hybrid ADF+SHIR (`41–43`) -> Modeling/Delta (`44–47`) -> Spark (`48–52`) -> Kafka/Streaming (`53–56`) -> Distributed Systems/K8s/Chaos (`57–60`) -> Full Integration/FinOps (`61–64`).
- **Subjects explicitly placed where justified:**
  - *Synchronous Bidding vs Asynchronous Analytics:* Placed on Day 30 (sync budget check) and Day 53 (async Kafka decoupling) so Kafka never sits in the synchronous ad-serve critical path.
  - *Kubernetes & CDNs:* Explicitly deferred to Days 57 & 60 (after Docker, statelessness, and bottlenecks are understood) so they solve demonstrated scaling/deployment needs rather than adding premature complexity.
  - *Azure Databricks & Event Hubs:* Audited below and replaced with zero-cost local Spark/Delta/Kafka due to free-tier restrictions.

---

## Part D — Infrastructure & Cost Strategy (Verified Pricing & Limits)

> **Progression:** Local Python (`Days 1–12`) -> Local Docker Postgres/HTTP (`13–37`) -> Azure Free Account + Storage/SQL/ADF+SHIR (`38–43`) -> Local Docker Spark/Delta/Kafka/Redis/Prometheus/k6 (`44–64`).

### Verified Azure Services & Free-Tier Rules (Checked Nov 2026)

| Service | Free Eligibility & Limits (Verified) | What Happens If Exceeded / Hidden Costs | How to Avoid Charges | Zero-Cost Local Alternative |
| :--- | :--- | :--- | :--- | :--- |
| **Azure Free Account** *(General)* | **$200 credit for 30 days** + 12-mo free tier on select services + 65+ always-free services. **India Warning:** *"12 months free services is not available if you sign up directly for Pay-As-You-Go in India"*—you must register via the **Azure Free Account** signup first. | After 30 days (or credit exhaustion), you must convert to Pay-As-You-Go; after 12 months, 12-mo services bill at PAYG rates. | Set **$1 and $5 Azure Budgets + email alerts** on Day 38; delete test resources immediately after Stage G. | Local Docker Compose stack. |
| **Azure SQL Database (Free Offer)** | **Always Free (per subscription, up to 10 DBs):** **100,000 vCore seconds/month** serverless compute + **32 GB data** + **32 GB backup**. Resets monthly. | Can configure to **auto-pause** when free limit is hit (or switch to PAYG if unchecked—**always select "Auto-pause when monthly free limit reached"**). | Select Serverless Free Offer + enable the hard auto-pause toggle at limit. | Local PostgreSQL in Docker (`postgres:16`). |
| **Azure Blob Storage / ADLS Gen2** | New free accounts get **5 GB LRS hot Blob storage + 20K reads + 10K writes/mo for 12 months**. | **Hidden Trap:** Enabling **ADLS Gen2 Hierarchical Namespace** bills extra metadata storage & directory-rename operations; exceeding 5 GB or using GRS/ZRS bills immediately; **outbound internet egress** beyond free allowance costs per GB. | Use **Standard LRS** only, keep test datasets <100 MB, delete containers after Day 43. | **Azurite** (Azure Storage emulator) or **MinIO** (S3-compatible) in Docker. |
| **Azure Data Factory (ADF) + SHIR** | **First 1,000 pipeline orchestration activity runs/month free**; **Self-Hosted IR free up to 5 nodes**. | **Hidden Traps:** (1) Scheduled polling triggers burn runs; (2) **Cloud IR Data Movement costs $0.25/DIU-hour**; (3) **Mapping Data Flows cost ~$0.273/vCore-hour** (NOT free!). | Use manual triggers only, keep total runs <100/mo, **never enable Mapping Data Flows**, use SHIR for local compute. | Python ingestion scripts + `cron`/Dagster/Prefect in Docker. |
| **Azure Functions** | **Consumption Plan Always-Free Grant:** **1,000,000 requests + 400,000 GB-s/month** per subscription (Flex Consumption: 250K reqs + 100K GB-s). | Exceeding free grants bills $0.20/million executions + $0.000016/GB-s; linked Storage Account logs also consume minor Blob storage. | Keep triggers manual/bounded and clean up logs. | Local Python / FastAPI containers. |
| **Azure Event Hubs** *(DO NOT USE)* | **No permanent free tier.** Basic starts at ~$0.015/TU-hr (~$11/mo continuously running) + ingress events; Standard ~$0.03/TU-hr (~$22/mo). | Bills hourly the moment a namespace exists, even with zero traffic. | **Do not provision Event Hubs** once 30-day $200 credit ends. | **Self-hosted Apache Kafka (KRaft)** or Redpanda in Docker. |
| **Azure Databricks** *(DO NOT USE)* | **No free tier.** Even the 14-day Premium Free Trial only waives **DBUs**—you **still pay hourly for Azure VMs, Managed Disks, and Public IPs**. | Running a small 2-node cluster even a few hours/day costs real money immediately. | **Do not provision Azure Databricks.** | **Local Apache Spark + PySpark + `delta-spark`** in Docker. |
| **Private Endpoints / VMs / NAT Gateways** | **Not always free** (Private Endpoints charge hourly + per GB processed). | Silent hourly burn even when idle. | Verify cost = `$0` before creating; delete immediately after any 10-min test. | Local Docker networks. |

---

## Part E — First Assignment: Day 1

### Day 1 — Advertiser & Campaign Entities (Variables, Data Types, Operators)

* **1. Business Context:** AdStream needs an in-memory representation of a single advertiser's campaign and a reliable way to track spend and performance metrics (CTR, CPC, CPM, remaining budget) without losing fractional cents/micros to floating-point rounding errors.
* **2. Task — What I Must Do:**
  1. Create a fresh folder for your clean from-scratch start (e.g., `adstream_scratch/day01_campaign_basics.py` inside your workspace—keep it separate from any old files).
  2. Define variables representing: `advertiser_id` (`str`), `campaign_id` (`str`), `campaign_name` (`str`), `is_active` (`bool`), `daily_budget_micros` (`int`, where `$1.00 = 1,000,000 micros`), `spent_micros` (`int`), `impressions` (`int`), and `clicks` (`int`).
  3. Compute and print:
     * `remaining_budget_micros` and `remaining_budget_usd`
     * `ctr_percent` (`(clicks / impressions) * 100`)
     * `cpc_micros` (`spent_micros // clicks` or `float`) and `cpm_micros` (`(spent_micros * 1000) // impressions`)
  4. Experiment inside the same script (or Python REPL) with `0.1 + 0.2 == 0.3` vs integer micros addition (`100_000 + 200_000 == 300_000`) and write a 3-line comment in your code explaining why floats drift on financial sums.
* **3. Why Are We Doing This?:** Every subsequent billing engine, SQL ledger, and reconciliation test relies on deterministic integer-unit money arithmetic.
* **4. How Should I Approach It? — HINT:**
  * Use underscores in large integers for readability (`10_000_000` = `$10.00`).
  * Test what happens when `impressions = 0` or `clicks = 0`—note the `ZeroDivisionError` (we will guard against it systematically starting Day 2, or you can observe it explicitly today).
  * Do **not** wrap this in classes, functions, JSON files, or FastAPI yet—keep strictly to variables, basic types, operators, and `print(f"...")`.
* **5. Prerequisite Learning Resources (<=1 hr):**
  * **Official Python Tutorial — Ch. 3 ("An Informal Introduction to Python"):** https://docs.python.org/3/tutorial/introduction.html (~40 minutes; read Sections 3.1.1 Numbers and 3.1.2 Text).
* **6. Completion Criteria:**
  * You paste/share your `day01_campaign_basics.py` code and its terminal output.
  * You can explain in your own words: (a) what each data type (`int`, `float`, `str`, `bool`) is storing, (b) the difference between `/` and `//`, and (c) why `0.1 + 0.2` behaves differently from integer micros.
* **7. Concepts Introduced:**
  * *New:* Variables, `int`, `float`, `str`, `bool`, arithmetic (`+`, `-`, `*`, `/`, `//`), f-strings, integer minor-unit money (`micros`).
  * *Reused:* None.

---

## Persistent Progress Ledger

* **Completed assignments:** None yet.
* **Current assignment:** Day 1 — Advertiser & Campaign Entities (`adstream_scratch/day01_campaign_basics.py`).
* **Pending assignments:** Days 2–64.
* **Concepts mastered:** Pending Day 1 review.
* **Concepts requiring revision:** None yet.
* **Current blockers:** None.
* **Next assignment:** Day 2 — Campaign Eligibility & Event Batch Simulation (locked until Day 1 passes).
