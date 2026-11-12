"""
Day 3: Indexing Impressions, Publishers & Deduplicating IDs
Uses list (ordered log), tuple (immutable composite key), set (O(1) dedup),
dict (per-campaign/country totals), and benchmarks list vs set lookups.
"""

import time


def main():
    # 1. Raw incoming event stream (ordered list, intentionally includes duplicate event_ids)
    raw_events = [
        {"event_id": "evt_101", "campaign_id": "camp_01", "country": "US", "type": "impression", "cost_micros": 1_500},
        {"event_id": "evt_102", "campaign_id": "camp_01", "country": "US", "type": "click", "cost_micros": 50_000},
        {"event_id": "evt_101", "campaign_id": "camp_01", "country": "US", "type": "impression", "cost_micros": 1_500},  # duplicate
        {"event_id": "evt_103", "campaign_id": "camp_01", "country": "IN", "type": "impression", "cost_micros": 800},
        {"event_id": "evt_104", "campaign_id": "camp_02", "country": "US", "type": "impression", "cost_micros": 2_000},
        {"event_id": "evt_102", "campaign_id": "camp_01", "country": "US", "type": "click", "cost_micros": 50_000},       # duplicate
        {"event_id": "evt_105", "campaign_id": "camp_02", "country": "US", "type": "click", "cost_micros": 75_000},
        {"event_id": "evt_106", "campaign_id": "camp_01", "country": "IN", "type": "click", "cost_micros": 25_000},
        {"event_id": "evt_105", "campaign_id": "camp_02", "country": "US", "type": "click", "cost_micros": 75_000},       # duplicate
        {"event_id": "evt_107", "campaign_id": "camp_02", "country": "IN", "type": "impression", "cost_micros": 1_000},
    ]

    seen_event_ids = set()  # Note: {} creates an empty dict, so always use set()
    accepted_log = []
    duplicate_count = 0

    spend_by_key = {}
    impressions_by_key = {}
    clicks_by_key = {}

    for event in raw_events:
        event_id = event["event_id"]

        if event_id in seen_event_ids:
            duplicate_count += 1
            continue

        if event["cost_micros"] < 0:
            continue

        seen_event_ids.add(event_id)
        accepted_log.append(event)

        # Tuples are immutable and hashable, so they work as dict keys.
        # A mutable list [campaign_id, country] would raise TypeError: unhashable type.
        key = (event["campaign_id"], event["country"])

        spend_by_key[key] = spend_by_key.get(key, 0) + event["cost_micros"]
        if event["type"] == "impression":
            impressions_by_key[key] = impressions_by_key.get(key, 0) + 1
        elif event["type"] == "click":
            clicks_by_key[key] = clicks_by_key.get(key, 0) + 1

    print("=== Part 1: Deduplicated Batch Summary ===")
    print(f"Raw events received : {len(raw_events)}")
    print(f"Unique accepted     : {len(accepted_log)}")
    print(f"Duplicates skipped  : {duplicate_count}")
    print("\nBreakdown by (campaign_id, country):")

    for key in spend_by_key:
        imps = impressions_by_key.get(key, 0)
        clicks = clicks_by_key.get(key, 0)
        spend = spend_by_key[key]
        ctr = (clicks / imps) if imps > 0 else 0.0
        print(
            f"  {key} -> impressions={imps}, clicks={clicks}, "
            f"CTR={ctr:.2%}, spend=${spend / 1_000_000:.6f} ({spend} micros)"
        )

    # 2. Benchmark: O(n) list lookup vs O(1) set lookup across 100,000 IDs
    total_ids = 100_000
    ids_list = [f"evt_{i}" for i in range(total_ids)]
    ids_set = set(ids_list)
    probe_ids = [f"evt_{i}" for i in range(99_000, 100_000)]

    start_list = time.perf_counter()
    list_hits = 0
    for target in probe_ids:
        if target in ids_list:
            list_hits += 1
    list_elapsed = time.perf_counter() - start_list

    start_set = time.perf_counter()
    set_hits = 0
    for target in probe_ids:
        if target in ids_set:
            set_hits += 1
    set_elapsed = time.perf_counter() - start_set

    speedup = (list_elapsed / set_elapsed) if set_elapsed > 0 else 0.0

    print("\n=== Part 2: Membership Lookup Benchmark (1,000 lookups in 100,000 IDs) ===")
    print(f"list lookup : {list_elapsed:.6f}s (hits={list_hits})")
    print(f"set lookup  : {set_elapsed:.6f}s (hits={set_hits})")
    print(f"set speedup : {speedup:,.1f}x faster")


if __name__ == "__main__":
    main()
