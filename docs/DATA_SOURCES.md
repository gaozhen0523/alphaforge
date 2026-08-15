<!-- docs/DATA_SOURCES.md -->
# Day 1 Data-Source Review

AlphaForge needs daily A-share OHLCV for roughly 100–300 stocks over five years.
The MVP should keep acquisition replaceable and convert source-specific output to
the canonical contract before any downstream use.

| Source | Access | Daily OHLCV and adjustment | MVP trade-off |
| --- | --- | --- | --- |
| [AkShare / Sina](https://github.com/akfamily/akshare/blob/main/docs/data/stock/stock.md) | No account or token | `stock_zh_a_daily` supports daily history and qfq/hfq prices | Current MVP primary source and already a project dependency. Frequent requests may be rate-limited or temporarily IP-blocked. |
| [Tushare Pro](https://tushare.pro/document/1?doc_id=27) | Account and token; some APIs use points-based permissions | Structured daily history; [adjustment factors](https://tushare.pro/document/2?doc_id=28) and qfq/hfq via `pro_bar` | More explicit data API and identifiers, but token, permissions, and adjustment workflow add avoidable Day 1 setup. |
| [BaoStock](https://baostock.com/) | No registration is required for the data platform | Historical daily bars and documented adjustment factors | Simple free fallback, but would add another dependency and offers no clear MVP advantage over the dependency already selected. |

## Recommendation

Use AkShare's Sina-backed `stock_zh_a_daily` for the current Day 1 MVP. It needs
no credentials, supports adjusted prices, and has been manually verified in the
current network environment. The earlier EastMoney-backed `stock_zh_a_hist`
repeatedly failed because its upstream endpoint closed connections in this
environment. Sina is also an upstream public interface: AkShare warns that
frequent requests may trigger temporary IP blocking, so later acquisition must
use a deliberately conservative request pattern.

## MVP Data Semantics

- AlphaForge MVP canonical OHLC prices are fixed to back-adjusted (`hfq`) prices.
  The adapter applies this contract internally rather than exposing adjustment
  as a caller option.
- Canonical `volume` is measured in shares. Sina's `stock_zh_a_daily` already
  reports shares, so the adapter performs no unit scaling.
- Week 1 uses a frozen static universe. It is intentionally simpler than a
  point-in-time historical constituent universe.
- The static universe creates survivorship bias: results may overstate historical
  performance by excluding securities that delisted or left the chosen universe.
  This limitation must be disclosed in research and backtest results.

These choices are ingestion provenance, not additional columns in the seven-column
canonical OHLCV frame. Missing trading-date rows, including suspended days, remain
missing rather than being forward-filled.

## Frozen CSI 300 Universe

Week 1 uses one committed CSI 300 snapshot rather than resolving membership at
runtime. `scripts/snapshot_csi300_universe.py` calls AkShare's
`index_stock_cons_csindex(symbol="000300")` only to create the snapshot. It
requires exactly 300 unique constituents, converts codes to AlphaForge symbols,
sorts them by symbol, and writes:

```text
configs/universe/csi300_<snapshot_date>.csv
```

The CSV contains `snapshot_date`, `symbol`, and the source-provided `name`. The
date is AkShare/CSIndex's constituent-file date. After generation, the CSV is a
static input that should be committed to Git; bulk acquisition and all downstream
research must read it and must not dynamically request current membership.

Generate or deliberately refresh a snapshot manually with:

```bash
uv run python scripts/snapshot_csi300_universe.py
```

This frozen current-membership snapshot is **not** a point-in-time historical
membership dataset. Applying it across the full price history creates both
survivorship and membership bias. PIT universe support is outside the Week 1 MVP,
so research and backtest results must disclose this limitation.

## Rate-Controlled Bulk Acquisition

`scripts/download_market_data.py` reads only the frozen CSV and invokes the
existing `fetch_akshare_daily_ohlcv` adapter sequentially. Requests are separated
by a configurable delay of 2.0 seconds by default; there is no concurrency or
retry framework. This deliberately low-frequency request pattern reduces the risk
of Sina temporarily blocking the client.

Each failed symbol and its error reason are logged, later symbols still run, and
the final summary reports requested, successful, failed, and row counts. If any
symbol fails, the script retains successful rows in its diagnostic result but does
not write the official output Parquet and exits non-zero. The canonical downstream
dataset is published only when every requested symbol succeeds.

Example smoke acquisition:

```bash
uv run python scripts/download_market_data.py \
    --universe configs/universe/csi300_<snapshot_date>.csv \
    --start-date 20240101 \
    --end-date 20240131 \
    --limit 5
```

## Processed Dataset

The MVP writes one consolidated file at
`data/processed/ohlcv_hfq.parquet`. Before persistence, all successful frames are
concatenated and passed through canonical normalization and validation. Rows are
unique on `(date, symbol)` and sorted by `date, symbol`. The file is read back and
strictly revalidated, including canonical dtypes, after writing.

This Parquet file is the canonical downstream dataset. Its OHLC values are `hfq`
research-adjusted prices, not the historical nominal prices at which shares
actually traded. Canonical volume remains measured in shares.

## Canonical Market-Data Loading

`MarketDataLoader` reads one canonical Parquet dataset and optionally filters it
by inclusive `start_date`, inclusive `end_date`, and canonical `symbols`. It
returns the seven canonical columns sorted by `date, symbol` and validates both
the source dataset and the returned frame.

Requested symbols must be unique and use exact AlphaForge canonical form. If any
requested symbol is absent from the complete dataset, loading raises a clear
error rather than silently returning a partial symbol selection. A valid filter
whose date window contains no observations returns a validated canonical empty
DataFrame. The loader never creates calendar rows, fills suspensions, or changes
OHLCV values.
