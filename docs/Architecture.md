# AdStream — Architecture (v0.1)

**Version:** v0.1, 13 Nov 2026. Derived from the AdStream charter, the Day-1 estimation (arithmetic verified) and the owner decisions recorded in `docs/Decisions.md` (ADR-001 to ADR-011). Sections labelled Proposed are the mentor's derivation and still need owner review.

**Rule:** this is the single canonical architecture document. Stack, schema and scope changes go through `docs/Decisions.md` first.

| Label | Meaning |
|---|---|
| Fixed | Stated in the charter. Changes only through an ADR. |
| Decided | Chosen by the owner and recorded in `docs/Decisions.md`. |
| Proposed | Derived by the mentor. Needs owner approval. |
| Open | Not decided yet. See section 12. |
| Owner | Draft to be rewritten in the owner's own words. |

Component status: **designed** (on paper only), **built** (code exists, tests pass), **measured** (benchmarked, with raw data and a repro command). Nothing is measured yet.

---

## 1. Purpose and scope [Fixed]

AdStream is a platform-agnostic advertising data infrastructure platform. It ingests, processes, transforms, enriches, stores, analyzes and serves advertising data from many ecosystems: Google Ads-like, YouTube-like, Amazon Ads-like, Meta-like, retail media, programmatic exchanges and independent publishers. Data is synthetic at first. Real integrations are separate connector implementations that need authorized APIs, exports or feeds.

Out of scope for now: real external integrations, an end-user UI, running a real auction or bidder (AdStream exposes the synchronous budget API and the simulator plays the decision component that calls it, see ADR-003), Kubernetes, and any paid cloud service (needs explicit approval).

## 2. Problem statement [Owner]

*Draft derived from the charter. Rewrite in your own words, 8 lines max.*

Advertisers, agencies and publishers need trustworthy answers about advertising performance and money: impressions, clicks, CTR, spend, remaining budget, publisher revenue, attribution and financial liability. The data comes from many ecosystems that emit events in different shapes, at very high rate (design target: 1M events/s at peak), with duplicates, late and out-of-order arrivals, skewed keys, missing fields, schema changes and fraudulent traffic. AdStream must preserve every event, turn it into correct canonical data and financial records, and serve fresh analytics at the lowest infrastructure cost, with cost per million events measured rather than assumed. A wrong number is worse than a late number: repeated delivery must never repeat a financial effect, and nothing may be silently dropped.

## 3. Scale and requirements

### 3.1 Design target [Fixed]

**1,000,000 events/s peak ingestion.** This is an architectural scale-out target, not a claim about the local machine. We benchmark one partition or worker honestly, then model the infrastructure needed to reach the target. No performance number is stated without evidence (workload, hardware, command, raw data).

### 3.2 Derived capacity numbers (from Task 1A, arithmetic verified)

| Quantity | Value | Derivation |
|---|---|---|
| Peak rate | 1,000,000 events/s | design target |
| Average rate | 400,000 events/s | assumption |
| Average event size | 600 bytes raw JSON | assumption |
| Peak payload throughput | 600 MB/s = 4.8 Gbps | 1,000,000 × 600 B, then ×8 for bits. Payload only: excludes protocol overhead and replication |
| Events per day (average) | 34.56 billion | 400,000 × 86,400 |
| Raw volume per day | 20.736 TB | 34.56 B × 600 B |
| Compressed volume per day | 4.1472 TB | assumed 5:1, to be replaced by a measured ratio |
| One copy, 30 days | about 124.4 TB | 4.1472 × 30 |
| One copy, 365 days | about 1.51 PB | 4.1472 × 365 |

All volumes are a single copy, before Kafka replication, Bronze/Silver/Gold copies and any retention policy. The three assumptions (average rate, event size, compression) are placeholders until measured.

### 3.3 Quality requirements [Proposed]

| Quality | Requirement | Verified by |
|---|---|---|
| Financial correctness | Zero duplicate financial effects. The ledger reconciles to the event log with zero unexplained variance. | Financial correctness tests, reconciliation job |
| Durability | An acknowledged event is never lost. | Failure-injection tests |
| Completeness | Nothing is silently dropped. Every rejected event is quarantined with its reason and raw payload. | Contract tests, quarantine counts |
| Throughput | 1M events/s via horizontal partitioning. The per-partition rate is measured, not assumed. | Load tests (k6), benchmark reports |
| Freshness | Near-real-time aggregates within a lag target. TBD after first measurements. | End-to-end lag metric |
| Latency | p50/p95/p99 ingestion latency targets. TBD after first measurements. | Load tests |
| Budget enforcement | Zero overspend for spend authorized through the reserve API. Low reserve latency: the p99 target is set after a baseline measurement. | Concurrency tests, latency benchmark |
| Multi-currency | Amounts keep their currency. Every conversion records the rate version used. | Financial correctness tests |
| Recovery | Replay and reprocess without duplicates. Recovery time is measured. | Failure-injection and replay tests |
| Security | Validated input, authenticated ingestion, pseudonymous user ids, secrets kept out of the repository. | Security checks, code review |
| Cost | Cost per million events and per TB processed is reported for every pipeline. | FinOps metrics |

Correctness requirements are absolute. Performance numbers are set only after measurement.

### 3.4 What the numbers imply [Proposed]

- **CPU:** at 1M events/s, one core has 1 µs per event. With C cores the per-event budget is C µs. Batching, compact serialization and partitioned parallelism are design requirements, not later optimizations.
- **Network and disk:** 600 MB/s is payload only. Kafka disk and inter-broker traffic grow with the replication factor, and every consumer group adds read traffic.
- **The money path does not see 1M events/s.** The asynchronous ledger sees billable events: impressions under CPM billing, clicks under CPC, conversions under CPA. The synchronous reserve path sees every spend decision that needs a budget check, and its rate depends on the decision component and the reservation point (O-13). Both depend on the traffic mix and the pricing-model mix (ADR-006).

## 4. Invariants and failure modes [Owner]

*Draft derived from the charter. Rewrite the invariants in your own words and add two failure modes of your own.*

**Invariants** (things that must be true whatever fails):

1. Repeated delivery of an event never creates a repeated financial effect.
2. An acknowledged event is never lost.
3. A rejected event is never silently dropped: it is quarantined with its reason and raw payload.
4. Raw source payloads and source identifiers are preserved unchanged.
5. Spend authorized through the reserve API never exceeds a campaign's budget (zero slack, ADR-003). Spend that external ecosystems report after the fact cannot be refused: it is recorded and any overrun is flagged.
6. After reconciliation, the ledger equals what the event log implies.
7. Replaying or reprocessing the same events gives the same result.
8. Money is exact: integer micros plus a currency code, never floats. Every currency conversion records the rate version used.
9. Every published metric can be traced to the source events behind it.

**Failure modes:**

| Failure mode | Invariant at risk | Defence (Proposed) | Test |
|---|---|---|---|
| Sender retries after a timeout, or a consumer replays after a restart | 1 | Unique `event_id`, unique constraint in the ledger, idempotent consumers | Send one click 3 times, expect one charge |
| Broker or process dies after acknowledging | 2 | Acknowledge only after a durable write, consumers commit offsets after processing | Kill a process during a load run, count events |
| Malformed or unknown-shape payload | 3, 4 | Validate at the edge, quarantine with raw payload | Invalid-payload contract tests |
| Concurrent requests spend the same budget | 5 | Atomic reservation (one conditional update or an exclusive budget slice), never read-then-write | N parallel spends, final spend never exceeds the budget |
| Late or out-of-order events (a click before its impression) | 6, 7 | Store event time and ingestion time separately, use watermarks, apply corrections as new entries | Simulator with injected lateness |
| Cache or stream state drifts from the ledger | 6 | Periodic reconciler against the ledger | Inject drift, expect detection |
| Hot keys (one advertiser or publisher dominates) | throughput | Choose keys from measured skew, salt hot keys if needed | Skewed-workload benchmark |
| A source changes its schema | 3, 4 | Versioned contracts, tolerant reader, quarantine on break | Contract tests per version |
| An event schema changes incompatibly | 3, 7 | Registry compatibility check rejects the change at publish time, old data stays readable | Compatibility tests in CI |
| An FX rate is stale, missing, or moves between reserve and commit | 5, 8 | Versioned rates with a staleness bound, the reservation locks its rate, commit cannot exceed the reserved amount | Rate-move and missing-rate tests |

## 5. System architecture

### 5.1 Diagram [Fixed layers, Proposed flows]

```text
 A  SOURCES  (synthetic generator + source-shaped adapters)
        |  events: duplicates, late, malformed, skewed
        v
 B  INGESTION  (FastAPI + Pydantic)
    authenticate -> adapt -> validate contract -> keep raw payload
        |                          |
        | valid                    | invalid
        |                          v
        |                   QUARANTINE (reason + raw payload)
        v
 C  KAFKA  (topics by event family; replicated; replayable)
        |
        +---------------------+----------------------+
        v                     v                      v
 F  BRONZE writer       D  REAL-TIME           G  LEDGER consumer
    (immutable raw)        dedupe, fraud flags,   (idempotent writes)
        |                  enrich, live aggs            |
        v                        |                      v
 E  BATCH (Spark)                |              G  POSTGRES (+ Redis)
    Bronze -> Silver -> Gold     |                 budgets, reservations,
        |                        |                 ledger, billing
        +------------+-----------+----------------------+
                     v
             RECONCILIATION
             (ledger vs Silver/Gold vs event log; idempotent repair)
                     |
                     v
 H  SERVING  (APIs, analytical SQL)

 I  FINOPS AND OBSERVABILITY covers every box
    (Prometheus, Grafana, k6, benchmark logs)
```

The synchronous budget path (G1 and G2) is drawn in section 6.1.

### 5.2 Components [Fixed]

| ID | Component | Responsibility (from the charter) | Why it exists | Tech | Status |
|---|---|---|---|---|---|
| A | Sources | Google/YouTube/Amazon/Meta/retail-media/exchange-like feeds plus a deterministic synthetic generator (seeded; skew, duplicates, late events, nulls, schema drift) | Realistic, reproducible, failure-rich data before any real feed | Python | designed |
| B | Connector and ingestion | Source adapters, API and batch ingestion, schema validation, contract enforcement, serialization, authentication, error handling, quarantine, raw payload preservation | Keeps bad data out of the pipeline without losing it | FastAPI, Pydantic | designed |
| C | Event transport | Durable topics by event family, partitions, producer coordination, consumer groups, offsets, replication, ordering within a partition, retry and replay, lag monitoring | Absorbs bursts, decouples producers from consumers, allows replay | Kafka | designed |
| D | Real-time processing | Deduplication, fraud detection, stream enrichment, live campaign aggregates, event correlation, budget-state updates, near-real-time reporting | Fresh numbers before batch completes | PySpark Structured Streaming (where appropriate) | designed |
| E | Batch processing | Historical transforms, large-scale enrichment, attribution, reconciliation, historical aggregation, reprocessing, analytical preparation | Complete, authoritative answers, late data corrected | Spark | designed |
| F | Lakehouse | Bronze (immutable raw plus metadata), Silver (validated, canonical, deduplicated, enriched, conformed dimensions), Gold (campaign performance, spend, publisher revenue, attribution, conversions, finance) | Cheap durable history and clear quality tiers | Parquet, Delta Lake | designed |
| G | Financial and transactional | Budgets, campaign allocations, spend reservations, billing records, ledgers, publisher obligations, refunds and adjustments, reconciliation | Money needs transactions and exactness | PostgreSQL, Redis | designed |
| G1 | Budget service | Synchronous reserve, commit and release against campaign budgets, in the campaign's currency, with zero overspend and low latency. Journals every reservation event | Strict budget enforcement must not wait on the event pipeline | Strategy chosen by measurement in S2 (Postgres and/or Redis) | designed |
| G2 | FX rates | Versioned exchange rates with effective times and sources, a low-latency cache with a staleness bound, explicit recorded conversions | Multi-currency budgets and reports stay exact and auditable | PostgreSQL, in-process cache | designed |
| R | Schema registry | Versioned event schemas, compatibility rules, rejection of incompatible changes | Safe schema evolution and replayable history | Product chosen in S1 (O-11), added to the stack by ADR-004 | designed |
| H | Analytical serving | Analytical queries, campaign, advertiser, publisher, attribution and revenue reporting, APIs for consumers | Answers the business questions | FastAPI, SQL (default engine: Spark SQL over Gold, ADR-007) | designed |
| I | FinOps and observability | CPU, memory, disk, network, Kafka throughput and lag, Spark metrics and shuffle, storage and compression, query and processing latency, cost per million events and per TB | Every optimization needs a measured before and after | Prometheus, Grafana, k6 | designed |

### 5.3 Data flow [Proposed]

**Synchronous path (separate from the event path):** a decision component reserves budget through G1 before delivery, then commits or releases (section 6.1). It never waits on Kafka.

**Event path:**

1. Sources (A) send events, singly or in batches, to ingestion (B).
2. B authenticates, adapts each event to the common envelope and validates it against its registered schema (R). Invalid events go to quarantine with the raw payload and the reason. Valid events are serialized and published to Kafka (C). The caller is acknowledged only after the broker confirms a durable write.
3. Independent consumer groups read C: the Bronze writer, the real-time processors and the ledger consumer.
4. The Bronze writer appends raw events plus ingestion metadata to the lakehouse (F). Bronze is never modified.
5. Real-time processing (D) deduplicates within a bounded window (ADR-009: as long as the watermark delay, using Spark's built-in streaming state), flags fraud, enriches and updates live aggregates. These numbers are provisional. A duplicate that escapes the window is caught by Silver and, for money, by the ledger.
6. The ledger consumer writes billable events and the budget service's reservation events (the `finance` topic) to the financial layer (G) idempotently, keyed by `event_id`. The ledger is the authoritative place for financial effects.
7. Batch processing (E) turns Bronze into Silver (validated, canonical, deduplicated) and Gold (campaign, advertiser and publisher metrics, attribution, finance). Gold is authoritative once the lateness window closes.
8. Reconciliation compares the ledger with Silver/Gold and the event log, reports variance, and repairs with idempotent adjustments.
9. Serving (H) answers queries from Gold, live aggregates and the ledger.
10. FinOps and observability (I) measure every step.

### 5.4 Design principles [Proposed]

Each principle exists because of a failure it prevents. We do not add a component or rule without one.

| # | Principle | Failure it prevents |
|---|---|---|
| P1 | Validate at the edge and quarantine instead of dropping. | Malformed data corrupting pipelines or vanishing |
| P2 | Kafka is a transport with finite retention. Bronze is the durable system of record for raw events. | Losing the ability to replay, paying to keep everything in Kafka |
| P3 | Delivery is at-least-once. Correctness comes from idempotent writes, not from trusting delivery. | Duplicate effects from retries and replays |
| P4 | Deduplicate in three places with different guarantees: stream (bounded window, best effort), Silver (complete, for analytics), ledger (authoritative, for money). | Unbounded state in the stream, duplicate charges |
| P5 | Streaming numbers are provisional. Gold and the ledger are authoritative after the lateness window. Corrections are new entries, never edits. | Reports that silently change, lost audit trail |
| P6 | Budget decisions never wait on Kafka consumers. | Consumer lag turning into overspend |
| P7 | Event time and ingestion time are always stored separately. | Events landing in the wrong day or window |
| P8 | Partition for parallelism, and measure skew before choosing keys. | Hot partitions limiting throughput |
| P9 | Redis is never the source of truth for money. | Losing balances when a cache restarts |
| P10 | Budget enforcement is strict and synchronous: reserve before delivery, commit or release after, reservations expire. | Overspend and stranded budget |
| P11 | Contracts live in the registry. Incompatible changes are rejected at publish time. | Silent schema breaks, unreadable history |
| P12 | Every currency conversion records the rate version used. | Unexplainable money differences, drifting reports |
| P13 | The edge is sized for peak, consumers for average plus catch-up, and money has its own lane. | Cost explosion, billing delayed by an analytics backlog |

### 5.5 Traffic absorption and peak handling (ADR-008) [Decided]

Peak is 2.5 times the average (1,000,000 against 400,000 events/s). Each layer has its own rule:

1. **Edge (ingestion):** stateless and horizontally scalable, sized for the peak. If it is ever overloaded it answers `429` with `Retry-After`. Senders retry with the same `event_id`, so nothing is silently dropped and retries are harmless (P3).
2. **Queue (Kafka):** absorbs bursts. Brokers and partitions are sized for the peak write rate, and retention for the largest expected backlog plus the replay window.
3. **Consumers:** sized between the average and the peak. During a peak, lag grows. After it, consumers drain the backlog at capacity minus arrival rate.

Money gets its own lane: the `finance` topic has its own consumers and capacity, so an analytics backlog cannot delay billing. The synchronous budget path does not use Kafka at all (P6).

Illustrative arithmetic. Assumptions: one 30-minute peak per day, constant rates, 600-byte events, payload only, single copy, first-in first-out. Real peaks will be measured.

| Consumer capacity | Backlog at end of peak | Queue storage | Worst lag | Time to drain |
|---|---|---|---|---|
| 500,000 events/s | 900 million events | 540 GB | 30 min | 150 min |
| 600,000 events/s | 720 million events | 432 GB | 20 min | 60 min |
| 800,000 events/s | 360 million events | 216 GB | 7.5 min | 15 min |

Consumer capacity is a cost-versus-freshness dial. Choosing it needs a freshness target (O-14). Last resort only: explicit, weighted sampling of bid-level events, recorded as sampled and never applied to money, delivery or conversion events. A scaled-down experiment with a rate-limited consumer (slices S3 and S7) will validate the arithmetic.

## 6. Financial correctness (money path) [Proposed]

- The ledger is append-only. Balances are derived from entries, never edited.
- Every entry carries `event_id`, campaign, account, amount in integer micros, currency code, `occurred_at`, `recorded_at` and an entry type (reserve, commit, release, adjustment, refund).
- Idempotency: a unique constraint per event and ledger leg, so a repeated event cannot add a second entry.
- Reservations follow reserve, then commit or release. An abandoned reservation expires and is released, otherwise budget is stranded.
- Budgets are enforced synchronously (ADR-003). A reservation is atomic (one conditional update or an exclusive budget slice), never read-then-write. Section 6.1 has the design.
- Late events, refunds and fraud reversals are new compensating entries.
- Reconciliation compares the ledger with the event log and Gold. Variance must be zero or explained.
- Currency is stored per entry (ADR-005). Conversions are explicit entries that record the rate version. Section 7.5 has the rules.
- Spend that external ecosystems report after the fact cannot be refused. It is recorded as an entry, and any overrun it causes is flagged, not hidden.

### 6.1 Synchronous reservation path [Proposed] (ADR-003)

```text
 DECISION COMPONENT (the simulator plays this role)
        |  1. reserve(campaign, amount, currency)      synchronous, low latency
        v
 G1  BUDGET SERVICE ------- reads -------> G2  FX RATE CACHE
        |                                       (versioned, bounded staleness)
        |  2. approved or rejected, returned to the caller
        |  3. commit or release after delivery or timeout
        |
        +-- journals every reservation event durably
                |
                v   asynchronous, off the critical path
           KAFKA `finance` topic -> LEDGER consumer -> Postgres ledger
```

Requirements:
- Zero overspend.
- Low latency. The p99 target is set after a baseline measurement.
- A restart never loses or double-counts a reservation: state is rebuilt from the journal and the ledger.
- No dependency on Kafka consumers.

Strategy candidates. The strategy is chosen by measurement in slice S2, not by opinion:

| Strategy | Idea | Strength | Risk |
|---|---|---|---|
| Central atomic update in Postgres | One conditional update on the campaign's balance row | Simple, durable, strictly correct | Contention on hot campaigns, a network round trip per call |
| Atomic script in Redis | Check and decrement in one script on hot state | Very fast | State is lost on restart unless rebuilt from the journal. Redis is never the source of truth (P9) |
| Exclusive budget slices | Hand each shard a slice of the remaining budget, with the sum of slices never above the budget | Fast local checks, still zero overspend | Budget can be stranded in a slice, needs rebalancing |

Strictness has a price: "never overspend" can mean under-delivery, because budget is held by pending reservations and wins are rejected once the budget is exhausted. Reservations therefore expire and are released. Whether to reserve at bid time or at win time is open (O-13).

## 7. Data architecture

### 7.1 Lakehouse tiers [Fixed]

| Tier | Content |
|---|---|
| Bronze | Immutable source data: original payloads, source metadata, ingestion metadata |
| Silver | Validated data, canonical models, deduplicated events, enriched records, conformed dimensions |
| Gold | Campaign performance, advertiser spend, publisher revenue, attribution, conversion metrics, financial analytics, business reporting models |

### 7.2 Kafka topics [Proposed families, keys decided in ADR-008]

Topics are grouped by event family, never per field or per advertiser (charter rule):

| Topic family | Events |
|---|---|
| `auction` | Ad requests, bids, auction wins and losses |
| `delivery` | Impressions, clicks, video starts, quartiles and completions |
| `conversion` | Add-to-cart, purchase, conversion |
| `finance` | Budget consumption, billing, adjustments |
| `quarantine` | Rejected events with reason and raw payload |

**Keys (ADR-008):** `auction`, `delivery` and `conversion` events are keyed by the request id, so all events of one ad request stay together and in order, and load spreads evenly across partitions. `finance` events are keyed by `campaign_id`, so each campaign's reservation lifecycle stays ordered. A hot campaign gets a salted key only if measured skew demands it. Ordering is guaranteed only within a partition. Final keys wait for the data contracts (step 3).

### 7.3 Event envelope and entities [Proposed, finalized in the data contracts step]

Every event shares: `event_id` (unique, survives retries), `event_type`, `schema_version`, `source` and `source_event_id`, `occurred_at` (event time, UTC), `received_at` (ingestion time, UTC). Money is integer micros plus a currency code. Source-specific fields live in an extension object, and the original payload is preserved. Schemas are registered and versioned (section 7.4).

Core entities: Advertiser, Campaign, Ad, Publisher, App or Site, Placement, and a pseudonymous User. The rule for relationships is that the "many" side stores the id of the "one" side (a Campaign carries `advertiser_id`, an Ad carries `campaign_id`). Impressions, clicks, conversions, auctions and bids are events, not entities.

### 7.4 Schema registry and evolution (ADR-004) [Proposed rules]

- Every event type has a registered, versioned schema. The registry is the source of truth for contracts.
- Allowed change: add an optional field with a default. Not allowed: rename, retype or remove a field. The registry rejects anything else at publish time.
- Proposed compatibility mode: full and transitive, so old and new readers can read every version, including when old data is replayed.
- Sources send JSON. Ingestion validates it and publishes a compact binary format (Avro or Protobuf, O-11) to Kafka. The original payload stays in Bronze unchanged.
- The 600-byte figure in section 3.2 is raw JSON at the edge. Sizes on the wire and in storage will differ and must be measured.
- Contract tests run the compatibility check in CI.

### 7.5 Currency and FX (ADR-005) [Proposed rules]

- Every amount is `amount_micros` (an integer) plus `currency` (an ISO 4217 code). There is no fixed currency.
- FX rates are versioned data: base, quote, rate, effective time, source. They are never overwritten.
- A conversion is explicit. It stores the original amount, the converted amount and the rate version.
- Budgets are held in the campaign's currency. A reservation converts the spend amount into that currency using the current rate, rounds up, and locks the rate. Commit can never exceed what was reserved.
- Reporting converts "as of" a rate version. Revaluing changes reports, not the ledger.
- Development rate source: a deterministic, seeded synthetic series from the simulator. A real feed, such as published central bank reference rates, is a later connector. Details: O-12.

### 7.6 Time zones (ADR-011) [Decided]

- Timestamps are UTC instants.
- Each advertiser account has a reporting time zone (an IANA name such as `Asia/Kolkata`).
- Gold keeps 15-minute UTC buckets, so every current time zone, including half-hour and 45-minute offsets, rolls up to exact local days. This works for additive metrics. Distinct counts are computed from event-level data.

### 7.7 Analytics serving and attribution (ADR-007, ADR-010) [Decided]

- Gold models are designed from the charter's business questions: CTR, CPC, CPM, spend, remaining budget, ROAS, publisher revenue, suspicious activity, and breakdowns by country, product, device, audience, placement and time.
- Default engine: Spark SQL over the Gold tables, so no new tool. Revisit only if measurements show a latency or cost problem.
- Attribution: last click within a configurable window. The conversion, click and impression chain stays traceable (invariant 9). Other models arrive later through an ADR.

## 8. Technology decisions [Fixed]

| Need | Choice | Note |
|---|---|---|
| Language | Python | |
| API and validation | FastAPI, Pydantic | |
| Transactional store | PostgreSQL | Ledger and budgets |
| Low-latency state | Redis | Only where appropriate, never the source of truth for money |
| Event streaming | Apache Kafka | |
| Stream processing | PySpark Structured Streaming | Where appropriate |
| Batch processing | Apache Spark | |
| Lake storage | Parquet, Delta Lake | |
| Schema registry | Product chosen in S1 (O-11) | Added by ADR-004, not in the original charter stack |
| Analytics serving | Spark SQL over Gold (default, ADR-007) | Revisit only if measurements show a problem |
| Load testing | k6 | |
| Deployment | Docker, Docker Compose | Kubernetes deferred until containers, processes and networking are understood |
| Observability | Prometheus, Grafana | |
| Testing | pytest | |
| Version control | Git | |

Rule: the stack changes only through an ADR (existing decision, problem, alternative, migration impact, owner approval).

**Development machine (measured 13 Nov 2026):** Intel Core i5-1245U (10 cores, 12 threads), 15.6 GB RAM, about 269 GB free disk. Installed: Python 3.14.10, Git, WSL. Not installed yet: Docker, Java (Spark needs it), uv.

Consequences:
- The full stack cannot run at once on this machine. Tools are introduced one at a time, when a slice needs them.
- Benchmarks are per component, then scaled by arithmetic. A local single-broker Kafka has no replication, so broker-loss durability cannot be tested locally.
- No cloud spend without explicit approval.

## 9. FinOps and observability [Fixed]

Measure: events/s, bytes/s, data processed, scanned and shuffled, compression ratio, storage, CPU time, memory, disk and network I/O, processing latency, recovery time, cost per million events, cost per TB processed.

Rules:
1. Every optimization has a before and after on an identical workload.
2. No performance claim without evidence: workload, hardware, command, raw data.
3. Local hardware utilization is reported separately from estimated cloud cost, and every price assumption is dated.

Capacity method [Proposed]: measure the rate per core or partition, then derive cores and partitions for the 1M events/s target, then add storage (with the measured compression), network and replication, then price it with explicit assumptions, and report cost per million events and per TB.

## 10. Testing strategy [Fixed]

| Test type | What it proves |
|---|---|
| Unit | Single functions behave correctly, including invalid input |
| Contract | Event shapes are enforced and versioned |
| Integration | Components work together (API to Kafka to ledger) |
| Load | Throughput and latency percentiles under controlled load |
| Failure injection | Crashes, retries, duplicates and lateness do not break invariants |
| Data quality | Completeness, uniqueness and referential checks on every tier |
| Financial correctness | Budgets, ledger and reconciliation hold their invariants |
| Performance benchmark | Reproducible numbers for the cost model |

## 11. Design progress, build order and status

### 11.1 Design progress [Proposed]

| Step | Artifact | Status |
|---|---|---|
| 1 | Problem statement and requirements | Draft in sections 2 and 3 |
| 2 | Invariants and failure modes | Draft in section 4 |
| 3 | Data contracts (entities and events) | Proposed logical v0.1 in [DataContracts.md](./DataContracts.md); owner review pending. S1 pilot built for click, impression and conversion, the other 13 event types are pending |
| 4 | Architecture map | v0 in section 5 |
| 5 | Sequence diagrams for ingest, reserve budget, late event, reconcile and replay | Not started |
| 6 | Storage design (Postgres ledger, Bronze/Silver/Gold, grain, partitioning) | Not started |
| 7 | Capacity and cost model | Started in section 3.2 |
| 8 | Class and module design | Per component, just before coding it |

### 11.2 Build order: vertical slices, money path first (ADR-002) [Proposed]

| Slice | Content |
|---|---|
| S0 | Foundations: Python environment, pytest, metric functions (in progress) |
| S1 | Contracts: Pydantic event models, schema registry, validation, quarantine rules |
| S2 | Money path: budget service (synchronous, strict), FX rates, Postgres ledger, idempotency, concurrency and latency tests, strategy comparison |
| S3 | Ingestion: FastAPI to Kafka |
| S4 | Bronze and Silver: raw preservation, deduplication |
| S5 | Real-time: Structured Streaming aggregates, late-event handling |
| S6 | Gold, reconciliation, serving |
| S7 | FinOps: observability, load tests, capacity model |

Each slice ends with tests, a documented failure scenario and, where relevant, measured numbers.

Proposed refinement: S2 is built twice. S2a runs in plain Python with in-memory fakes behind the same interfaces (simulator, validation, budget service, ledger, reconciliation), which proves the flow and the invariants but says nothing about performance. S2b swaps the fakes for Postgres in Docker, then adds concurrency and latency tests.

### 11.3 Component status

| Component | Status | Note |
|---|---|---|
| Python environment and pytest | built | Virtual environment kept outside OneDrive |
| Metrics library: `compute_ctr` | built | Tests incomplete. CPC and CPM not started |
| Contract validation (S1 pilot): `src/adstream/contracts` | built | Click, impression and conversion (3 of 16 event types), quarantine record and `validate_event`. Registry and serialization format (O-11) not started |
| A to I, G1, G2, R (section 5.2) | designed | Nothing else exists yet |

## 12. Decision log

Status: **Decided** (the owner chose it, recorded in `docs/Decisions.md`), **Proposed** (a default is proposed and waits for owner approval), **Open** (not decided yet).

| ID | Decision | Status | Outcome or default |
|---|---|---|---|
| O-1 | Budget enforcement mode | Decided (ADR-003) | Synchronous enforcement through a reserve API, low latency |
| O-2 | Analytical serving | Decided (ADR-007) | Analytics is designed in. Default engine: Spark SQL over Gold |
| O-3 | Traffic absorption, partition keys, topic boundaries | Decided (ADR-008) | Queue absorbs bursts, peak plan in section 5.5, keys in section 7.2 |
| O-4 | Stream deduplication window and state store | Decided (ADR-009) | Window as long as the watermark delay, Spark's built-in state, the ledger is the final authority |
| O-5 | Contract management | Decided (ADR-004) | Schema registry with enforced evolution |
| O-6 | Attribution model | Decided (ADR-010) | Last click within a configurable window, chain stays traceable |
| O-7 | Traffic mix and funnel assumptions | Decided (ADR-006) | Real-world mixed traffic, configured per source type |
| O-8 | Currency and FX policy | Decided (ADR-005) | Multi-currency with managed FX rates, details in O-12 |
| O-9 | Reporting time zone and date boundaries | Decided (ADR-011) | UTC instants, per-account time zone, 15-minute UTC buckets |
| O-10 | Overspend slack | Decided (ADR-003) | Zero |
| O-11 | Registry product and serialization format | Open | Decide in S1 |
| O-12 | FX details: rate source, staleness bound, rounding | Open | Decide in S2. Proposed: lock the rate at reservation, round up for budget checks |
| O-13 | Reservation point: at bid time or at win time | Open | Decide in S2 |
| O-14 | Freshness target and lateness window | Open | Decide in S5. Needs the owner's freshness target |

## 13. Your edits [Owner]

1. Rewrite section 2 in your own words, 8 lines max.
2. Rewrite the invariants in section 4 in your own words and add two failure modes of your own.
3. Put a `?` next to anything you do not understand. Those lines are the most useful for the next session.

## Glossary

- **Idempotent:** doing it twice has the same effect as doing it once.
- **At-least-once delivery:** a message may arrive more than once, but it is not lost.
- **Event time and ingestion time:** when something happened versus when AdStream received it.
- **Watermark:** how long a stream processor waits for late events before it treats a time window as closed.
- **Bronze, Silver, Gold:** raw, cleaned and business-ready data tiers.
- **Reconciliation:** comparing two independent records of the same facts and explaining any difference.
- **Quarantine:** a holding area for rejected events, kept with the reason and the raw payload.
- **Partition key:** the value that decides which partition (lane) of a topic an event goes to. The same key always goes to the same lane, in order.
- **Reservation:** setting budget aside before delivery, then committing it when the ad is delivered or releasing it if not.
- **Schema registry:** a service that stores every version of every event schema and rejects incompatible changes.
- **FX rate:** the price of one currency in another at a point in time.
