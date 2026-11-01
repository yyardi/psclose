from psclose.narrate import load_inputs, template_memo, write_memo
from psclose.report import write_csvs
from psclose.rollup import build_rollup
from psclose.schedule import close_through


def test_template_memo_reads_the_close_outputs(july_ledger, policy, tmp_path):
    (result,) = close_through(july_ledger, "2026-07", policy)
    out_dir = tmp_path / "2026-07"
    write_csvs(result, build_rollup(july_ledger, result), out_dir)

    data = load_inputs(out_dir)
    assert data["period"] == "2026-07"
    assert data["items"] == 48
    assert data["totals_by_currency"]["USD"]["recognized_period"] == 242669.97

    memo = template_memo(data)
    assert memo.startswith("# July 2026 close memo")
    assert "PX-12 / CI-PX-12A" in memo
    assert "Open questions" in memo

    path = write_memo(out_dir, use_claude=False)
    assert path.name == "close_memo.md"
    assert "templated" in path.read_text()
