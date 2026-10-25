"""Latest eligible forecast at or before the decision cutoff."""

from __future__ import annotations

import pandas as pd


def select_latest_eligible_forecast(
    forecasts: pd.DataFrame,
    delivery_start: pd.Timestamp,
    cutoff_utc: pd.Timestamp,
) -> pd.Series | None:
    """
    From rows forecasting `delivery_start`, keep publish_time <= cutoff_utc
    and return the row with the latest publish_time.
    """
    if forecasts.empty:
        return None
    subset = forecasts[
        (forecasts["start_time"] == delivery_start)
        & (forecasts["publish_time"] <= cutoff_utc)
    ]
    if subset.empty:
        return None
    idx = subset["publish_time"].idxmax()
    return subset.loc[idx]
