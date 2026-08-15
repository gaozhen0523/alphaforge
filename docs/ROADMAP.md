# AlphaForge — Four-Week Roadmap

## Week 1 — End-to-End MVP

Goal: run the complete baseline once.

### Day 1 — Data

- Define the market-data schema and loader.
- Download a small OHLCV universe, validate it, and store it as Parquet.

### Day 2 — Factors

- Implement 20-day Momentum, 5-day Reversal, and 20-day Volatility.
- Standardize the factor API and timing semantics.

### Day 3 — Factor Research

- Implement cross-sectional rank, forward returns, IC, ICIR, quantile returns, and factor correlation.
- Produce the first research results.

### Day 4 — Portfolio

- Convert factor values into signals and target weights.
- Implement weekly rebalance, top-quantile selection, and equal weighting.

### Day 5 — Backtest

- Implement position, turnover, cost, return, and PnL accounting.
- Enforce `signal(t) → position(t+1)` timing.

### Day 6 — Analytics & Tests

- Implement annualized return, volatility, Sharpe, max drawdown, and turnover.
- Test timing, weights, costs, and PnL.

### Day 7 — End-to-End

- Connect the config-driven pipeline.
- Run baseline results with one command.

### Week 1 Done

- The full Data → Factor → Research → Portfolio → Backtest → Metrics pipeline runs correctly.
- Critical timing and accounting behavior is tested.

## Week 2 — Resume-Ready MVP

Goal: make the baseline credible, reproducible, and presentable.

### Day 8 — Data Quality

- Add missing, duplicate, and invalid-data checks.
- Document adjustment and suspension rules.

### Day 9 — Research Robustness

- Analyze factor decay and multiple forward horizons.
- Check result stability.

### Day 10 — Out-of-Sample

- Add chronological train / validation / test splits.
- Document controls for overfitting and data snooping.

### Day 11 — Cost Analysis

- Run transaction-cost and slippage sensitivity analysis.
- Measure the effect of turnover on returns.

### Day 12 — Factor Combination

- Combine only the three MVP factors using simple rank or z-score methods.
- Do not introduce ML or additional factors.

### Day 13 — Engineering Cleanup

- Refine APIs, configuration, logging, and tests.
- Verify reproducible runs.

### Day 14 — Resume Ready

- Complete the README, architecture diagram, results, and limitations.
- Draft resume bullets and the project summary.

### Week 2 Done

- Results are reproducible and supported by data-quality, robustness, out-of-sample, and cost analysis.
- The repository is ready for GitHub presentation, resume use, and an interview walkthrough.

## Week 3 — Performance & Depth

Goal: build genuine Quant Developer technical depth.

### Day 15 — Profiling

- Identify CPU and memory bottlenecks.
- Record a reproducible baseline benchmark.

### Day 16 — Python Optimization

- Optimize a measured bottleneck with appropriate Python, NumPy, vectorization, or caching techniques.
- Compare correctness and performance before and after.

### Day 17 — C++ Integration

- Select a real remaining hot path only if profiling justifies C++.
- Implement it with C++17 and pybind11, or document why C++ is not warranted.

### Day 18 — Benchmark

- Compare baseline Python, optimized Python, and C++ when applicable.
- Explain performance and maintenance trade-offs.

### Day 19 — Bias Deep Dive

- Audit look-ahead, survivorship, and overfitting risks.
- Connect each risk to concrete project behavior.

### Day 20 — Quant Deep Dive

- Deepen understanding of IC, factor decay, Sharpe, turnover, and drawdown.
- Prepare clear explanations of formulas and intuition.

### Day 21 — Project Mock

- Conduct a full project deep dive.
- Identify and close important design or knowledge gaps.

### Week 3 Done

- The project supports one quant research story, one correctness story, and one evidence-based performance story.
- Any C++ work is justified by profiling and verified against Python results.

## Week 4 — Interview Conversion

Goal: freeze scope and convert the project into interview-ready material.

### Day 22 — Scope Freeze

- Stop adding major features.
- Fix only important bugs, correctness issues, and presentation gaps.

### Day 23 — Architecture Story

- Prepare the architecture walkthrough.
- Explain module boundaries and design trade-offs.

### Day 24 — Quant Story

- Practice the factor → signal → position → PnL narrative.
- Explain research and backtest results.

### Day 25 — Correctness Story

- Prepare for questions about timing, bias, costs, and data quality.

### Day 26 — Performance Story

- Present the profiling → optimization → benchmark sequence, including C++ only if used.

### Day 27 — Resume / GitHub Final

- Finalize resume bullets.
- Polish the README and final results.

### Day 28 — Full Mock

- Run a complete Quant Developer project interview simulation.
- Finalize the project question bank.

### Week 4 Done

- The repository and resume materials are final and scope-frozen.
- A clear 10–30 minute project deep dive covers architecture, quant research, correctness, and performance.
