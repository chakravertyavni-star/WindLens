# Elexon API Investigation Findings

Investigation date: 25 October 2026  
Status: **Verified against live Insights API responses**, except where labelled unverified.

Reproducible probe script: `scripts/investigate_elexon_api.py`  
Machine-readable summary: `docs/investigation/elexon_api_probe.json`

## Official documentation used

- Actuals stream: https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream
- Forecast stream: https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream
- API guidance: https://bmrs.elexon.co.uk/api-documentation/guidance
- Wind generation page: https://bmrs.elexon.co.uk/wind-generation
- Developer portal: https://developer.data.elexon.co.uk/

Related WINDFOR pages were read for context only. The assignment analysis will use the two stream datasets above, not demand, price, or other generation datasets.

## Base URL and access

| Item | Verified finding |
| --- | --- |
| Base URL | `https://data.elexon.co.uk/bmrs/api/v1` |
| Authentication | Not required. Public Insights API. |
| Rate limit | Documented as 5,000 requests per minute per user. Not load-tested here. |
| Stream behaviour | Stream endpoints return a JSON array. No page token was observed or documented. Guidance says stream endpoints have no data-volume restriction. |
| Error handling | Failed stream requests may include details in the HTTP trailer. Combined FUELHH filters returned HTTP 400 JSON. |

## FUELHH stream: actual wind generation

`GET /datasets/FUELHH/stream`

### Verified query parameters

| Parameter | Type | Verified? | Notes |
| --- | --- | --- | --- |
| `settlementDateFrom` | date `yyyy-MM-dd` | Yes | Used successfully for January 2026. |
| `settlementDateTo` | date `yyyy-MM-dd` | Yes | Inclusive in the January probe: 2026-01-01 to 2026-01-31 returned all 31 dates. |
| `fuelType` | array of strings | Yes | `fuelType=WIND` returned only WIND rows. |
| `settlementPeriod` | array of integers | Documented, not separately probed | Use later if a single period is needed. |
| `publishDateTimeFrom` / `publishDateTimeTo` | date-time | Documented | Must not be combined with settlement-date filters. |

### Verified restriction

Combining settlement-date and publish-date filters returned HTTP 400:

`The Settlement Date fields cannot be set when a Publish Date field is set.`

### Verified response fields

| Field | Example | Meaning |
| --- | --- | --- |
| `dataset` | `FUELHH` | Dataset name. |
| `publishTime` | `2026-01-01T00:30:00Z` | When this outturn record was published. |
| `startTime` | `2026-01-01T00:00:00Z` | Start of the 30-minute delivery period. |
| `settlementDate` | `2026-01-01` | UK settlement date. |
| `settlementPeriod` | `1` to `48` in January 2026 | Half-hour number on that settlement date. |
| `fuelType` | `WIND` | Fuel category. |
| `generation` | `13756` | Actual generation. Official docs describe FUELHH values as average MW over 30 minutes. |

### January 2026 coverage

Live query:

`/datasets/FUELHH/stream?settlementDateFrom=2026-01-01&settlementDateTo=2026-01-31&fuelType=WIND`

| Check | Result |
| --- | --- |
| HTTP status | 200 |
| Records | 1,488 |
| Settlement dates | 31, from 2026-01-01 to 2026-01-31 |
| Expected half-hours | 31 x 48 = 1,488 |
| Missing settlement periods 1-48 | None |
| Missing `generation` values | 0 |
| Observed generation range | 1,695 MW to 17,805 MW |
| Start-time minutes | 744 ending `:00` and 744 ending `:30` |

January 2026 contains no UK daylight-saving transition, so every settlement date had 48 periods. This will not be true in March or October.

The stream returned the newest settlement period first. Processing code must sort by `startTime` rather than assuming chronological order.

## WINDFOR stream: wind generation forecasts

`GET /datasets/WINDFOR/stream`

### Verified query parameters

| Parameter | Type | Verified? | Notes |
| --- | --- | --- | --- |
| none | - | Yes | Returns only the latest published forecast. Observed 25 October 2026: 74 hourly rows, one `publishTime` of `2026-10-25T11:30:00Z`. |
| `publishDateTimeFrom` | date-time | Yes | Required for historical / superseded forecasts. |
| `publishDateTimeTo` | date-time | Yes | Used with From to bound the publication window. |

No documented `startTime`, `settlementDateFrom`, or `fuelType` filter exists for this stream.

An undocumented `startTime=2026-01-01T00:00:00Z` parameter was sent with a 6-hour publish window. The API still returned HTTP 200 and 146 rows, matching the same publish window without that parameter. **Do not rely on `startTime` as a server-side filter.** January delivery periods must be selected in application code after download.

### Verified response fields

Observed fields only:

| Field | Example | Meaning |
| --- | --- | --- |
| `dataset` | `WINDFOR` | Dataset name. |
| `publishTime` | `2025-12-31T02:30:00Z` | When this forecast version was published. |
| `startTime` | `2026-01-01T00:00:00Z` | Delivery period being forecast. |
| `generation` | `19556` | Forecast generation. Official wind page and related docs describe this as MW. |

The stream response did **not** include `settlementDate` or `settlementPeriod`. Those fields appear on some opinionated `/forecast/generation/wind/*` endpoints, which are out of scope for the quantitative analysis.

### Historical January 2026 forecast availability

Historical forecasts are available.

| Probe | Result |
| --- | --- |
| Publishes on 2025-12-31 | 8 publish times, 584 rows. 368 rows had January 2026 `startTime` values. Start times ran from `2025-12-30T21:00:00Z` to `2026-01-02T21:00:00Z`. |
| Publishes 2026-01-30 00:00Z to 06:00Z | 2 publish times, 146 rows. Start times ran to `2026-02-01T21:00:00Z`, so late-January delivery periods are present. |

Therefore the records required for January 2026 delivery-period analysis exist on the live API. The full January WINDFOR archive was **not** downloaded in this milestone.

### Observed publication clock times

Elexon documents NESO updates at 03:30, 05:30, 08:30, 10:30, 12:30, 16:30, 19:30 and 23:30.

Observed UTC publish times on 31 December 2025:

`02:30`, `04:30`, `07:30`, `09:30`, `11:30`, `15:30`, `18:30`, `22:30`

These are consistently one hour earlier than the documented clock times. Possible explanations include timezone labelling, a documentation offset, or a changed schedule. **Treat the documented clock times as official guidance and the UTC timestamps in the data as the source of truth for selection logic.**

### Resolution mismatch

All investigated WINDFOR `startTime` values ended at minute `:00`. FUELHH values alternate between `:00` and `:30`.

This is a verified analytical issue:

- Forecasts are hourly.
- Actuals are half-hourly.

The planned matching rule is documented in the project report. It has not been implemented yet.

## Timestamp and timezone notes

- All inspected timestamps used ISO-8601 with a `Z` suffix, meaning UTC.
- January 2026 is entirely GMT (`Europe/London` equals UTC). No duplicate or missing settlement period is expected.
- Settlement period 1 on 2026-01-01 started at `2026-01-01T00:00:00Z`.
- Later milestones must still parse timestamps as timezone-aware UTC and convert to `Europe/London` when applying the decision cutoff, because the same code should remain correct around DST changes.

## How January 2026 forecasts will be retrieved

Because WINDFOR can only be filtered by publish time:

1. Request a publish window wide enough to include day-ahead (and earlier) forecasts that mention January start times. A cautious planned window is `2025-12-25T00:00:00Z` to `2026-01-31T23:59:59Z`.
2. Keep only rows whose `startTime` falls in January 2026 delivery periods.
3. Apply the configurable decision cutoff in code.
4. Keep the latest eligible `publishTime` for each delivery `startTime`.

Do not request the unfiltered stream when historical selection is required. That path returns only the latest forecast currently on the platform.

## Fallback strategy if live access fails later

Live access worked on 25 October 2026. If a later environment cannot reach Elexon:

1. Re-run `scripts/investigate_elexon_api.py` and record the error.
2. Download a filtered snapshot with the documented parameters above and store it under `data/raw/` with a provenance note.
3. Point the future client at that snapshot through an environment variable.
4. Never fabricate missing Elexon observations.

## Unknowns

- Exact NESO publication timezone used in the public clock-time schedule.
- Whether WINDFOR hourly values represent the hour starting or ending at `startTime`. The field name and FUELHH analogy suggest the period **starting** at `startTime`, but this is not explicitly proven by a schema description.
- Whether every January delivery hour has at least one forecast published before a given cutoff. That requires the later matching pipeline.
- Client-specific purchasing cutoff. The 09:20 Europe/London default is an assumption.
