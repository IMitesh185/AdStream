from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from adstream.domain.metrics import (
    calculate_cpa_micros,
    calculate_cpc_micros,
    calculate_cpm_micros,
    calculate_ctr_percent,
    calculate_cvr_percent,
    calculate_platform_fee_micros,
    calculate_publisher_payout_micros,
    calculate_roas,
    micros_to_usd,
    usd_to_micros,
)
from adstream.domain.models import (
    Campaign,
    CampaignStatus,
    ImpressionEvent,
    PricingModel,
    SourceSystem,
)


def test_exact_decimal_micros_roundtrip() -> None:
    assert usd_to_micros("0.10") + usd_to_micros("0.20") == usd_to_micros("0.30")
    assert str(micros_to_usd(12_345_678)) == "12.345678"


def test_cpm_multiplies_before_integer_division() -> None:
    # $0.50 across 1,000,000 impressions = $0.0005 CPM (500 micros), never 0
    assert calculate_cpm_micros(500_000, 1_000_000) == 500
    assert calculate_cpm_micros(12_500_000, 10_000) == 1_250_000
    assert calculate_cpm_micros(100, 0) == 0


def test_metrics_zero_guards_and_publisher_split_partition() -> None:
    assert calculate_ctr_percent(250, 10_000) == pytest.approx(2.5)
    assert calculate_ctr_percent(10, 0) == 0.0
    assert calculate_cpc_micros(12_500_000, 250) == 50_000
    assert calculate_cpc_micros(12_500_000, 0) == 0
    assert calculate_cvr_percent(5, 100) == pytest.approx(5.0)
    assert calculate_cpa_micros(1_000_000, 4) == 250_000
    assert calculate_roas(4_000_000, 1_000_000) == pytest.approx(4.0)

    gross = 123_457
    payout = calculate_publisher_payout_micros(gross, rev_share_bps=7000)
    fee = calculate_platform_fee_micros(gross, rev_share_bps=7000)
    assert payout + fee == gross


def test_strict_int_rejects_booleans_and_budget_invariant() -> None:
    with pytest.raises(ValidationError):
        Campaign(
            campaign_id="c1",
            advertiser_id="a1",
            account_id="acc1",
            name="Bad Bool Budget",
            status=CampaignStatus.ACTIVE,
            pricing_model=PricingModel.CPC,
            daily_budget_micros=True,  # type: ignore[arg-type]
            remaining_budget_micros=True,  # type: ignore[arg-type]
            max_bid_micros=100,
        )

    with pytest.raises(ValidationError):
        Campaign(
            campaign_id="c1",
            advertiser_id="a1",
            account_id="acc1",
            name="Remaining Exceeds Daily",
            daily_budget_micros=1000,
            remaining_budget_micros=2000,
            max_bid_micros=100,
        )

    with pytest.raises(ValidationError):
        ImpressionEvent(
            event_id="e1",
            idempotency_key="e1",
            source_system=SourceSystem.SYNTHETIC,
            source_event_id="e1",
            event_time=datetime.now(timezone.utc),
            advertiser_id="a1",
            campaign_id="c1",
            country="US",
            cost_micros=False,  # type: ignore[arg-type]
        )
