# Data

Status: **No local snapshot has been committed**.

Live Elexon requests succeeded during the 25 October 2026 investigation. The investigation script summarised results in `docs/investigation/elexon_api_probe.json` and did not store a full January WINDFOR archive.

Planned later:

- `raw/` - optional validated historical snapshot if live access is unavailable
- `processed/` - matched forecast/actual tables produced by the backend
- `synthetic/` - labelled synthetic examples for tests only

Never mix synthetic examples with real Elexon observations.
