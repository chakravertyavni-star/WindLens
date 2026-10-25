"""Elexon Insights API client using only verified query parameters."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ElexonClient:
    def __init__(self, base_url: str, timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get_stream(self, path: str, params: dict[str, str]) -> list[dict[str, Any]]:
        url = f"{self.base_url}{path}"
        logger.info("Elexon GET %s params=%s", url, params)
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(url, params=params, headers={"Accept": "application/json"})
            response.raise_for_status()
            data = response.json()
        if not isinstance(data, list):
            raise TypeError(f"Expected JSON array from {path}, got {type(data).__name__}")
        return data

    def fetch_fuelhh_wind(
        self,
        settlement_date_from: date,
        settlement_date_to: date,
    ) -> list[dict[str, Any]]:
        return self._get_stream(
            "/datasets/FUELHH/stream",
            {
                "settlementDateFrom": settlement_date_from.isoformat(),
                "settlementDateTo": settlement_date_to.isoformat(),
                "fuelType": "WIND",
            },
        )

    def fetch_windfor_by_publish_window(
        self,
        publish_datetime_from: str,
        publish_datetime_to: str,
    ) -> list[dict[str, Any]]:
        return self._get_stream(
            "/datasets/WINDFOR/stream",
            {
                "publishDateTimeFrom": publish_datetime_from,
                "publishDateTimeTo": publish_datetime_to,
            },
        )
