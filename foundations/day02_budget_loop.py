'''
    Day 2: Simulate a sequence of 20 ad-event charges against a campaign budget
    using if/elif/else, for, and while loops—stopping when budget runs out
    or status is not ACTIVE, and counting served vs rejected events.
'''


def main():
    daily_budget_micros = int(input("Enter daily budget in micros ($1 = 1_000_000): "))
    remaining_budget_micros = daily_budget_micros
    status = input("Enter campaign status (ACTIVE/PAUSED): ").strip().upper()
    base_cost_micros = int(input("Enter base event cost in micros: "))
    max_bid_micros = base_cost_micros * 3

    served_events = 0
    rejected_events = 0
    stop_reason = "Completed all 20 events"

    for event_num in range(1, 21):
        # Varying charges across events (1x, 2x, 3x, 4x base cost) so budget edges are exercised
        event_cost = base_cost_micros * (((event_num - 1) % 4) + 1)

        # Fail closed: only ACTIVE campaigns may serve ads
        if status != "ACTIVE":
            rejected_events += 1
            stop_reason = f"Stopped at event {event_num}: campaign status is {status}"
            break
        elif remaining_budget_micros == 0:
            stop_reason = f"Stopped at event {event_num}: budget exhausted"
            break
        elif event_cost <= 0:
            rejected_events += 1
            print(f"Event {event_num}: REJECTED (invalid non-positive cost {event_cost})")
            continue
        elif event_cost > max_bid_micros:
            rejected_events += 1
            print(
                f"Event {event_num}: REJECTED "
                f"(cost {event_cost} exceeds max bid {max_bid_micros})"
            )
            continue
        elif event_cost > remaining_budget_micros:
            rejected_events += 1
            print(
                f"Event {event_num}: REJECTED "
                f"(cost {event_cost} > remaining {remaining_budget_micros})"
            )
            continue
        else:
            remaining_budget_micros -= event_cost
            served_events += 1
            print(
                f"Event {event_num}: SERVED "
                f"(charged {event_cost}, remaining {remaining_budget_micros})"
            )

    # Secondary while-loop check: drain any leftover budget with minimum-cost impressions
    bonus_served = 0
    while (
        status == "ACTIVE"
        and base_cost_micros > 0
        and remaining_budget_micros >= base_cost_micros
    ):
        remaining_budget_micros -= base_cost_micros
        bonus_served += 1

    total_spent_micros = daily_budget_micros - remaining_budget_micros

    print("\n--- Batch Summary ---")
    print(f"Stop Reason: {stop_reason}")
    print(f"Served events (batch): {served_events}")
    print(f"Bonus served (while drain): {bonus_served}")
    print(f"Rejected events: {rejected_events}")
    print(f"Total spent: ${total_spent_micros / 1_000_000:.2f} ({total_spent_micros} micros)")
    print(
        f"Remaining budget: ${remaining_budget_micros / 1_000_000:.2f} "
        f"({remaining_budget_micros} micros)"
    )


if __name__ == "__main__":
    main()