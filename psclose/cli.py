"""Command line: close a period, replay history, or draft the controller memo."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .backtest import format_report, replay
from .config import Config
from .exceptions import ACTION, INFO, REVIEW
from .ledger import assemble, last_closed_period
from .periods import next_period, period_range
from .report import write_csvs, write_report
from .rollup import build_rollup, write_rollup
from .schedule import close_through


def _config(args) -> Config:
    cfg = Config.load(args.config)
    if getattr(args, "base", None):
        cfg.inputs.base = Path(args.base)
    if getattr(args, "increment", None):
        cfg.inputs.increments = [Path(p) for p in args.increment]
    if getattr(args, "out", None):
        cfg.inputs.out_dir = Path(args.out)
    return cfg


def run_close(args) -> int:
    cfg = _config(args)
    target_dir = cfg.inputs.out_dir / args.period
    target_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = target_dir / "ledger.sqlite"
    conn = assemble(cfg.inputs.base, cfg.inputs.increments, ledger_path)
    try:
        results = close_through(conn, args.period, cfg.policy)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for result in results:
        out_dir = cfg.inputs.out_dir / result.period
        rollups = build_rollup(conn, result)
        write_rollup(conn, rollups)
        files = write_csvs(result, rollups, out_dir)
        files.append(write_report(conn, result, rollups, out_dir))
        counts = {s: sum(1 for e in result.exceptions if e.severity == s) for s in (ACTION, REVIEW, INFO)}
        totals: dict[str, float] = {}
        for c in result.items:
            totals[c.ctx.currency] = totals.get(c.ctx.currency, 0.0) + float(c.delta)
        print(f"{result.period}: {len(result.items)} schedule rows, "
              + ", ".join(f"{amt:,.2f} {cur}" for cur, amt in sorted(totals.items())) + " recognized in period; "
              f"{counts[ACTION]} to answer, {counts[REVIEW]} to review, {counts[INFO]} noted.")
        for f in files:
            print(f"  wrote {f.relative_to(cfg.root) if f.is_relative_to(cfg.root) else f}")
    print(f"  ledger {ledger_path.relative_to(cfg.root) if ledger_path.is_relative_to(cfg.root) else ledger_path}"
          f" (closed through {last_closed_period(conn)})")
    if getattr(args, "memo", False):
        from .narrate import write_memo

        for result in results:
            path = write_memo(cfg.inputs.out_dir / result.period, model=args.model)
            print(f"  wrote {path.relative_to(cfg.root) if path.is_relative_to(cfg.root) else path}")
    conn.close()
    return 0


def run_backtest(args) -> int:
    cfg = _config(args)
    scratch = cfg.inputs.out_dir / "backtest"
    scratch.mkdir(parents=True, exist_ok=True)
    conn = assemble(cfg.inputs.base, [], scratch / "ledger.sqlite")
    first_row = conn.execute("SELECT MIN(period) FROM revenue_schedule").fetchone()[0]
    first = args.first or next_period(first_row)
    last = args.last or last_closed_period(conn)
    if not period_range(first, last):
        print(f"error: nothing to replay between {first} and {last}", file=sys.stderr)
        return 2
    result = replay(conn, first, last, cfg.policy)
    print(format_report(result))
    conn.close()
    return 0 if result.ok else 1


def run_narrate(args) -> int:
    from .narrate import write_memo

    cfg = _config(args)
    path = write_memo(cfg.inputs.out_dir / args.period, model=args.model)
    print(f"wrote {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="psclose", description="Close a professional-services revenue period.")
    parser.add_argument("--config", default="psclose.toml", help="policy and input paths (default: psclose.toml)")
    sub = parser.add_subparsers(dest="command", required=True)

    close = sub.add_parser("close", help="close every open period up to --period and write the outputs")
    close.add_argument("--period", required=True, help="target period, YYYY-MM")
    close.add_argument("--base", help="closed base database (overrides config)")
    close.add_argument("--increment", action="append", help="increment database, repeatable, in order (overrides config)")
    close.add_argument("--out", help="output directory (overrides config)")
    close.add_argument("--memo", action="store_true", help="also draft the controller memo with Claude")
    close.add_argument("--model", default=None, help="Claude model id for --memo")
    close.set_defaults(func=run_close)

    back = sub.add_parser("backtest", help="replay closed periods from their inputs and diff against the ledger")
    back.add_argument("--base", help="closed base database (overrides config)")
    back.add_argument("--out", help="output directory (overrides config)")
    back.add_argument("--from", dest="first", help="first period to replay (default: first period with a prior)")
    back.add_argument("--to", dest="last", help="last period to replay (default: last closed)")
    back.set_defaults(func=run_backtest)

    memo = sub.add_parser("narrate", help="draft the controller memo for an already closed period")
    memo.add_argument("--period", required=True)
    memo.add_argument("--out", help="output directory (overrides config)")
    memo.add_argument("--model", default=None)
    memo.set_defaults(func=run_narrate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
