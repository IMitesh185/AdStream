from pathlib import Path

from adstream.adapters.ecosystems import create_default_registry
from adstream.domain.models import (
    ClickEvent,
    ConversionEvent,
    ImpressionEvent,
    SourceSystem,
    VideoInteractionEvent,
)
from adstream.ingestion.quarantine import QuarantineSink
from adstream.ingestion.validator import IngestionValidator


def test_multi_ecosystem_adapters_preserve_raw_payloads() -> None:
    reg = create_default_registry()

    g = reg.parse(
        SourceSystem.GOOGLE_ADS,
        {
            "googleEventId": "g_1",
            "kind": "impression",
            "schemaVersion": 2,
            "timestampUtc": "2026-11-18T12:00:00Z",
            "customerId": "adv_1",
            "campaignId": "camp_1",
            "geoCountry": "us",
            "costMicros": 1500,
            "creativeFormat": "banner",
        },
    )
    assert isinstance(g, ImpressionEvent)
    assert g.country == "US"
    assert g.raw_payload["googleEventId"] == "g_1"

    yt = reg.parse(
        SourceSystem.YOUTUBE_ADS,
        {
            "ytEventId": "y_1",
            "eventType": "video_interaction",
            "occurredAt": "2026-11-18T12:00:05Z",
            "advertiserId": "adv_1",
            "campaignId": "camp_1",
            "country": "GB",
            "videoQuartile": "complete",
            "cpvMicros": 50_000,
        },
    )
    assert isinstance(yt, VideoInteractionEvent)
    assert yt.is_billable is True

    amzn = reg.parse(
        SourceSystem.AMAZON_ADS,
        {
            "amznEventId": "a_1",
            "eventType": "conversion",
            "eventTimestamp": "2026-11-18T12:01:00Z",
            "sellerAccountId": "adv_1",
            "campaignId": "camp_1",
            "marketplaceCountry": "US",
            "attributedSalesMicros": 25_000_000,
        },
    )
    assert isinstance(amzn, ConversionEvent)
    assert amzn.revenue_micros == 25_000_000

    meta = reg.parse(
        SourceSystem.META_ADS,
        {
            "fbEventId": "m_1",
            "eventName": "click",
            "eventTime": "2026-11-18T12:00:10Z",
            "adAccountId": "adv_1",
            "campaignId": "camp_1",
            "country": "IN",
            "spendMicros": 40_000,
        },
    )
    assert isinstance(meta, ClickEvent)
    assert meta.cost_micros == 40_000


def test_quarantine_isolates_malformed_and_breaking_schema(tmp_path: Path) -> None:
    qpath = tmp_path / "quarantine.jsonl"
    validator = IngestionValidator(quarantine=QuarantineSink(qpath))

    items = [
        (
            SourceSystem.GOOGLE_ADS,
            {
                "googleEventId": "ok_1",
                "kind": "impression",
                "schemaVersion": 1,
                "timestampUtc": "2026-11-18T12:00:00Z",
                "customerId": "adv_1",
                "campaignId": "camp_1",
                "geoCountry": "US",
                "costMicros": 1000,
            },
        ),
        (
            SourceSystem.GOOGLE_ADS,
            {"googleEventId": "bad_ver", "kind": "impression", "schemaVersion": 99},
        ),
        (
            SourceSystem.GOOGLE_ADS,
            {"googleEventId": "bad_cost", "kind": "click", "costMicros": "free"},
        ),
    ]
    res = validator.validate_stream(items)
    assert len(res.accepted) == 1
    assert len(res.quarantined) == 2
    assert len(validator.quarantine.read_persisted()) == 2
    reasons = validator.quarantine.summary_by_reason()
    assert reasons["UNSUPPORTED_SCHEMA_VERSION"] == 1
    assert reasons["INVALID_EVENT"] == 1
