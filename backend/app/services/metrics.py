"""Forecast accuracy metrics on matched pairs only."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class MetricResult:
    n: int
    mae: float | None
    rmse: float | None
    bias: float | None

    def as_dict(self) -> dict:
        return {
            "n": self.n,
            "mae": self.mae,
            "rmse": self.rmse,
            "bias": self.bias,
        }


def compute_errors(matched: pd.DataFrame) -> pd.Series:
    """forecast error = forecast generation - actual generation."""
    if matched.empty:
        return pd.Series(dtype=float)
    return matched["forecast_mw"] - matched["actual_mw"]


def compute_metrics(matched: pd.DataFrame) -> MetricResult:
    valid = matched.dropna(subset=["forecast_mw", "actual_mw"])
    n = len(valid)
    if n == 0:
        return MetricResult(n=0, mae=None, rmse=None, bias=None)
    errors = compute_errors(valid)
    mae = float(np.abs(errors).mean())
    rmse = float(np.sqrt((errors**2).mean()))
    bias = float(errors.mean())
    return MetricResult(n=n, mae=mae, rmse=rmse, bias=bias)
