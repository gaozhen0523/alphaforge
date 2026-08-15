# Frozen Universe Snapshots

手动生成 Week 1 CSI300 snapshot：

```bash
uv run python scripts/snapshot_csi300_universe.py
```

提交生成的 `csi300_<snapshot_date>.csv`，并将该文件的准确路径传给 bulk downloader。Downstream research 和 backtest 不得在 runtime 解析 current constituents。

Snapshot 包含其记录的 source date 当日的 current membership，不是 point-in-time historical universe。因此，用它覆盖更早的价格历史会引入 survivorship bias（幸存者偏差）和 membership bias。
