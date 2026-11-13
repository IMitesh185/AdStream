# AdStream - Compact event data contracts

**Status:** Proposed field reference derived from [DataContracts.md](./DataContracts.md). The full document remains unchanged and owns detailed behavior, entities, API operations and approval gates.

**R** = required, non-null. **O** = optional/unknown. **C** = required under the stated condition. Defaulted arrays/objects may be omitted, but cannot be null.

**Types:** `id` is a non-empty, case-sensitive string; `int64` is an exact signed 64-bit integer; `positive_int` is `int64 > 0`; `timestamp` is RFC 3339 UTC ending in `Z`, with up to six fractional digits. Limits and policies remain those of the full contract.

## 1. Shared event envelope

Every business event uses this envelope. Later JSON examples show only its `payload`, with `event_type` taken from the event heading.

| Field | Field type | Required | Why it is needed |
|---|---|---|---|
| `event_id` | `id` | R | Stable logical event identity; unchanged on retries/replay. |
| `event_type` | registered string enum | R | Selects the event contract. |
| `schema_version` | `positive_int` | R | Selects the registered writer schema. |
| `source` | registered source/account string | R | Identifies the authenticated connector or internal service. |
| `source_event_id` | non-empty source-native string | R | Preserves source identity and supports stable deduplication. |
| `occurred_at` | `timestamp` | R | Assigns the business fact to its correct time. |
| `received_at` | `timestamp` | R in canonical storage | Ingestion-assigned time; producers need not supply it. |
| `payload` | event-specific object | R | Contains the fields defined below, including applicable shared contexts. |
| `extensions` | JSON object | O; default `{}` | Preserves non-authoritative source extras; no credentials or prohibited personal data. |

Complete canonical click example:

```json
{
  "event_id": "evt-click-1",
  "event_type": "click",
  "schema_version": 1,
  "source": "synthetic.retail.account_demo",
  "source_event_id": "source-click-1",
  "occurred_at": "2026-11-13T07:30:01.000000Z",
  "received_at": "2026-11-13T07:30:01.250000Z",
  "payload": {
    "request_id": "request-1",
    "advertiser_id": "advertiser-demo",
    "campaign_id": "campaign-demo",
    "ad_id": "ad-demo",
    "publisher_id": "publisher-demo",
    "app_site_id": "site-demo",
    "placement_id": "placement-demo",
    "click_id": "click-1",
    "impression_id": "impression-1"
  },
  "extensions": {}
}
```

## 2. Shared payload fields

Contexts are reusable field lists, not nested JSON objects. Include their fields directly inside `payload` only when an event lists that context.

| Context | Field | Field type | Required | Why it is needed |
|---|---|---|---|---|
| RequestRef | `request_id` | `id` | R | Correlates the request chain and supplies its partition key; never fabricate it. |
| AdContext | `advertiser_id` | `id` | R | Identifies the advertiser; must match Campaign's parent. |
| AdContext | `campaign_id` | `id` | R | Attributes performance/spend; must match Ad's parent. |
| AdContext | `ad_id` | `id` | R | Identifies the creative. |
| InventoryContext | `publisher_id` | `id` | R | Identifies the inventory owner. |
| InventoryContext | `app_site_id` | `id` | R | Identifies the publisher's app/site. |
| InventoryContext | `placement_id` | `id` | R | Identifies the slot in that app/site. |
| ObservationContext | `user_id` | `id` | O | Pseudonymous correlation for attribution/fraud; anonymous events omit it. |
| ObservationContext | `identity_namespace` | `id` | C with `user_id` | Prevents unauthorized cross-namespace identity joins; omit both for anonymous events. |
| ObservationContext | `country_code` | ISO 3166-1 alpha-2 string | O | Geographic breakdown; unknown is null. |
| ObservationContext | `device_type` | enum: `desktop`, `mobile`, `tablet`, `connected_tv`, `other` | O | Device breakdown; unknown is null. |
| ObservationContext | `audience_ids` | `id[]` | O; default `[]` | Distinct authorized audience segments. |
| FinanceContext | `advertiser_id` | `id` | R | Identifies the financial owner. |
| FinanceContext | `campaign_id` | `id` | R | Attributes money and supplies the finance partition key. |

## 3. Nested field types

`Money` is exact integer micros plus currency: 1 currency unit = 1,000,000 micros. Monetary JSON must preserve integer precision. Negative amounts are allowed only for explicitly signed deltas.

| Object | Field | Field type | Required | Why it is needed |
|---|---|---|---|---|
| Money | `amount_micros` | `int64` | R | Exact amount without binary floating-point arithmetic. |
| Money | `currency` | uppercase ISO 4217 string | R | Prevents mixing currencies without explicit FX conversion. |
| ConversionItem | `line_item_id` | non-empty source-native string | R | Unique purchase/action line within a conversion. |
| ConversionItem | `product_id` | `id` | R | Product breakdown. |
| ConversionItem | `quantity` | `positive_int` | R | Units in this line. |
| ConversionItem | `revenue` | `Money` | R | Total line revenue, not unit price; non-negative. |
| AdjustmentLeg | `account_id` | `id` | R | Financial account being adjusted. |
| AdjustmentLeg | `balance_kind` | enum: `budget_consumed`, `advertiser_spend`, `publisher_payable` | R | Names the balance affected; cannot modify reservation holds. |
| AdjustmentLeg | `delta` | signed `Money` | R | Non-zero change in the account's currency. |
| ValidationError | `code` | string | R | Machine-readable failure reason. |
| ValidationError | `field_path` | JSON Pointer string | R | Invalid field location; empty string means the whole input. |
| ValidationError | `message` | string | R | Bounded explanation without secrets/raw personal data. |

## 4. Event fields and JSON payloads

Examples are synthetic fixtures. Referenced entities, reservations and policies are assumed to exist; these examples are not all successive operations on one reservation.

### ad_request

**Shared:** RequestRef + InventoryContext + ObservationContext. **Topic/key:** `auction` / `request_id`.

| Field | Field type | Required | Why it is needed |
|---|---|---|---|
| `requested_format` | enum: `display`, `video`, `native`, `other` | R | Matches the opportunity to formats supported by the placement. |
| `auction_id` | `id` | O | Links an auction already allocated at request time. |

```json
{
  "request_id": "request-1",
  "publisher_id": "publisher-demo",
  "app_site_id": "site-demo",
  "placement_id": "placement-demo",
  "requested_format": "video"
}
```

### bid

**Shared:** RequestRef + AdContext. **Topic/key:** `auction` / `request_id`.

| Field | Field type | Required | Why it is needed |
|---|---|---|---|
| `auction_id` | `id` | R | Identifies the auction receiving the bid. |
| `bid_id` | `id` | R | Stable identity of this bid. |
| `pricing_model` | enum: `cpc`, `cpm`, `cpa` | R | Defines the price unit: click, 1,000 impressions or qualifying conversion. |
| `bid_price` | `Money` | R | Non-negative offered unit price, not realized spend. |
| `pricing_policy_id` | `id` | R | Identifies the applicable terms. |
| `pricing_policy_version` | `positive_int` | R | Freezes those terms for audit/replay. |
| `reservation_id` | `id` | O | Links authorization where reservation timing requires it before bidding. |

```json
{
  "request_id": "request-1",
  "advertiser_id": "advertiser-demo",
  "campaign_id": "campaign-demo",
  "ad_id": "ad-demo",
  "auction_id": "auction-1",
  "bid_id": "bid-1",
  "pricing_model": "cpc",
  "bid_price": {"amount_micros": 2000000, "currency": "INR"},
  "pricing_policy_id": "pricing-demo",
  "pricing_policy_version": 1
}
```

### auction_result

**Shared:** RequestRef; AdContext required for `won`/`lost`, absent for `no_bid`. **Topic/key:** `auction` / `request_id`.

| Field | Field type | Required | Why it is needed |
|---|---|---|---|
| `auction_id` | `id` | R | Identifies the auction. |
| `result_id` | `id` | R | Stable outcome identity. |
| `outcome` | enum: `won`, `lost`, `no_bid` | R | Defines the result variant. |
| `bid_id` | `id` | C for `won`/`lost` | Identifies the evaluated bid; absent for `no_bid`. |
| `clearing_price` | `Money` | C for `won` | Records the non-negative winning price, not a ledger charge. |
| `pricing_model` | enum: `cpc`, `cpm`, `cpa` | C with clearing price | Interprets the clearing-price unit; agrees with the bid. |
| `reason_code` | enum: `outbid`, `budget_rejected`, `timeout`, `no_eligible_bid`, `other` | C for `lost`/`no_bid` | Explains why no delivery was won. |
| `reservation_id` | `id` | O | Links any related spend authorization. |

```json
{
  "request_id": "request-1",
  "advertiser_id": "advertiser-demo",
  "campaign_id": "campaign-demo",
  "ad_id": "ad-demo",
  "auction_id": "auction-1",
  "result_id": "result-1",
  "outcome": "won",
  "bid_id": "bid-1",
  "clearing_price": {"amount_micros": 1250000, "currency": "INR"},
  "pricing_model": "cpc"
}
```

### impression

**Shared:** RequestRef + AdContext + InventoryContext + ObservationContext. **Topic/key:** `delivery` / `request_id`.

| Field | Field type | Required | Why it is needed |
|---|---|---|---|
| `impression_id` | `id` | R | Identifies one impression for counts, click linkage and CPM billing evidence. |
| `bid_id` | `id` | O | Links auction-backed delivery; not required for direct-sold inventory. |
| `result_id` | `id` | O | Links the applicable auction result. |

```json
{
  "request_id": "request-1",
  "advertiser_id": "advertiser-demo",
  "campaign_id": "campaign-demo",
  "ad_id": "ad-demo",
  "publisher_id": "publisher-demo",
  "app_site_id": "site-demo",
  "placement_id": "placement-demo",
  "impression_id": "impression-1"
}
```

### click

**Shared:** RequestRef + AdContext + InventoryContext + ObservationContext. **Topic/key:** `delivery` / `request_id`.

| Field | Field type | Required | Why it is needed |
|---|---|---|---|
| `click_id` | `id` | R | Identifies one actual click; retries retain it, genuine new clicks do not. |
| `impression_id` | `id` | R | Traces the clicked impression, even if its event arrives later. |
| `landing_page_ref` | `id` | O | Identifies the observed approved destination version; agrees with Ad metadata. |

```json
{
  "request_id": "request-1",
  "advertiser_id": "advertiser-demo",
  "campaign_id": "campaign-demo",
  "ad_id": "ad-demo",
  "publisher_id": "publisher-demo",
  "app_site_id": "site-demo",
  "placement_id": "placement-demo",
  "click_id": "click-1",
  "impression_id": "impression-1",
  "user_id": "user-demo",
  "identity_namespace": "synthetic.advertiser-demo",
  "country_code": "IN"
}
```

### video_progress

**Shared:** RequestRef + AdContext + InventoryContext + ObservationContext. **Topic/key:** `delivery` / `request_id`.

| Field | Field type | Required | Why it is needed |
|---|---|---|---|
| `impression_id` | `id` | R | Links playback to delivery. |
| `playback_id` | `id` | R | Identifies one playback; a new replay uses a new ID. |
| `milestone` | enum: `started`, `quartile_25`, `quartile_50`, `quartile_75`, `completed` | R | Counts each `(playback_id, milestone)` once. |
| `position_ms` | non-negative `int64` | R | Position reached; cannot exceed known video duration. |
| `video_duration_ms` | `positive_int` | O | Enables duration/progress validation. |

```json
{
  "request_id": "request-1",
  "advertiser_id": "advertiser-demo",
  "campaign_id": "campaign-demo",
  "ad_id": "ad-demo",
  "publisher_id": "publisher-demo",
  "app_site_id": "site-demo",
  "placement_id": "placement-demo",
  "impression_id": "impression-1",
  "playback_id": "playback-1",
  "milestone": "quartile_25",
  "position_ms": 5000,
  "video_duration_ms": 20000
}
```

### conversion

**Shared:** RequestRef + ObservationContext. **Topic/key:** `conversion` / `request_id`.

| Field | Field type | Required | Why it is needed |
|---|---|---|---|
| `conversion_id` | `id` | R | Stable business action identity; prevents repeated counts/revenue. |
| `advertiser_id` | `id` | R | Owns the action before campaign/Ad attribution is resolved. |
| `conversion_type` | enum: `add_to_cart`, `purchase`, `custom` | R | Selects the action and conditional fields. |
| `action_name` | non-empty string | C for `custom` | Names the registered custom action. |
| `order_id` | non-empty source-native string | C for purchase | Identifies the source/advertiser-scoped order. |
| `revenue` | `Money` | C for purchase; O for a value-bearing custom action | Supplies non-negative economic value; missing is not zero. |
| `product_id` | `id` | C for add-to-cart; O otherwise | Identifies the affected product. |
| `quantity` | `positive_int` | C for add-to-cart; O otherwise | Counts product units. |
| `reported_click_id` | `id` | O | Supplies attribution evidence, not an override of last-click policy. |
| `reported_campaign_id` | `id` | O | Preserves a source association; required if `reported_ad_id` is supplied. |
| `reported_ad_id` | `id` | O | Must belong to the supplied reported campaign. |
| `items` | `ConversionItem[]` | O; default `[]` | Product allocation; distinct line IDs, with one currency and exact sum to conversion revenue. |

```json
{
  "request_id": "request-1",
  "conversion_id": "conversion-1",
  "advertiser_id": "advertiser-demo",
  "conversion_type": "purchase",
  "order_id": "order-demo-1",
  "revenue": {"amount_micros": 500000000, "currency": "INR"},
  "user_id": "user-demo",
  "identity_namespace": "synthetic.advertiser-demo",
  "reported_click_id": "click-1",
  "items": [
    {
      "line_item_id": "line-1",
      "product_id": "product-demo",
      "quantity": 1,
      "revenue": {"amount_micros": 500000000, "currency": "INR"}
    }
  ]
}
```

### event_correction

**Shared:** RequestRef. **Topic/key:** target's non-financial family / target's `request_id`.

| Field | Field type | Required | Why it is needed |
|---|---|---|---|
| `correction_id` | `id` | R | Identifies the correction once. |
| `target_event_id` | `id` | R | Preserves the original observation link. |
| `target_event_type` | enum: `ad_request`, `bid`, `auction_result`, `impression`, `click`, `video_progress`, `conversion` | R | Selects the target schema; financial events cannot be corrected this way. |
| `expected_revision_event_id` | `id` | R | Detects conflicting revision heads; initially the original event ID. |
| `operation` | enum: `replace`, `invalidate` | R | Distinguishes replacement from retraction. |
| `replacement_payload` | complete target payload object | C for `replace` | Supplies the full corrected observation, not a partial patch. |
| `replacement_occurred_at` | `timestamp` | C for `replace` | Supplies the corrected business time. |
| `reason_code` | non-empty registered string | R | Explains the authorized correction; request/occurrence identity cannot change. |

```json
{
  "request_id": "request-1",
  "correction_id": "correction-1",
  "target_event_id": "evt-video-1",
  "target_event_type": "video_progress",
  "expected_revision_event_id": "evt-video-1",
  "operation": "invalidate",
  "reason_code": "source_retraction"
}
```

### budget_reserved

**Shared:** FinanceContext + RequestRef. **Topic/key:** `finance` / `campaign_id`.

| Field | Field type | Required | Why it is needed |
|---|---|---|---|
| `reservation_id` | `id` | R | Identifies the durable authorization. |
| `idempotency_key` | `id` | R | Prevents reserve-command retries from creating extra holds. |
| `budget_id` | `id` | R | Selects the budget allocation. |
| `budget_version` | `positive_int` | R | Records the limit/configuration evaluated. |
| `maximum_charge` | `Money` | R | Positive cap in the original charge currency. |
| `reserved_amount` | `Money` | R | Positive hold in campaign currency. |
| `expires_at` | `timestamp` | R | Bounds the hold; after authorization, no later than budget-period end. |
| `decision_point` | enum: `bid`, `win` | R | Records the activated reservation timing, not a new default. |
| `pricing_policy_id` | `id` | R | Identifies authorized pricing terms. |
| `pricing_policy_version` | `positive_int` | R | Freezes those terms. |
| `fx_conversion_id` | `id` | C for cross-currency reserve | Locks exact conversion/rate/rounding evidence. |

```json
{
  "advertiser_id": "advertiser-demo",
  "campaign_id": "campaign-demo",
  "request_id": "request-1",
  "reservation_id": "reservation-1",
  "idempotency_key": "reserve-command-1",
  "budget_id": "budget-demo",
  "budget_version": 1,
  "maximum_charge": {"amount_micros": 2000000, "currency": "INR"},
  "reserved_amount": {"amount_micros": 2000000, "currency": "INR"},
  "expires_at": "2026-11-13T07:31:00.000000Z",
  "decision_point": "win",
  "pricing_policy_id": "pricing-demo",
  "pricing_policy_version": 1
}
```

### budget_committed

**Shared:** FinanceContext + RequestRef. **Topic/key:** `finance` / `campaign_id`.

| Field | Field type | Required | Why it is needed |
|---|---|---|---|
| `reservation_id` | `id` | R | References the active authorization at the service transition. |
| `idempotency_key` | `id` | R | Prevents repeated commit effects. |
| `budget_id` | `id` | R | Matches the reservation's allocation. |
| `billing_key` | `id` | R | Identifies one primary charge across observations/producers. |
| `billable_event_id` | `id` | R | Links charge evidence, even if it arrives in Kafka later. |
| `billable_event_type` | enum: `impression`, `click`, `conversion` | R | Matches CPM/CPC/CPA terms. |
| `billable_occurred_at` | `timestamp` | R | Assigns spend to the billable action's time. |
| `final_charge` | `Money` | R | Non-negative original-currency charge, no greater than the original cap. |
| `committed_amount` | `Money` | R | Non-negative campaign-currency consumption, no greater than the hold. |
| `released_amount` | `Money` | R | Non-negative unused hold; committed plus released equals the reserved amount. |
| `fx_conversion_id` | `id` | C for cross-currency commit | Records conversion using the reservation's locked terms. |

```json
{
  "advertiser_id": "advertiser-demo",
  "campaign_id": "campaign-demo",
  "request_id": "request-1",
  "reservation_id": "reservation-1",
  "idempotency_key": "commit-command-1",
  "budget_id": "budget-demo",
  "billing_key": "billing.synthetic.click-1",
  "billable_event_id": "evt-click-1",
  "billable_event_type": "click",
  "billable_occurred_at": "2026-11-13T07:30:01.000000Z",
  "final_charge": {"amount_micros": 1250000, "currency": "INR"},
  "committed_amount": {"amount_micros": 1250000, "currency": "INR"},
  "released_amount": {"amount_micros": 750000, "currency": "INR"}
}
```

### budget_released / budget_expired

**Shared:** FinanceContext + RequestRef. **Topic/key:** `finance` / `campaign_id`. The two event types share these fields.

| Field | Field type | Required | Why it is needed |
|---|---|---|---|
| `reservation_id` | `id` | R | Identifies the hold being released. |
| `idempotency_key` | `id` | R | Makes release/expiry repeatable without repeating its effect. |
| `budget_id` | `id` | R | Matches the original allocation. |
| `released_amount` | `Money` | R | Entire remaining campaign-currency hold; creates no spend. |
| `reason_code` | enum: `unused`, `auction_lost`, `cancelled`, `expired` | R | Only `budget_expired` uses `expired`. |

`budget_released` payload:

```json
{
  "advertiser_id": "advertiser-demo",
  "campaign_id": "campaign-demo",
  "request_id": "request-2",
  "reservation_id": "reservation-2",
  "idempotency_key": "release-command-2",
  "budget_id": "budget-demo",
  "released_amount": {"amount_micros": 2000000, "currency": "INR"},
  "reason_code": "auction_lost"
}
```

`budget_expired` payload:

```json
{
  "advertiser_id": "advertiser-demo",
  "campaign_id": "campaign-demo",
  "request_id": "request-3",
  "reservation_id": "reservation-3",
  "idempotency_key": "expire-command-3",
  "budget_id": "budget-demo",
  "released_amount": {"amount_micros": 2000000, "currency": "INR"},
  "reason_code": "expired"
}
```

### spend_reported

**Shared:** FinanceContext. **Topic/key:** `finance` / `campaign_id`.

| Field | Field type | Required | Why it is needed |
|---|---|---|---|
| `billing_key` | `id` | R | Identifies one external charge/statement; matching controlled charges are not charged twice. |
| `budget_id` | `id` | R | Identifies the historical allocation, including late liabilities. |
| `cost_grain` | enum: `event`, `aggregate` | R | Distinguishes one billable event from a statement. |
| `billable_event_id` | `id` | C for event-level cost | Links the chargeable occurrence. |
| `source_statement_id` | non-empty source-native string | C for aggregate cost | Identifies the source statement. |
| `coverage_start` | `timestamp` | C for aggregate cost | Inclusive statement coverage start. |
| `coverage_end` | `timestamp` | C for aggregate cost | Exclusive coverage end, after start. |
| `reported_amount` | `Money` | R | Non-negative liability in source currency; not refused for budget exhaustion. |
| `campaign_amount` | `Money` | R | Non-negative campaign-currency spend. |
| `fx_conversion_id` | `id` | C if currencies differ | Makes source-to-campaign conversion auditable. |
| `pricing_policy_id` | `id` | R | Identifies source-reported pricing authority. |
| `pricing_policy_version` | `positive_int` | R | Freezes those terms; overlapping event/aggregate costs are not both additive. |

```json
{
  "advertiser_id": "advertiser-demo",
  "campaign_id": "campaign-demo",
  "billing_key": "billing.external.statement-1",
  "budget_id": "budget-demo",
  "cost_grain": "aggregate",
  "source_statement_id": "statement-1",
  "coverage_start": "2026-11-13T07:00:00.000000Z",
  "coverage_end": "2026-11-13T08:00:00.000000Z",
  "reported_amount": {"amount_micros": 3000000, "currency": "INR"},
  "campaign_amount": {"amount_micros": 3000000, "currency": "INR"},
  "pricing_policy_id": "external-pricing-demo",
  "pricing_policy_version": 1
}
```

### financial_adjustment

**Shared:** FinanceContext. **Topic/key:** `finance` / `campaign_id`.

| Field | Field type | Required | Why it is needed |
|---|---|---|---|
| `adjustment_id` | `id` | R | Stable authorized correction identity. |
| `reference_event_id` | `id` | R | Preserves the prior financial fact rather than overwriting it. |
| `budget_id` | `id` | R | Identifies the affected allocation. |
| `reason_code` | non-empty registered string | R | Explains the correction. |
| `policy_id` | `id` | R | Identifies correction authority/calculation rules. |
| `policy_version` | `positive_int` | R | Makes the calculation reproducible. |
| `legs` | non-empty `AdjustmentLeg[]` | R | Explicit compensating deltas; cannot bypass authorization for additional controlled spend. |

```json
{
  "advertiser_id": "advertiser-demo",
  "campaign_id": "campaign-demo",
  "adjustment_id": "adjustment-1",
  "reference_event_id": "evt-external-spend-1",
  "budget_id": "budget-demo",
  "reason_code": "source_statement_correction",
  "policy_id": "reconciliation-demo",
  "policy_version": 1,
  "legs": [
    {
      "account_id": "spend-account-demo",
      "balance_kind": "advertiser_spend",
      "delta": {"amount_micros": -100000, "currency": "INR"}
    },
    {
      "account_id": "consumed-account-demo",
      "balance_kind": "budget_consumed",
      "delta": {"amount_micros": -100000, "currency": "INR"}
    }
  ]
}
```

### refund

**Shared:** FinanceContext. **Topic/key:** `finance` / `campaign_id`.

| Field | Field type | Required | Why it is needed |
|---|---|---|---|
| `refund_id` | `id` | R | Prevents duplicate credits. |
| `original_charge_event_id` | `id` | R | Links the primary charge being credited. |
| `billing_key` | `id` | R | Preserves original charge identity; not a new primary charge. |
| `budget_id` | `id` | R | Links the original allocation. |
| `amount` | `Money` | R | Positive campaign-currency credit, bounded by the remaining refundable charge. |
| `budget_credit` | `Money` | R | Capacity restored by policy, from zero through the refund amount. |
| `refund_policy_id` | `id` | R | Distinguishes refunding spend from reinstating budget. |
| `refund_policy_version` | `positive_int` | R | Freezes that policy. |
| `reason_code` | non-empty registered string | R | Explains the credit; publisher reversals need separate explicit adjustments. |

```json
{
  "advertiser_id": "advertiser-demo",
  "campaign_id": "campaign-demo",
  "refund_id": "refund-1",
  "original_charge_event_id": "evt-committed-1",
  "billing_key": "billing.synthetic.click-1",
  "budget_id": "budget-demo",
  "amount": {"amount_micros": 250000, "currency": "INR"},
  "budget_credit": {"amount_micros": 0, "currency": "INR"},
  "refund_policy_id": "refund-no-reinstatement-demo",
  "refund_policy_version": 1,
  "reason_code": "approved_credit"
}
```

### publisher_obligation

**Shared:** FinanceContext. **Topic/key:** `finance` / `campaign_id`.

| Field | Field type | Required | Why it is needed |
|---|---|---|---|
| `obligation_id` | `id` | R | Identifies one accrued publisher liability. |
| `publisher_id` | `id` | R | Identifies who is owed the amount. |
| `basis_event_id` | `id` | R | Links the underlying charge/statement. |
| `billing_key` | `id` | R | Links the advertiser charge without adding it to spend again. |
| `amount` | `Money` | R | Non-negative obligation in publisher settlement currency, not proof of cash payment. |
| `revenue_policy_id` | `id` | R | Identifies publisher calculation/fee terms. |
| `revenue_policy_version` | `positive_int` | R | Makes the exact obligation reproducible. |
| `fx_conversion_id` | `id` | C for cross-currency calculation | Records the conversion used to derive publisher currency. |

```json
{
  "advertiser_id": "advertiser-demo",
  "campaign_id": "campaign-demo",
  "obligation_id": "obligation-1",
  "publisher_id": "publisher-demo",
  "basis_event_id": "evt-committed-1",
  "billing_key": "billing.synthetic.click-1",
  "amount": {"amount_micros": 1000000, "currency": "INR"},
  "revenue_policy_id": "publisher-terms-demo",
  "revenue_policy_version": 1
}
```

## 5. Quarantine record and JSON

**Topic/key:** `quarantine` / `quarantine_id`. This is a standalone system record, not a business-event `payload`; it does not require the shared envelope because rejected inputs may not have valid IDs.

| Field | Field type | Required | Why it is needed |
|---|---|---|---|
| `quarantine_id` | `id` | R | Identifies the retained failure. |
| `receipt_id` | `id` | R | Links the raw delivery attempt. |
| `source` | registered source/account string | O | Identifies the source only when established. |
| `event_id` | `id` | O | Links a business event only when its identity is valid. |
| `event_type` | string | O | Preserves the observed value, even if unsupported. |
| `observed_schema_version` | string | O | Safely preserves an invalid/unrecognized version value. |
| `stage` | enum: `adaptation`, `schema`, `identity`, `reference`, `financial` | R | Identifies where validation failed. |
| `errors` | non-empty `ValidationError[]` | R | Explains every retained failure without a silent drop. |
| `raw_payload_ref` | `id` | R | Resolves durably to the original source bytes. |
| `raw_payload_sha256` | 64-character lowercase hex string | R | Verifies the preserved bytes. |
| `received_at` | `timestamp` | R | Records delivery time. |
| `quarantined_at` | `timestamp` | R | Records durable failure capture time. |
| `adapter_version` | `id` | O | Identifies the mapping implementation if one was selected. |

```json
{
  "quarantine_id": "quarantine-1",
  "receipt_id": "receipt-empty-1",
  "stage": "schema",
  "errors": [
    {
      "code": "MALFORMED_JSON",
      "field_path": "",
      "message": "Empty body is not valid JSON."
    }
  ],
  "raw_payload_ref": "raw-empty-1",
  "raw_payload_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "received_at": "2026-11-13T07:30:02.000000Z",
  "quarantined_at": "2026-11-13T07:30:02.100000Z"
}
```
