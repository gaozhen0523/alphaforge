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
