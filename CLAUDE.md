# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this app is

Desktop app to manage table-tennis tournaments for the LJTT club. Multi-tournament storage with one or more **formats** — only `top12` is implemented today (12 players, 11 rounds: 5 pool rounds × 2 pools of 6, then 6 cross-pool rounds with round 11 reserved for same-rank pairings).

The repo started as "Top12" and was renamed to "Tournoi LJTT" in commit `763dd83`. Some internal paths still use `top12` (legacy DB fallback, the folder name on disk, the `top12` type code) — that's intentional and shouldn't be changed.

## Stack

- Python 3.10+, **PyQt6** for the GUI (no web layer, no async)
- **SQLite** via `sqlite3` (no ORM); migrations are inline in `database.py::_migrate_v1_if_needed`
- **PyInstaller** for the single-file Windows .exe
- No tests, no linter configured

## Build & run

```powershell
.\build.ps1                # silent rebuild — produces dist\TournoiLJTT.exe
.\build.ps1 -Verbose       # full PyInstaller log on stdout
python main.py             # run from source (uses ~/.tournoi-ljtt/ as data dir)
```

`build.ps1` creates `.venv`, installs `requirements.txt`, cleans `build/` + `dist/`, then runs PyInstaller via `tournoi_ljtt.spec`. PyInstaller writes INFO to stderr, so the script briefly flips `$ErrorActionPreference` to `Continue` during that call — don't undo that, it's why builds work.

If a build fails with "Access denied" on `dist\TournoiLJTT.exe`, the running app is locking the file — close it before retrying.

## Data location

- **Runtime DB**: `%USERPROFILE%\.tournoi-ljtt\tournoi-ljtt.db`
- **Legacy fallback**: if `~/.top12/top12.db` exists and the new DB doesn't, `main.py::_resolve_data_dir` copies it over once at startup. Don't remove this — production PCs may still be coming from the old layout.
- The `.exe` does **not** embed the DB. Rebuilding never touches user data.

## Architecture: where things live

```
main.py                    # entry: app icon, AppUserModelID, data-dir resolution, Database boot
src/
├── models.py              # dataclasses: Tournament, Player, Match, PlayerStanding
│                          # + TOURNAMENT_TYPES registry (the single source of truth for formats)
├── database.py            # SQLite layer + inline migration chain (v1 → v6)
├── tournament.py          # ALL match-generation and ranking logic — see "Algorithms" below
├── stats.py               # Statistics page awards (Marathonien, Showmen, etc.)
└── ui/
    ├── styles.py          # "Editorial Club" theme: palette + STYLESHEET + GlowBackground + load_fonts()
    ├── styles_editorial_v6.py  # previous V6 "Editorial / Hero" theme, kept for rollback
    ├── styles_legacy.py   # pre-V6 theme, kept for rollback
    ├── widgets.py         # small reusable helpers — currently just make_page_header()
    ├── main_window.py     # QMainWindow, sidebar (TOURNOI / NAVIGATION / ACTIONS), QStackedWidget routing
    ├── home_page.py       # Tournament list + new/open/edit/delete
    ├── tournament_dialog.py  # Create/edit dialog with the "Type de tournoi" combo
    ├── player_page.py     # 12-player entry sorted by points
    ├── rounds_page.py     # Used twice: session=1 (pool) and session=2 (cross). Tabs per round + standings below.
    ├── general_ranking_page.py
    ├── statistics_page.py
    ├── set_dialog.py      # Per-set score entry popup
    ├── match_card.py
    ├── print_export.py    # A4 print/PDF — 2×10 grid of strip-shaped match slips
    └── dialogs.py         # confirm() helper with FR Oui/Non buttons
```

The `assets/` folder ships logos, the .ico, and two SVG icons (`arrow-down.svg`, `calendar.svg`) that QSS references via `styles.py::_asset_url()`. The spec bundles the whole `src/assets/` dir — new assets there are picked up automatically.

## Algorithms (the part that matters)

All in `tournament.py`. Read this section before editing scheduling or rankings.

- **Pool seeding** is **fixed, not random**: ranks 1‑4‑5‑8‑9‑12 → Pool A; 2‑3‑6‑7‑10‑11 → Pool B. See `split_into_pools`.
- **Pool rounds** use a hard-coded Berger schedule for 6 players (`BERGER_6`).
- **Cross rounds**: 6×6 latin square with `offset = 5 - round_index` so that Round 11 is the same-rank final (A1‑B1, A2‑B2, …). `build_cross_rounds` reverses the order in round 11 specifically so the top pairings play last.
- **Table & referee assignment** (`assign_tables_and_referees`): greedy initial pass + `_two_opt_pass` + `_three_opt_pass` local search. Targets **4‑4‑3** per player across the 3 tables and 5‑6 refereeing slots per player. The constraint is per-session (each batch of 3 simultaneous matches must use tables {1,2,3} exactly).
- **Backfill** (`main_window.py::_backfill_assignments_if_needed`): if a loaded tournament violates the session constraint, **all** matches are reset and re-assigned — even played ones, because table/ref are algorithmic outputs, not user input.
- **Standings & tiebreaks** (`compute_standings` → `_rank_with_tiebreaks` → `_break_points_tie`):
  1. Match points DESC (win=1, loss=0)
  2. 2-way tie → head-to-head
  3. 3+ tie → set differential
  4. 3+ still tied → **point differential on matches between the tied players only** (`_break_by_inner_point_diff`, uses `Match.set_scores`)
  5. 2 left at any later step → head-to-head; 3+ left at the very end → alphabetical fallback
- Standings are computed identically for pools (`pool="A"/"B"`, `max_round=5`) and overall — pages don't need to know about the rules.

## UI theme notes

- The page background is a custom `GlowBackground` widget (radial bordeaux gradient on near-black, default corner `bottom-left`, intensity 80) in `styles.py`. Most widgets are transparent in QSS so the glow shows through; cards/inputs set their own surface.
- Four variable fonts are embedded under `src/assets/fonts/` and registered at startup via `styles.load_fonts(app)` called from `main.py` after `QApplication` creation: Inter (UI), Playfair Display (h1/h2 — italic accent word in titles), Source Serif 4 (body), JetBrains Mono (scores & numbers). The QSS font-family stacks fall back to Segoe UI / Georgia / Consolas if the TTFs fail to load.
- Page headers go through `widgets.make_page_header(title, eyebrow=..., accent_word=..., lead=...)`. The helper renders an eyebrow (uppercase bordeaux), a serif h1 with one word optionally italicised in bordeaux, an optional lead paragraph, and a 1px red hairline. `rounds_page.py` rebuilds the header dynamically (session 1 / session 2 / pool variants) via `_set_header()`.
- **Tables with rounded corners** use a `_RoundedWrap` QFrame with a `QRegion` mask + a transparent viewport. QSS `border-radius` does **not** clip child widgets in Qt — the mask is what actually rounds the bottom corners. See `rounds_page.py::_wrap_table` and `general_ranking_page.py`.
- **Deterministic row heights**: row heights are computed from `QFontMetrics` (not `resizeRowsToContents`), so pool A and pool B align even when names have different lengths.
- **Print preview**: `print_export.py` temporarily clears the app stylesheet AND forces a light `QPalette` on `QPrintPreviewDialog` because Qt's print dialog inherits the parent's dark palette and the toolbar buttons go invisible otherwise.

## Adding a new tournament format

1. Append `("code", "Label")` to `TOURNAMENT_TYPES` in `src/models.py` — that's it for the UI (the combo populates from this list and `tournament_type_label()` resolves the label everywhere).
2. Add the actual scheduling / standings logic. Today everything in `tournament.py` is `top12`-specific (BERGER_6, the 6×6 cross, table-equity targets). New formats will need either parallel functions or a strategy dispatch keyed on `Tournament.tournament_type`.
3. Pages currently assume 12 players and 11 rounds (Session 1 / Session 2 labels, the "Générer la phase finale" flow, the `split_into_pools` signature). Generalising means making `RoundsPage` and `main_window._open_tournament` branch on the format.

## Migrations

`Database._migrate_v1_if_needed` runs every startup and is **idempotent**. To add a new column: append a fresh `if "col" not in xxxx_cols:` block at the end with the `ALTER TABLE`. Never modify existing migration blocks — old DBs may still need to walk through them.

## Git / repo conventions

- Remote: `https://github.com/alexisprat01-pixel/tournoi-ljtt.git` (the old `top12` repo was renamed; GitHub keeps the redirect)
- Commit messages are in French, imperative form, one-line summary + optional body
- Tag `pre-editorial-theme` marks the last commit before the V6 theme — useful as a rollback reference
- Tag `pre-editorial-club-theme` marks the last commit before the "Editorial Club" theme (2026-05-26). Rollback: `git checkout pre-editorial-club-theme`. Page files were refactored to use `widgets.make_page_header`, so a simple import switch from `styles` to `styles_editorial_v6` won't fully revert the look — use the tag.

## Things to avoid

- Don't use PowerShell `-replace` on source files — it mangles UTF-8 (em-dashes, accented chars become mojibake). Use the `Edit` tool instead.
- Don't move table/ref assignment logic into UI code. It's intentionally in `tournament.py` and re-run on load via the backfill.
- Don't widen the call signature of `Database.update_tournament` without going through both call sites (`home_page.py` and `main_window.py`) — they pass a 4-tuple from `TournamentDialog.get_values()`.
