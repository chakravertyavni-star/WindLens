# Scripts

## generate_report.py

Creates `docs/PROJECT_REPORT.pdf` from `docs/PROJECT_REPORT.md`.

```bash
python -m pip install -r requirements-docs.txt
python scripts/generate_report.py
```

The PDF includes a title page, the Markdown body, and native drawings for the five architecture diagrams.

## start-backend.ps1 / start-frontend.ps1

Windows helpers for local WindLens development. Backend port is configured in `dev.env` (default 8001); frontend proxy in `frontend/.env.development`.

## investigate_elexon_api.py

Probes the public Elexon Insights API with documented parameters and writes `docs/investigation/elexon_api_probe.json`.

```bash
python scripts/investigate_elexon_api.py
```

This script does not fabricate records. If the network request fails, the JSON will contain the error.
