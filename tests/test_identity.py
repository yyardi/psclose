from psclose.identity import alias_index, normalize, resolve_timesheets, sales_order_links


def test_normalize_collapses_separators():
    assert normalize("Larkspur Foods | Core Delivery") == normalize("Larkspur Foods Core Delivery")
    assert normalize("  Quarrystone Ins. Core RollOut ") == "quarrystone ins core rollout"


def test_alias_index_knows_every_name_a_project_goes_by(history_ledger):
    index = alias_index(history_ledger)
    assert index[normalize("Redwood Transit Core")] == ("PX-18", "openair_name")
    assert index[normalize("Aurelia Hlth Data Program")] == ("PX-01", "so_alias")
    assert index[normalize("Redwood Transit | Core Services")] == ("PX-18", "display_name")


def test_unlinked_timesheets_resolve_by_name_or_stay_unresolved(july_ledger):
    counts = resolve_timesheets(july_ledger)
    rows = july_ledger.execute(
        """
        SELECT t.project_name_as_reported AS name, r.project_id, r.method, COUNT(*) AS n
        FROM timesheet_resolution r JOIN timesheet_entry t ON t.id = r.timesheet_id
        WHERE r.method != 'source' GROUP BY 1, 2, 3 ORDER BY 1
        """
    ).fetchall()
    by_name = {r["name"]: (r["project_id"], r["method"], r["n"]) for r in rows}
    assert by_name["Redwood Transit Core"] == ("PX-18", "openair_name", 25)
    assert by_name["Legacy Support Work"] == (None, "unresolved", 1)
    assert counts["source"] == 4402 + 768 - 26


def test_sales_orders_without_a_project(july_ledger):
    links = {l.sales_order_id: l for l in sales_order_links(july_ledger)}
    assert set(links) == {"SO-PX-19", "SO-PX-20-ORPHAN"}
    assert links["SO-PX-19"].project_id == "PX-19"
    assert links["SO-PX-19"].method == "netsuite_so_hint"
    assert links["SO-PX-20-ORPHAN"].project_id is None
    assert links["SO-PX-20-ORPHAN"].has_items is False
