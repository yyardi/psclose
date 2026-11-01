"""Link operational rows to projects when the source system did not.

OpenAir timesheets arrive with a free-text project name and, when the OpenAir link exists, a
project id. When the link is missing we match the reported name against every name the
project is known by: its display name and the aliases kept in project.aliases_json. The
result is written to timesheet_resolution so later steps and the exception report can see
how each row was linked. Timesheet ids are never used as a hint here; a row whose id looks
like a project but whose name matches nothing stays unresolved and is reported.
"""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize(name: str) -> str:
    return " ".join(_NON_ALNUM.sub(" ", name.lower()).split())


def _aliases(aliases_json: str) -> dict:
    try:
        data = json.loads(aliases_json or "{}")
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def alias_index(conn: sqlite3.Connection) -> dict[str, tuple[str | None, str]]:
    """Normalized name -> (project_id, source). A name claimed by two projects maps to None."""
    index: dict[str, tuple[str | None, str]] = {}

    def claim(name: str, project_id: str, source: str) -> None:
        key = normalize(name)
        if not key:
            return
        existing = index.get(key)
        if existing and existing[0] not in (None, project_id):
            index[key] = (None, "ambiguous")
        elif not existing:
            index[key] = (project_id, source)

    for row in conn.execute("SELECT id, display_name, aliases_json FROM project"):
        claim(row["display_name"], row["id"], "display_name")
        aliases = _aliases(row["aliases_json"])
        for name in aliases.get("openair_names", []) or []:
            claim(str(name), row["id"], "openair_name")
        if aliases.get("so_alias"):
            claim(str(aliases["so_alias"]), row["id"], "so_alias")
    return index


def resolve_timesheets(conn: sqlite3.Connection) -> dict[str, int]:
    """(Re)build timesheet_resolution for every timesheet row. Returns counts by method."""
    index = alias_index(conn)
    counts: dict[str, int] = {}
    rows = []
    for ts in conn.execute("SELECT id, project_id, project_name_as_reported FROM timesheet_entry"):
        if ts["project_id"]:
            method, project_id, matched = "source", ts["project_id"], None
        else:
            hit = index.get(normalize(ts["project_name_as_reported"]))
            if hit and hit[0]:
                method, project_id, matched = hit[1], hit[0], ts["project_name_as_reported"]
            elif hit:
                method, project_id, matched = "ambiguous", None, ts["project_name_as_reported"]
            else:
                method, project_id, matched = "unresolved", None, None
        counts[method] = counts.get(method, 0) + 1
        rows.append((ts["id"], project_id, method, matched))
    conn.execute("DELETE FROM timesheet_resolution")
    conn.executemany("INSERT INTO timesheet_resolution VALUES (?, ?, ?, ?)", rows)
    conn.commit()
    return counts


@dataclass(frozen=True)
class SalesOrderLink:
    sales_order_id: str
    tran_id: str
    customer_id: str
    total_native: float
    currency: str
    project_id: str | None
    method: str
    has_items: bool


def sales_order_links(conn: sqlite3.Connection) -> list[SalesOrderLink]:
    """Sales orders with no project: try the netsuite_so_hint alias, report the rest."""
    hints: dict[str, str] = {}
    for row in conn.execute("SELECT id, aliases_json FROM project"):
        hint = _aliases(row["aliases_json"]).get("netsuite_so_hint")
        if hint:
            hints[str(hint)] = row["id"]
    out = []
    sql = """
        SELECT so.id, so.tran_id, so.customer_id, so.total_native, so.currency,
               EXISTS (SELECT 1 FROM contract_item ci WHERE ci.sales_order_id = so.id) AS has_items
        FROM sales_order so WHERE so.project_id IS NULL ORDER BY so.id
    """
    for row in conn.execute(sql):
        project_id = hints.get(row["tran_id"])
        out.append(
            SalesOrderLink(
                sales_order_id=row["id"],
                tran_id=row["tran_id"],
                customer_id=row["customer_id"],
                total_native=row["total_native"],
                currency=row["currency"],
                project_id=project_id,
                method="netsuite_so_hint" if project_id else "unresolved",
                has_items=bool(row["has_items"]),
            )
        )
    return out
