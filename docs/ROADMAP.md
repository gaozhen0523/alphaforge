# AlphaForge — Four-Week Roadmap

## Week 1 — End-to-End MVP: DONE

目标：

> **先完整跑通一次。**

### Day 1 — Data: DONE

- 建 repo、schema 和 Data Loader。
- 下载小规模 OHLCV，清洗并存 Parquet。

### Day 2 — Factors: DONE

- 实现 Momentum / Reversal / Volatility。
- 统一 factor API 和时间语义。

### Day 3 — Factor Research: DONE

- 实现 rank、forward return、IC、ICIR、quantile analysis。
- 跑出第一版研究结果。

### Day 4 — Portfolio: DONE

- factor → signal → target weights。
- Weekly rebalance、top quantile、equal weight。

### Day 5 — Backtest: DONE

- position → turnover → cost → return → PnL。
- 明确 `signal(t) → position(t+1)`，避免 look-ahead bias（前视偏差）。

### Day 6 — Analytics & Tests: DONE

- 实现 Sharpe、MDD、volatility、turnover 等。
- 测试 timing、weights、cost、PnL。

### Day 7 — End-to-End: DONE

- config 驱动完整 pipeline。
- 一条命令跑出 baseline results。

### Week 1 Done

```text
Data
→ Factor
→ Research
→ Portfolio
→ Backtest
→ Metrics
```

完整可运行。

## Week 2 — Resume-Ready MVP

目标：

> **从“能跑”变成“可信、能写简历”。**

### Day 8 — Data Quality: DONE

- 补 missing / duplicate / invalid data 校验。
- 明确 adjustment、停牌等处理规则。

### Day 9 — Research Robustness: DONE

- factor decay、不同 forward horizon。
- 检查结果稳定性。

### Day 10 — Out-of-Sample: DONE

- time-based train / validation / test split。
- evaluate factor robustness out of sample。
- control overfitting / data snooping。

### Day 11 — Cost Analysis: DONE

- transaction cost / slippage sensitivity。
- 分析 turnover 对收益的影响。

### Day 12 — Factor Combination: DONE

- 做简单 rank / z-score 多因子组合。
- 不引入 ML。

### Day 13 — Engineering Cleanup: DONE

- 清理 API、config、logging、tests。
- 保证实验稳定复现。

### Day 14 — Resume Ready

- README、架构图、结果、limitations。
- 写第一版简历 bullets 和项目介绍。

### Week 2 Done

项目可以正式：

**写简历 + GitHub 展示 + 面试讲。**

## Week 3 — Performance & Depth

目标：

> **增加真正的 QD 技术深度。**

### Day 15 — Profiling

- 找 CPU / memory bottleneck。
- 保存 baseline benchmark。

### Day 16 — Python Optimization

- NumPy / vectorization / cache 等优化。
- 测优化前后性能。

### Day 17 — C++ Integration

- 选择一个真实 hot path。
- 用 C++17 + pybind11 实现。

### Day 18 — Benchmark

- Python vs optimized Python vs C++。
- 分析优化 trade-off。

### Day 19 — Bias Deep Dive

- 系统复习 look-ahead、survivorship、overfitting 等。
- 对照项目找真实案例。

### Day 20 — Quant Deep Dive

- 深挖 IC、factor decay、Sharpe、turnover、drawdown。
- 能解释公式和直觉。

### Day 21 — Project Mock

- 完整做一次项目 deep dive。
- 找出知识和设计薄弱点。

### Week 3 Done

至少形成：

**一个 quant research story + 一个 correctness story + 一个 performance / C++ story。**

## Week 4 — Interview Conversion

目标：

> **停止扩项目，把成果转换成面试能力。**

### Day 22 — Scope Freeze

- 不再新增大功能。
- 只修关键 bug 和 correctness。

### Day 23 — Architecture Story

- 准备项目架构讲解。
- 能解释各模块设计取舍。

### Day 24 — Quant Story

- 熟练讲 factor → signal → position → PnL。
- 能解释实验结果。

### Day 25 — Correctness Story

- 准备 timing、bias、cost、data quality 追问。

### Day 26 — Performance Story

- 准备 profiling → optimization → C++ → benchmark 故事。

### Day 27 — Resume / GitHub Final

- 定稿简历 bullets。
- 精简 README 和最终结果。

### Day 28 — Full Mock

- 完整模拟 QD 项目面试。
- 整理最终项目题库。
