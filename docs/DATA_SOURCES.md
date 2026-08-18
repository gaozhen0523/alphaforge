# Data Source and Quality Semantics

AlphaForge 需要约 100–300 只 A 股、约五年的日频 OHLCV。MVP 的数据获取层应可替换；任何 source-specific output（数据源特定输出）都必须先转换为 canonical schema，再提供给下游模块。

| Source | Access | Daily OHLCV and adjustment | MVP trade-off |
| --- | --- | --- | --- |
| [AkShare / Sina](https://github.com/akfamily/akshare/blob/main/docs/data/stock/stock.md) | 无账号或 token | `stock_zh_a_daily` 支持日频历史和 qfq / hfq 价格 | 当前 MVP primary source，且已是项目依赖。频繁请求可能受到 rate limit 或临时 IP 封禁。 |
| [Tushare Pro](https://tushare.pro/document/1?doc_id=27) | 需要账号和 token；部分 API 采用积分权限 | 提供结构化日频历史；[adjustment factor](https://tushare.pro/document/2?doc_id=28) 以及 `pro_bar` 的 qfq / hfq | 数据 API 和标识符更明确，但 token、权限和复权流程会增加不必要的 Day 1 配置。 |
| [BaoStock](https://baostock.com/) | 数据平台无需注册 | 提供历史日线和有文档说明的 adjustment factor | 可作为简单、免费的 fallback，但会引入额外依赖，相比当前数据源没有明显的 MVP 优势。 |

## Recommendation

当前 Day 1 MVP 使用 AkShare 的 Sina-backed `stock_zh_a_daily`。该接口不需要 credentials、支持 adjusted prices，并已在当前网络环境中人工验证。此前 EastMoney-backed `stock_zh_a_hist` 因上游 endpoint 反复关闭连接而不可用。Sina 同样是上游公共接口；AkShare 提示频繁请求可能触发临时 IP blocking，因此批量获取必须采用保守的 request pattern。

## MVP Data Semantics

- AlphaForge MVP 的 canonical OHLC price 固定为后复权（`hfq`）。adapter 内部执行该 contract，不向调用方开放 adjustment 选项。
- Canonical `volume` 单位为 shares。Sina `stock_zh_a_daily` 已返回 shares，因此 adapter 不做单位换算。
- Week 1 使用 frozen static universe，刻意保持比 point-in-time historical constituent universe 更简单。
- Static universe 会引入 survivorship bias（幸存者偏差）：由于排除了已退市或已离开该 universe 的证券，历史表现可能被高估。research 和 backtest results 必须披露这一 limitation。

这些约定属于 ingestion provenance，不会成为七列 canonical OHLCV frame 的额外 columns。缺失的 trading-date rows（包括停牌日）保持缺失，不做 forward fill。

## Frozen CSI300 Universe

Week 1 使用一份已提交的 CSI300 snapshot，而不是在 runtime 解析 constituents。`scripts/snapshot_csi300_universe.py` 只在创建 snapshot 时调用 AkShare 的 `index_stock_cons_csindex(symbol="000300")`。脚本要求恰好 300 个 unique constituents，将代码转换为 AlphaForge symbols，按 symbol 排序，并写入：

```text
configs/universe/csi300_<snapshot_date>.csv
```

CSV 包含 `snapshot_date`、`symbol` 和数据源提供的 `name`。日期取自 AkShare / CSIndex constituent file。生成后，该 CSV 是需要提交到 Git 的 static input；bulk acquisition 及所有 downstream research 都必须读取它，不得动态请求 current membership。

手动生成或明确刷新 snapshot：

```bash
uv run python scripts/snapshot_csi300_universe.py
```

这份 frozen current-membership snapshot **不是** point-in-time universe。将它用于完整历史价格会同时引入 survivorship bias 和 membership bias。PIT universe support 不属于 Week 1 MVP，因此 research 和 backtest results 必须披露这一 limitation。

## Rate-Controlled Bulk Acquisition

`scripts/download_market_data.py` 只读取 frozen CSV，并按顺序调用现有的 `fetch_akshare_daily_ohlcv` adapter。默认 request interval 为可配置的 2.0 秒；不使用 concurrency 或 retry framework。保守的低频 request pattern 用于降低 Sina 临时封禁 client 的风险。

每个失败 symbol 及其 error reason 都会写入 log；后续 symbols 继续执行；final summary 报告 requested、successful、failed 和 row counts。如果任何 symbol 失败，脚本会在 diagnostic result 中保留成功 rows，但不会写入 official output Parquet，并以非零状态退出。只有全部 requested symbols 成功时才发布 canonical downstream dataset。

Small-scale acquisition 示例：

```bash
uv run python scripts/download_market_data.py \
    --universe configs/universe/csi300_<snapshot_date>.csv \
    --start-date 20240101 \
    --end-date 20240131 \
    --limit 5
```

## Processed Dataset

MVP 将 consolidated dataset 写入 `data/processed/ohlcv_hfq.parquet`。持久化前，所有成功 frames 会被合并，并经过 canonical normalization 和 validation。rows 在 `(date, symbol)` 上唯一，并按 `date, symbol` 排序。写入后重新读取并执行 strict validation，包括检查 canonical dtypes。

该 Parquet file 是 canonical downstream dataset。其 OHLC values 是用于 research 的 `hfq` adjusted prices，不是当时实际成交的 historical nominal prices。Canonical volume 单位保持为 shares。

## Canonical Market Data Loading

`MarketDataLoader` 读取单个 canonical Parquet dataset，并可按 inclusive `start_date`、inclusive `end_date` 和 canonical `symbols` 过滤。返回结果包含七个 canonical columns，按 `date, symbol` 排序，并对 source dataset 和结果 frame 都执行 validation。

Requested symbols 必须唯一，并使用完全一致的 AlphaForge canonical form。如果任何 requested symbol 不存在于完整 dataset，loader 会明确报错，不会静默返回 partial selection。合法 filter 的 date window 没有 observations 时，返回 validated canonical empty DataFrame。loader 不创建 calendar rows、不填充停牌日，也不修改 OHLCV values。

## Day 8 Data Quality Semantics

Production factor 和 return research 统一使用 `hfq` adjusted OHLC。复权价格用于避免 dividends、splits 等 corporate actions 造成机械价格 jump；它是 research price series，不应描述为当时市场真实 quoted execution price。

Canonical observed row 必须满足 `(date, symbol)` 唯一、OHLCV 无 NaN/inf、OHLC 严格为正、volume 非负，并满足：

```text
low <= open <= high
low <= close <= high
```

违反 contract 的 canonical data 明确失败，不自动 drop、修值或补 row。Data Layer 保持 unbalanced observed panel；所有 observed global dates × observed symbols 只用于 coverage diagnostics，不会生成 synthetic OHLCV observations。

Diagnostics 中，missing observation 是 expected panel 中不存在的 `(date, symbol)`。对单个 symbol，位于 first 和 last observed global date 之间的 gap 记为 internal missing，其余记为 boundary missing。这只是 gap location 的描述：missing 可能来自 suspension、IPO/history boundary、delisting、provider gap 或其他原因；当前不把 internal missing 自动分类为 suspension，也不把 boundary missing 自动分类为 IPO / delisting。

`duplicate_pairs` 统计出现超过一次的 unique `(date, symbol)` keys；`invalid_observations` 统计至少违反一项 numeric / OHLC rule 的 rows，duplicate 单独报告。`coverage_ratio = observed_unique_rows / expected_panel_rows`。

Downstream semantics 保持不变：

- factor rolling 和 research forward horizon 使用 future/past available observations，而不是补出的 exchange-calendar rows；
- Backtest valuation 对 close 做 past-only forward fill，missing observation 当天 return 为 `0`，下次真实 close 一次体现累计价格变化；
- valuation forward fill 只是 marking convention，不代表现实中可交易；
- Week 1 execution 仍理想化假设 marked close 可以成交，不模拟 suspension、limit up/down、liquidity 或 market impact constraints；
- frozen current-membership CSI300 仍存在 survivorship / membership bias，Day 8 不解决该 limitation。
