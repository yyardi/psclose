# Professional services close -- exercise brief

Welcome! Our client runs a professional-services business, and we'd love
your help closing out their July 2026 books. We've included two SQLite
databases to work with: `synthetic_ps_recon_scaled.sqlite`, which contains
their operational and accounting data through the June 2026 close (which is
final), and `july_increment.sqlite`, this month's new operational data
(timesheets, sales orders, contract items, and project events). July's
operational activity has arrived, but July hasn't been closed yet. Both
schemas are self-describing, so feel free to explore them directly using
`sqlite_master` and `PRAGMA table_info` rather than asking us for a data
dictionary.

Here's what we're looking for: design a system that can take this data and
produce the July 2026 revenue schedule. We need one row per contract item,
in the same shape as the historical `revenue_schedule` table (period
`2026-07`, with planned and recognized amounts using cumulative semantics
that match the history). Along with that, we'd appreciate a per-project
rollup and an exception report that walks through every figure that isn't a
straight-line continuation of June. Build it so it keeps working in August
without you needing to rebuild it by hand.

`GLOSSARY.md` defines the general PS/accounting vocabulary you'll run into
in the schema and in your conversations with the controller -- it's
terminology only, not a data dictionary for this particular dataset.

Our finance team is playing the role of your client's controller, and
they're here for questions throughout. Please use them to clarify anything
that comes up.

Good luck -- we're looking forward to seeing what you build.
