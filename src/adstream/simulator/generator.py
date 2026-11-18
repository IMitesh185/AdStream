"""
Realistic, relationally coherent synthetic AdStream data generator.

Produces:
- Full multi-entity catalog (agencies -> advertisers -> campaigns -> ad_groups -> ads,
  plus publishers -> placements, products, and audience segments).
- Streaming O(1)-memory event iterator generating coherent auction/impression/video/
  click/conversion chains along with configurable real-world abnormalities:
  * 80/20 skewed advertiser & publisher distributions
  * Duplicate retries
  * Out-of-order & late-arriving timestamps
  * Invalid foreign references & malformed raw records
  * Schema evolution (v1 + v2 + occasional breaking v99)
  * Fraudulent click-flood bursts
  * Multi-currency & sparse optional fields
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator

from adstream.domain.models import (
    Account,
    AdGroup,
    Advertisement,
    Advertiser,
    Agency,
    AudienceSegment,
    Campaign,
    CampaignStatus,
    CreativeAsset,
    CurrencyCode,
    Placement,
    PricingModel,
    Product,
    Publisher,
    SourceSystem,
)


@dataclass(frozen=True)
class SimulatorConfig:
    seed: int = 42
    num_advertisers: int = 20
    campaigns_per_advertiser: int = 3
    num_publishers: int = 12
    duplicate_rate: float = 0.08
    late_event_rate: float = 0.05
    malformed_rate: float = 0.03
    fraud_burst_rate: float = 0.03
    breaking_schema_rate: float = 0.01
    skew_top_share: float = 0.70  # 70% of traffic concentrated in top 20% advertisers/publishers
    base_time: datetime = field(
        default_factory=lambda: datetime(2026, 11, 18, 12, 0, 0, tzinfo=timezone.utc)
    )


@dataclass
class AdStreamCatalog:
    agencies: list[Agency]
    advertisers: list[Advertiser]
    accounts: list[Account]
    campaigns: list[Campaign]
    ad_groups: list[AdGroup]
    creatives: list[CreativeAsset]
    ads: list[Advertisement]
    products: list[Product]
    publishers: list[Publisher]
    placements: list[Placement]
    segments: list[AudienceSegment]

    campaign_by_id: dict[str, Campaign] = field(default_factory=dict)
    publisher_by_id: dict[str, Publisher] = field(default_factory=dict)
    ads_by_campaign: dict[str, list[Advertisement]] = field(default_factory=dict)
    placements_by_publisher: dict[str, list[Placement]] = field(default_factory=dict)


_COUNTRIES: tuple[tuple[str, CurrencyCode], ...] = (
    ("US", CurrencyCode.USD),
    ("GB", CurrencyCode.GBP),
    ("DE", CurrencyCode.EUR),
    ("IN", CurrencyCode.INR),
    ("JP", CurrencyCode.JPY),
)
_DEVICES: tuple[str, ...] = ("mobile", "desktop", "tablet", "ctv")
_BROWSERS: tuple[str | None, ...] = ("chrome", "safari", "firefox", "edge", None)
_SOURCES: tuple[SourceSystem, ...] = (
    SourceSystem.GOOGLE_ADS,
    SourceSystem.YOUTUBE_ADS,
    SourceSystem.AMAZON_ADS,
    SourceSystem.META_ADS,
    SourceSystem.RETAIL_MEDIA,
    SourceSystem.PROGRAMMATIC,
)


_SOURCE_PREFIX: dict[SourceSystem, str] = {
    SourceSystem.GOOGLE_ADS: "gads",
    SourceSystem.YOUTUBE_ADS: "yt",
    SourceSystem.AMAZON_ADS: "amzn",
    SourceSystem.META_ADS: "meta",
    SourceSystem.RETAIL_MEDIA: "rmn",
    SourceSystem.PROGRAMMATIC: "rtb",
    SourceSystem.SYNTHETIC: "syn",
}


class AdStreamSimulator:
    """Generates coherent entity catalogs and lazy streams of raw ecosystem payloads."""

    def __init__(self, config: SimulatorConfig | None = None) -> None:
        self.config = config or SimulatorConfig()
        self._rng = random.Random(self.config.seed)

    def build_catalog(self) -> AdStreamCatalog:
        rng = random.Random(self.config.seed)
        agencies = [
            Agency(agency_id="ag_001", name="Apex Media Holdings"),
            Agency(agency_id="ag_002", name="Vertex Digital Group"),
        ]
        segments = [
            AudienceSegment(segment_id="seg_tech", label="Tech Enthusiasts"),
            AudienceSegment(segment_id="seg_shop", label="Frequent Online Shoppers"),
            AudienceSegment(segment_id="seg_auto", label="Auto Intenders"),
            AudienceSegment(segment_id="seg_stream", label="Cord Cutters"),
        ]

        advertisers: list[Advertiser] = []
        accounts: list[Account] = []
        campaigns: list[Campaign] = []
        ad_groups: list[AdGroup] = []
        creatives: list[CreativeAsset] = []
        ads: list[Advertisement] = []
        products: list[Product] = []

        for a_idx in range(1, self.config.num_advertisers + 1):
            adv_id = f"adv_{a_idx:04d}"
            country, currency = _COUNTRIES[(a_idx - 1) % len(_COUNTRIES)]
            tier = "enterprise" if a_idx <= max(2, self.config.num_advertisers // 5) else "smb"
            agency_id = agencies[a_idx % len(agencies)].agency_id if a_idx % 3 != 0 else None

            advertisers.append(
                Advertiser(
                    advertiser_id=adv_id,
                    agency_id=agency_id,
                    name=f"Advertiser {a_idx:04d}",
                    tier=tier,  # type: ignore[arg-type]
                    country=country,
                    currency=currency,
                )
            )
            acc_id = f"acc_{a_idx:04d}"
            accounts.append(Account(account_id=acc_id, advertiser_id=adv_id, billing_currency=currency))

            prod_id = f"prod_{a_idx:04d}"
            products.append(
                Product(
                    product_id=prod_id,
                    advertiser_id=adv_id,
                    category=rng.choice(["electronics", "apparel", "grocery", "saas"]),
                    unit_price_micros=rng.randint(15_000_000, 120_000_000),
                )
            )

            for c_idx in range(1, self.config.campaigns_per_advertiser + 1):
                camp_id = f"camp_{a_idx:04d}_{c_idx:02d}"
                daily_budget = (
                    500_000_000_000 if tier == "enterprise" else 50_000_000_000
                )  # large enough for high-volume simulation unless constrained in tests
                pricing = rng.choice([PricingModel.CPC, PricingModel.CPM, PricingModel.CPV])
                campaigns.append(
                    Campaign(
                        campaign_id=camp_id,
                        advertiser_id=adv_id,
                        account_id=acc_id,
                        name=f"Campaign {camp_id}",
                        status=CampaignStatus.ACTIVE,
                        pricing_model=pricing,
                        daily_budget_micros=daily_budget,
                        remaining_budget_micros=daily_budget,
                        max_bid_micros=5_000_000,
                        currency=currency,
                        country_tier="tier_1" if country in ("US", "GB", "DE") else "tier_2",
                    )
                )

                ag_id = f"agp_{camp_id}"
                ad_groups.append(
                    AdGroup(
                        ad_group_id=ag_id,
                        campaign_id=camp_id,
                        name=f"AdGroup {camp_id}",
                        audience_segment=rng.choice(segments).segment_id,
                    )
                )

                cr_fmt = rng.choice(["banner", "native", "video", "sponsored_product"])
                cr_id = f"cr_{camp_id}"
                creatives.append(
                    CreativeAsset(
                        creative_id=cr_id,
                        creative_format=cr_fmt,  # type: ignore[arg-type]
                        duration_seconds=30 if cr_fmt == "video" else None,
                    )
                )
                ads.append(
                    Advertisement(
                        ad_id=f"ad_{camp_id}",
                        ad_group_id=ag_id,
                        campaign_id=camp_id,
                        creative_id=cr_id,
                        product_id=prod_id,
                    )
                )

        publishers: list[Publisher] = []
        placements: list[Placement] = []
        pub_types: tuple[str, ...] = ("web", "mobile_app", "ctv", "retail_site", "search")
        channels: tuple[str, ...] = ("display", "video", "search", "sponsored_listing")

        for p_idx in range(1, self.config.num_publishers + 1):
            pub_id = f"pub_{p_idx:04d}"
            publishers.append(
                Publisher(
                    publisher_id=pub_id,
                    name=f"Publisher {p_idx:04d}",
                    platform_type=pub_types[(p_idx - 1) % len(pub_types)],  # type: ignore[arg-type]
                    rev_share_bps=7000,
                )
            )
            for slot in range(1, 3):
                country, _ = _COUNTRIES[(p_idx + slot) % len(_COUNTRIES)]
                placements.append(
                    Placement(
                        placement_id=f"plc_{p_idx:04d}_{slot}",
                        publisher_id=pub_id,
                        channel=channels[(p_idx + slot) % len(channels)],  # type: ignore[arg-type]
                        country=country,
                    )
                )

        catalog = AdStreamCatalog(
            agencies=agencies,
            advertisers=advertisers,
            accounts=accounts,
            campaigns=campaigns,
            ad_groups=ad_groups,
            creatives=creatives,
            ads=ads,
            products=products,
            publishers=publishers,
            placements=placements,
            segments=segments,
        )
        catalog.campaign_by_id = {c.campaign_id: c for c in campaigns}
        catalog.publisher_by_id = {p.publisher_id: p for p in publishers}
        for ad in ads:
            catalog.ads_by_campaign.setdefault(ad.campaign_id, []).append(ad)
        for plc in placements:
            catalog.placements_by_publisher.setdefault(plc.publisher_id, []).append(plc)
        return catalog

    def _pick_skewed_campaign(self, catalog: AdStreamCatalog) -> Campaign:
        hot_cutoff = max(1, len(catalog.campaigns) // 5)
        if self._rng.random() < self.config.skew_top_share:
            return self._rng.choice(catalog.campaigns[:hot_cutoff])
        return self._rng.choice(catalog.campaigns)

    def _pick_skewed_publisher(self, catalog: AdStreamCatalog) -> Publisher:
        hot_cutoff = max(1, len(catalog.publishers) // 5)
        if self._rng.random() < self.config.skew_top_share:
            return self._rng.choice(catalog.publishers[:hot_cutoff])
        return self._rng.choice(catalog.publishers)

    def _to_ecosystem_payload(
        self,
        *,
        source: SourceSystem,
        seq_id: str,
        event_type: str,
        event_time: datetime,
        campaign: Campaign,
        ad: Advertisement,
        publisher: Publisher,
        placement: Placement,
        cost_micros: int,
        schema_version: int,
        impression_id: str | None = None,
        click_id: str | None = None,
        revenue_micros: int = 0,
        quartile: str | None = None,
        user_ip_hash: str | None = None,
    ) -> dict[str, Any]:
        ts_iso = event_time.isoformat()
        device = self._rng.choice(_DEVICES)
        if source == SourceSystem.GOOGLE_ADS:
            payload: dict[str, Any] = {
                "googleEventId": seq_id,
                "kind": event_type,
                "schemaVersion": schema_version,
                "timestampUtc": ts_iso,
                "customerId": campaign.advertiser_id,
                "campaignId": campaign.campaign_id,
                "adGroupId": ad.ad_group_id,
                "adId": ad.ad_id,
                "publisherId": publisher.publisher_id,
                "placementId": placement.placement_id,
                "geoCountry": placement.country,
                "device": device,
                "currencyCode": campaign.currency.value,
                "costMicros": cost_micros,
                "gclid": f"gclid_{seq_id}",
                "impressionId": impression_id,
                "clickId": click_id,
                "ipHash": user_ip_hash,
                "conversionValueMicros": revenue_micros,
            }
            if schema_version >= 2:
                payload["creativeFormat"] = "banner"
            return payload

        if source == SourceSystem.YOUTUBE_ADS:
            return {
                "ytEventId": seq_id,
                "eventType": event_type,
                "schemaVersion": schema_version,
                "occurredAt": ts_iso,
                "advertiserId": campaign.advertiser_id,
                "campaignId": campaign.campaign_id,
                "videoAdId": ad.ad_id,
                "creativeId": ad.creative_id,
                "channelPublisherId": publisher.publisher_id,
                "placementId": placement.placement_id,
                "country": placement.country,
                "deviceType": "ctv" if device == "ctv" else "mobile",
                "currency": campaign.currency.value,
                "costMicros": cost_micros,
                "cpvMicros": cost_micros,
                "videoQuartile": quartile or "start",
                "impressionId": impression_id,
                "videoId": f"vid_{ad.creative_id}",
            }

        if source == SourceSystem.AMAZON_ADS:
            return {
                "amznEventId": seq_id,
                "eventType": event_type,
                "schemaVersion": schema_version,
                "eventTimestamp": ts_iso,
                "sellerAccountId": campaign.advertiser_id,
                "campaignId": campaign.campaign_id,
                "adGroupId": ad.ad_group_id,
                "asin": ad.product_id or "B0000001",
                "marketplacePublisherId": publisher.publisher_id,
                "marketplaceCountry": placement.country,
                "device": device,
                "currency": campaign.currency.value,
                "spendsMicros": cost_micros,
                "clickId": click_id,
                "attributedSalesMicros": revenue_micros,
                "searchTerm": "wireless headphones" if self._rng.random() > 0.3 else None,
            }

        if source == SourceSystem.META_ADS:
            return {
                "fbEventId": seq_id,
                "eventName": event_type,
                "schemaVersion": schema_version,
                "eventTime": ts_iso,
                "adAccountId": campaign.advertiser_id,
                "campaignId": campaign.campaign_id,
                "adsetId": ad.ad_group_id,
                "adId": ad.ad_id,
                "surface": publisher.publisher_id,
                "country": placement.country,
                "platformDevice": device,
                "currency": campaign.currency.value,
                "spendMicros": cost_micros,
                "clickId": click_id,
                "valueMicros": revenue_micros,
                "fbp": f"fb.1.{seq_id}",
            }

        if source == SourceSystem.RETAIL_MEDIA:
            return {
                "rmnEventId": seq_id,
                "eventType": event_type,
                "schemaVersion": schema_version,
                "timestamp": ts_iso,
                "brandId": campaign.advertiser_id,
                "campaignId": campaign.campaign_id,
                "skuId": ad.product_id or "SKU_001",
                "retailerId": publisher.publisher_id,
                "placementSlot": placement.placement_id,
                "country": placement.country,
                "device": device,
                "currency": campaign.currency.value,
                "chargeMicros": cost_micros,
                "clickId": click_id,
                "basketMicros": revenue_micros,
            }

        return {
            "exchangeEventId": seq_id,
            "eventType": event_type,
            "schemaVersion": schema_version,
            "ts": ts_iso,
            "seatId": campaign.advertiser_id,
            "campaignId": campaign.campaign_id,
            "sspPublisherId": publisher.publisher_id,
            "tagId": placement.placement_id,
            "country": placement.country,
            "deviceType": device,
            "cur": campaign.currency.value,
            "clearingMicros": cost_micros,
            "auctionId": f"auc_{seq_id}",
        }

    def stream_raw_events(
        self, total_events: int, catalog: AdStreamCatalog | None = None
    ) -> Iterator[tuple[SourceSystem, dict[str, Any]]]:
        """
        Yield up to `total_events` (source_system, raw_payload) tuples lazily in O(1) memory.

        Maintains relational coherence: clicks reference generated impressions, and
        conversions trace back to generated clicks/impressions.
        """
        cat = catalog or self.build_catalog()
        recent_for_duplication: list[tuple[SourceSystem, dict[str, Any]]] = []
        emitted = 0
        seq = 0
        fraud_ip_hash = "ip_bot_cluster_99"

        while emitted < total_events:
            # Periodic duplicate retry injection
            if recent_for_duplication and self._rng.random() < self.config.duplicate_rate:
                yield self._rng.choice(recent_for_duplication)
                emitted += 1
                continue

            seq += 1
            campaign = self._pick_skewed_campaign(cat)
            ad = self._rng.choice(cat.ads_by_campaign[campaign.campaign_id])
            publisher = self._pick_skewed_publisher(cat)
            placement = self._rng.choice(cat.placements_by_publisher[publisher.publisher_id])
            source = self._rng.choice(_SOURCES)

            # Temporal spike + out-of-order/late arrival jitter
            offset_sec = seq // 10
            if self._rng.random() < self.config.late_event_rate:
                offset_sec -= self._rng.randint(400, 1200)  # arrives 6-20 min behind watermark
            event_time = self.config.base_time + timedelta(seconds=offset_sec)

            # Breaking schema version injection
            if self._rng.random() < self.config.breaking_schema_rate:
                bad_schema = {"googleEventId": f"badver_{seq}", "kind": "impression", "schemaVersion": 99}
                yield (SourceSystem.GOOGLE_ADS, bad_schema)
                emitted += 1
                continue

            # Malformed / missing required field injection
            if self._rng.random() < self.config.malformed_rate:
                malformed = {
                    "googleEventId": f"bad_{seq}",
                    "kind": "click",
                    "costMicros": "not_an_int",
                    "timestampUtc": event_time.isoformat(),
                }
                yield (SourceSystem.GOOGLE_ADS, malformed)
                emitted += 1
                continue

            schema_version = 2 if self._rng.random() < 0.25 else 1
            imp_seq = f"imp_{seq}"
            imp_cost = self._rng.randint(500, 5_000)

            imp_payload = self._to_ecosystem_payload(
                source=source,
                seq_id=imp_seq,
                event_type="impression",
                event_time=event_time,
                campaign=campaign,
                ad=ad,
                publisher=publisher,
                placement=placement,
                cost_micros=imp_cost,
                schema_version=schema_version,
            )
            yield (source, imp_payload)
            emitted += 1
            if len(recent_for_duplication) < 128:
                recent_for_duplication.append((source, imp_payload))
            else:
                recent_for_duplication[seq % 128] = (source, imp_payload)

            if emitted >= total_events:
                break

            # Fraudulent click burst simulation
            if self._rng.random() < self.config.fraud_burst_rate:
                burst_size = min(15, total_events - emitted)
                for b in range(burst_size):
                    clk_seq = f"fraud_clk_{seq}_{b}"
                    fraud_payload = self._to_ecosystem_payload(
                        source=SourceSystem.GOOGLE_ADS,
                        seq_id=clk_seq,
                        event_type="click",
                        event_time=event_time + timedelta(seconds=1),
                        campaign=campaign,
                        ad=ad,
                        publisher=publisher,
                        placement=placement,
                        cost_micros=250_000,
                        schema_version=1,
                        impression_id=f"gads_{imp_seq}" if source == SourceSystem.GOOGLE_ADS else imp_seq,
                        user_ip_hash=fraud_ip_hash,
                    )
                    yield (SourceSystem.GOOGLE_ADS, fraud_payload)
                    emitted += 1
                continue

            # Coherent video quartile event for YouTube impressions
            if source == SourceSystem.YOUTUBE_ADS and self._rng.random() < 0.4 and emitted < total_events:
                vid_payload = self._to_ecosystem_payload(
                    source=SourceSystem.YOUTUBE_ADS,
                    seq_id=f"vid_{seq}",
                    event_type="video_interaction",
                    event_time=event_time + timedelta(seconds=5),
                    campaign=campaign,
                    ad=ad,
                    publisher=publisher,
                    placement=placement,
                    cost_micros=50_000,
                    schema_version=schema_version,
                    impression_id=f"yt_{imp_seq}",
                    quartile="complete",
                )
                yield (SourceSystem.YOUTUBE_ADS, vid_payload)
                emitted += 1

            # Coherent click referencing the impression (~18% CTR in synthetic test traffic)
            if self._rng.random() < 0.18 and emitted < total_events:
                clk_seq = f"clk_{seq}"
                clk_cost = self._rng.randint(50_000, 400_000)
                clk_source = source if source != SourceSystem.YOUTUBE_ADS else SourceSystem.GOOGLE_ADS
                clk_payload = self._to_ecosystem_payload(
                    source=clk_source,
                    seq_id=clk_seq,
                    event_type="click",
                    event_time=event_time + timedelta(seconds=2),
                    campaign=campaign,
                    ad=ad,
                    publisher=publisher,
                    placement=placement,
                    cost_micros=clk_cost,
                    schema_version=schema_version,
                    impression_id=f"{_SOURCE_PREFIX[source]}_{imp_seq}",
                    user_ip_hash=f"ip_user_{seq % 500}",
                )
                yield (clk_source, clk_payload)
                emitted += 1

                # Coherent conversion attributed back to click (~20% of clicks convert)
                if (
                    clk_source in (SourceSystem.GOOGLE_ADS, SourceSystem.AMAZON_ADS, SourceSystem.META_ADS, SourceSystem.RETAIL_MEDIA)
                    and self._rng.random() < 0.20
                    and emitted < total_events
                ):
                    conv_payload = self._to_ecosystem_payload(
                        source=clk_source,
                        seq_id=f"conv_{seq}",
                        event_type="conversion",
                        event_time=event_time + timedelta(seconds=30),
                        campaign=campaign,
                        ad=ad,
                        publisher=publisher,
                        placement=placement,
                        cost_micros=0,
                        schema_version=schema_version,
                        click_id=f"{_SOURCE_PREFIX[clk_source]}_{clk_seq}",
                        impression_id=f"{_SOURCE_PREFIX[source]}_{imp_seq}",
                        revenue_micros=self._rng.randint(5_000_000, 80_000_000),
                    )
                    yield (clk_source, conv_payload)
                    emitted += 1
