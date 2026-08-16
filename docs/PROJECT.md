# AlphaForge — Cross-Sectional Quant Research & Backtesting Engine

## 项目定位

AlphaForge 是面向 **Quant Developer 求职** 的 interview-oriented quant engineering project。

目标岗位：

1. P0：Strategy / Research + Platform QD
2. P1：Strategy / Research QD
3. P2：Research Platform / Backtest / Data Infra QD

核心流程：

```text
Market Data → Factor → Signal → Portfolio → Execution → PnL → Metrics
```

项目目标不是追求高收益，而是展示：

- Python quant engineering
- factor research workflow
- backtesting
- data processing
- portfolio construction
- correctness / bias awareness
- transaction cost / slippage
- performance optimization
- 后续 C++ 扩展能力

## MVP Scope

### Data

- A 股日频
- 100–300 stocks
- 约 5 年数据
- OHLCV
- 本地 Parquet

### Factors

第一阶段只做：

- 20-day Momentum
- 5-day Reversal
- 20-day Volatility

### Research

- Cross-sectional rank（横截面排序）
- Forward return
- Spearman IC
- ICIR
- Quantile return
- Factor correlation

### Portfolio

- Weekly rebalance
- Long only
- Top quantile
- Equal weight

### Backtest

默认时间逻辑：

```text
signal(t) → trade / position(t+1) → future return
```

必须处理：

- turnover
- transaction cost
- slippage
- portfolio return
- cumulative PnL

### Metrics

- Annualized return
- Volatility
- Sharpe
- Max drawdown
- Turnover
- IC / ICIR

## 项目架构

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

Repo 大致保持：

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

Notebook 只负责研究和可视化，核心逻辑放在 `src/`。

## 开发原则

- **Correctness > Return**
- **Quant + Engineering，而不是纯 Notebook 或普通 Backend**
- **先实现简单、正确的 Python，再 profiling，再根据真实 bottleneck 考虑 C++**

项目必须能讨论：

- look-ahead bias（前视偏差）
- survivorship bias（幸存者偏差）
- overfitting / data snooping
- transaction cost
- slippage
- data quality
- factor timing

## Explicitly Out of Scope

- ML / Deep Learning
- LLM / Agent
- tick / order book / HFT
- live trading
- matching engine
- complex optimizer
- distributed system
- 大量 factors

任何新功能加入前先问：

> 是否明显增加 QD 面试价值？

否则不做。

## 最终成果

项目完成后应具备：

- 一个可运行 GitHub repo
- 一条命令跑完整 baseline
- 完整 data → PnL workflow
- 三个基础 factors
- factor research report
- backtest results
- correctness tests
- README + architecture
- 一个真实 performance optimization story
- 最好有一个 C++ / pybind11 优化模块
- 可以支撑 10–30 分钟项目 deep dive

## Python environment:
- This project uses uv for dependency and environment management.
- Codex cannot run `uv` because of sandbox/permission restrictions, do not modify or recreate the project environment. Report the limitation and provide the exact `uv run ...` command for the user to execute locally.
- Do not use pip directly unless explicitly requested.
- Do not create or use an alternative project environment.
