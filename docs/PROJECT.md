# AlphaForge — Cross-Sectional Quant Research & Backtesting Engine

## Project Definition

AlphaForge is an interview-oriented quant engineering project for Quant Developer roles. It demonstrates a correct, reproducible cross-sectional factor research and backtesting workflow rather than maximizing strategy return.

## Target Roles

1. P0: Strategy / Research + Platform QD
2. P1: Strategy / Research QD
3. P2: Research Platform / Backtest / Data Infra QD

## Core Pipeline

```text
Market Data → Factor → Signal → Portfolio → Execution → PnL → Metrics
```

## MVP Scope

### Data

- China A-share daily data
- 100–300 stocks over approximately five years
- OHLCV stored locally as Parquet

### Factors

- 20-day Momentum
- 5-day Reversal
- 20-day Volatility

### Research

- Cross-sectional rank and forward returns
- Spearman IC and ICIR
- Quantile returns and factor correlations

### Portfolio

- Weekly rebalance
- Long only, top quantile, equal weight

### Backtest

- Default timing: `signal(t) → trade / position(t+1) → future return`
- Turnover, transaction cost, slippage, portfolio return, and cumulative PnL

### Metrics

- Annualized return, volatility, Sharpe, and max drawdown
- Turnover, IC, and ICIR

## Architecture

```text
Data Layer
    ↓
Factor Engine
    ↓
Research / Signal
    ↓
Portfolio Builder
    ↓
Backtest / Execution
    ↓
Analytics
```

```text
src/alphaforge/
    data/
    factors/
    research/
    portfolio/
    backtest/
    analytics/
configs/
scripts/
tests/
notebooks/
benchmarks/
```

## Development Principles

- Correctness > Return.
- Build quant + engineering depth, not a notebook-only project or a generic backend.
- Keep factor timing and factor / signal / position / trade semantics explicit.
- Address look-ahead bias, survivorship bias, overfitting / data snooping, transaction cost, slippage, and data quality.
- Implement correct Python first, profile it, then consider C++ for a measured bottleneck.
- Keep core logic in `src/`; notebooks are for research and visualization.
- Keep experiments reproducible and test critical financial logic.

## Out of Scope

- ML, deep learning, LLMs, or agents
- Tick data, order books, HFT, live trading, or a matching engine
- Complex optimizers or risk models
- Distributed infrastructure
- Large factor libraries or dependencies without clear interview value

New scope must clearly improve Quant Developer interview value before it is accepted.

## Final Deliverables

- A runnable GitHub repository with one-command baseline execution
- A complete data-to-PnL workflow using the three MVP factors
- Factor research report and backtest results
- Correctness tests, README, and architecture documentation
- One genuine profiling and performance-optimization story
- If profiling justifies it, one C++17 / pybind11 optimization module
- Material sufficient for a 10–30 minute project deep dive
