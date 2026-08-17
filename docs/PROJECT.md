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

- Baseline factor：`momentum_20d`，higher factor is better
- Weekly rebalance：每个 calendar week 最后一个 global trading date
- Long only、top quintile / Q5、equal weight
- Portfolio Q5 复用 Research Q5 quantile semantics；factor NaN 不参与 selection，ties 不强制拆分
- Portfolio panel：完整 `global date × symbol`；缺失 observation 的 factor 保留 NaN

Portfolio timing boundary：

```text
factor(t) → signal(t) → target_weight(t)
```

`signal` / `target_weight` 只在 weekly rebalance decision 更新，其余日期 carry forward。`target_weight` 是当前目标配置，不是 actual portfolio weight；carry forward 不表示每日重新交易维持 equal weight。Execution、actual position、weight drift、turnover、cost、return 和 PnL 属于 Backtest layer。

### Backtest

默认时间逻辑：

```text
factor(t) → target_weight(t) → next global trading-date close execution
```

每日先由 previous post-trade weights 承担当日 close-to-close return，再计算
drifted pre-trade weights；若当日有 delayed execution event，才从 pre-trade
weights 交易到上一 global trading date 的 decision target。Carry-forward target
不表示 daily rebalance，`target_weight` 与 actual portfolio weight 必须区分。

Unbalanced panel 使用 past-only forward-filled close marking；缺失 observation
当天 return 为 0，下次真实 close 出现时一次性体现累计价格变化。Week 1 execution
假设可按 marked close 成交，不模拟 suspension、limit up/down、liquidity 或 market
impact。

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

## Development / Collaboration Workflow

后续开发减少任务过度碎片化。优先先理解完整 Quant 子流程、讲清核心知识和 correctness semantics，再一次实现一组相关 functions + tests 并统一 review。通常每个开发日控制在 1～2 个 cohesive coding batches；只有遇到重要的 correctness 或 architecture boundary 时再拆分。

例如 Day 4 的 `factor → signal → target weights` 应尽量作为完整 Portfolio flow 实现；Day 5 的 `position → turnover → cost → return → PnL` 也应优先整体设计和实现。

### Learning Priority

Quant、流程和设计知识讲解不能减少。重点帮助用户理解并能在面试中解释完整链路：

```text
Market Data
→ Factor
→ Signal
→ Portfolio
→ Execution
→ PnL
→ Metrics
```

重点解释每层职责、数学与金融直觉、timing semantics、数据流、bias / leakage 风险、重要 trade-off，以及 Quant Developer 面试可能如何追问。减少对 pandas corner cases、obscure dtype behavior、极少发生的 artificial edge cases 和缺少 Quant correctness 价值的 defensive validation 的强调。

### Engineering Detail Priority

必须认真保护 look-ahead bias、factor / signal / execution timing、symbol/date alignment、cross-sectional vs time-series semantics、forward-return alignment、survivorship / membership bias、data leakage、meaningful missing-data semantics、portfolio weights、turnover、transaction cost、slippage、return / PnL accounting、reproducibility 和真实 performance bottlenecks。

低价值 edge cases 优先记录 assumption / limitation，不为其增加大量实现复杂度。

### Tests

优先少量但强的 Quant correctness tests，重点覆盖 timing、alignment、grouping boundary、no look-ahead、portfolio invariants、turnover / cost 和 return accounting。避免为增加 test 数量堆积低价值 API edge cases。

### Implementation Style

继续遵循：

```text
simple correct Python
→ production run
→ profiling
→ optimize real bottlenecks
→ C++ / pybind11 only if profiling justifies it
```

坚持 `Correctness > Return`，不为获得漂亮 IC / Sharpe / PnL 进行 data snooping 或修改 baseline definitions。

已知 Codex sandbox 无法运行 `uv`，不使用 pip、不创建替代环境、不修改 dependency management，只提供准确的本地 `uv run ...` 命令。

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
