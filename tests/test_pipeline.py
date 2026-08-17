from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from alphaforge.data import normalize_ohlcv
from alphaforge.pipeline import load_pipeline_config, run_pipeline


def test_baseline_config_loading() -> None:
    config = load_pipeline_config(Path("configs/baseline.toml"))

    assert config["data"]["processed_path"] == (
        "data/processed/ohlcv_hfq.parquet"
    )
    assert config["factors"] == {
        "momentum_window": 20,
        "reversal_window": 5,
        "volatility_window": 20,
    }
    assert config["research"]["forward_horizon"] == 1
    assert config["research"]["n_quantiles"] == 5
    assert config["portfolio"] == {
        "factor": "momentum_20d",
        "n_quantiles": 5,
    }
    assert config["backtest"] == {
        "transaction_cost_bps": 5.0,
        "slippage_bps": 5.0,
    }
    assert config["analytics"]["periods_per_year"] == 252


def test_tiny_deterministic_end_to_end_pipeline(tmp_path: Path) -> None:
    dates = pd.bdate_range("2024-01-02", periods=35)
    symbols = [
        "600000.SH",
        "600001.SH",
        "600002.SH",
        "000001.SZ",
        "000002.SZ",
        "000004.SZ",
    ]
    rows = []
    for day, date in enumerate(dates):
        for number, symbol in enumerate(symbols):
            close = (
                20.0
                + number
                + day * (number + 1) / 100.0
                + np.sin(day / (number + 2)) / 10.0
            )
            rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "open": close * 0.99,
                    "high": close * 1.01,
                    "low": close * 0.98,
                    "close": close,
                    "volume": 1_000.0 + number,
                }
            )

    data_path = tmp_path / "ohlcv.parquet"
    normalize_ohlcv(pd.DataFrame(rows)).to_parquet(data_path, index=False)
    config = load_pipeline_config(Path("configs/baseline.toml"))
    config["data"]["processed_path"] = str(data_path)

    result = run_pipeline(config)

    assert set(result.factor_research) == {
        "momentum_20d",
        "reversal_5d",
        "volatility_20d",
    }
    for research in result.factor_research.values():
        assert not research.daily_ic.empty
        assert not research.quantile_returns.empty
        assert not research.ic_summary.empty
        assert not research.quantile_summary.empty
    assert not result.factor_correlation.empty
    assert not result.factor_data.empty
    assert not result.portfolio.empty
    assert not result.positions.empty
    assert not result.daily_backtest.empty
    assert result.factor_data["date"].is_monotonic_increasing
    assert result.daily_backtest["date"].is_monotonic_increasing
    assert result.daily_backtest["date"].is_unique
    assert np.isfinite(result.daily_backtest["net_return"]).all()
    assert np.isfinite(result.daily_backtest["nav"]).all()
    assert result.daily_backtest["nav"].gt(0.0).all()
    assert set(result.performance.index) == {
        "annualized_return",
        "annualized_volatility",
        "sharpe_ratio",
        "max_drawdown",
        "total_turnover",
        "average_daily_turnover",
        "annualized_turnover",
        "ending_nav",
        "cumulative_return",
    }
    assert result.portfolio.loc[
        result.portfolio["is_rebalance"], "date"
    ].nunique() > 0
    assert result.daily_backtest["is_execution"].sum() > 0
