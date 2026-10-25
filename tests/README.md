# Tests

```bash
python -m pip install -r requirements.txt
python -m pytest -m "not integration"
python -m pytest -m integration
```

Unit tests use **synthetic** data labelled in fixtures (not Elexon). The integration test calls the live public Elexon API for January 2026.
