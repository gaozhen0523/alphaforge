"""Build and inspect the production weekly baseline target portfolio."""

from __future__ import annotations

from pathlib import Path

from alphaforge.data import MarketDataLoader
from alphaforge.factors import momentum
from alphaforge.portfolio import build_long_only_top_quantile_portfolio

DATA_PATH = Path("data/processed/ohlcv_hfq.parquet")


def main() -> None:
    df = MarketDataLoader(DATA_PATH).load()
    df["momentum_20d"] = momentum(df, window=20)
    portfolio = build_long_only_top_quantile_portfolio(df, "momentum_20d")

    rebalance_dates = portfolio.loc[
        portfolio["is_rebalance"], "date"
    ].drop_duplicates()
    selected_count = (
        portfolio.loc[portfolio["is_rebalance"]]
        .groupby("date")["signal"]
        .sum()
    )
    weight_sum = portfolio.groupby("date")["target_weight"].sum()
    active_weight_sum = weight_sum.loc[weight_sum.gt(0.0)]
    non_unit_active_dates = int(
        active_weight_sum.sub(1.0).abs().gt(1e-12).sum()
    )

    print("Production target portfolio")
    print(f"dataset: {DATA_PATH}")
    print(f"rows: {len(portfolio):,}")
    print(f"symbols: {portfolio['symbol'].nunique():,}")
    print(
        f"date range: {portfolio['date'].min().date()} to "
        f"{portfolio['date'].max().date()}"
    )
    print(f"rebalance count: {len(rebalance_dates):,}")
    print(f"first rebalance date: {rebalance_dates.iloc[0].date()}")
    print(f"last rebalance date: {rebalance_dates.iloc[-1].date()}")
    print(
        "selected count on rebalance dates "
        f"(min/median/max): {int(selected_count.min())}/"
        f"{selected_count.median():.1f}/{int(selected_count.max())}"
    )
    print(
        "target weight (min/max): "
        f"{portfolio['target_weight'].min():.8f}/"
        f"{portfolio['target_weight'].max():.8f}"
    )
    print(
        "negative weight count: "
        f"{int(portfolio['target_weight'].lt(0.0).sum()):,}"
    )
    print(
        "active cross-sectional weight sum (min/max): "
        f"{active_weight_sum.min():.12f}/{active_weight_sum.max():.12f}"
    )
    print(f"non-unit active dates: {non_unit_active_dates:,}")


if __name__ == "__main__":
    main()
