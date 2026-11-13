"""
Exact integer-micros AdTech metrics and currency helpers.

All monetary values use integer micros ($1.00 = 1_000_000 micros) to prevent
IEEE-754 binary floating-point drift across billions of financial aggregations.
"""

from decimal import Decimal, ROUND_HALF_UP

MICROS_PER_UNIT = 1_000_000
BPS_DENOMINATOR = 10_000


def usd_to_micros(amount: str | int | Decimal) -> int:
    """Convert an exact decimal dollar amount to integer micros without float drift."""
    dec = Decimal(str(amount))
    scaled = (dec * MICROS_PER_UNIT).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(scaled)


def micros_to_usd(micros: int) -> Decimal:
    """Convert integer micros to exact Decimal dollars."""
    return (Decimal(micros) / Decimal(MICROS_PER_UNIT)).quantize(Decimal("0.000001"))


def calculate_ctr_percent(clicks: int, impressions: int) -> float:
    """Click-Through Rate (%): maps clicks to impressions."""
    if impressions <= 0 or clicks <= 0:
        return 0.0
    return (clicks / impressions) * 100.0


def calculate_cpc_micros(spent_micros: int, clicks: int) -> int:
    """Cost Per Click in integer micros: maps spend to clicks."""
    if clicks <= 0 or spent_micros <= 0:
        return 0
    return spent_micros // clicks


def calculate_cpm_micros(spent_micros: int, impressions: int) -> int:
    """Cost Per Mille (1,000 impressions) in integer micros; multiplies before floor division."""
    if impressions <= 0 or spent_micros <= 0:
        return 0
    return (spent_micros * 1_000) // impressions


def calculate_cvr_percent(conversions: int, clicks: int) -> float:
    """Conversion Rate (%): maps conversions to clicks."""
    if clicks <= 0 or conversions <= 0:
        return 0.0
    return (conversions / clicks) * 100.0


def calculate_cpa_micros(spent_micros: int, conversions: int) -> int:
    """Cost Per Acquisition in integer micros."""
    if conversions <= 0 or spent_micros <= 0:
        return 0
    return spent_micros // conversions


def calculate_roas(attributed_revenue_micros: int, spent_micros: int) -> float:
    """Return on Ad Spend (attributed revenue / ad spend)."""
    if spent_micros <= 0 or attributed_revenue_micros <= 0:
        return 0.0
    return attributed_revenue_micros / spent_micros


def calculate_publisher_payout_micros(gross_spend_micros: int, rev_share_bps: int = 7000) -> int:
    """Compute exact publisher payout in integer micros using basis points."""
    if gross_spend_micros <= 0 or rev_share_bps <= 0:
        return 0
    return (gross_spend_micros * rev_share_bps) // BPS_DENOMINATOR


def calculate_platform_fee_micros(gross_spend_micros: int, rev_share_bps: int = 7000) -> int:
    """Platform net take = gross spend minus publisher obligation (exact partition, zero lost micros)."""
    payout = calculate_publisher_payout_micros(gross_spend_micros, rev_share_bps)
    return gross_spend_micros - payout
