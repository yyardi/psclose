from psclose.backtest import KNOWN_DEVIATIONS, format_report, replay


def test_rules_reproduce_history(history_ledger, policy):
    result = replay(history_ledger, "2026-01", "2026-06", policy)
    print(format_report(result))
    assert result.rows_checked == 236 - 2  # the two 2025-12 opening rows are not replayed
    assert result.unexplained == [], format_report(result)
    assert {d.key for d in result.known} == set(KNOWN_DEVIATIONS)
