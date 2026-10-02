# mtgjson

A local, read-only copy of [MTGJSON](https://mtgjson.com)'s full card database as SQLite, for other scripts in this repo to query. Notes on the source: [reference/mtgjson.md](../reference/mtgjson.md).

## Usage

```
./mtgjson/run           # download if missing or different in size from upstream
./mtgjson/run --force   # re-download regardless
```

The file lands at `mtgjson/data/AllPrintings.sqlite` (~690 MB, git-ignored, mode 444). The download goes to a `.part` file first and replaces the old copy only after a sanity query succeeds. MTGJSON rebuilds daily; rerun whenever you want fresh data.

Requires `curl` and `sqlite3`.

## Using it from a script

Open it read-only so nothing can modify it:

```python
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "mtgjson" / "data" / "AllPrintings.sqlite"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
rows = con.execute("select name, manaValue from cards where name = ?", ("Lightning Bolt",)).fetchall()
```

From the shell: `sqlite3 -readonly mtgjson/data/AllPrintings.sqlite`.

## Gotchas

- Worktrees don't share `data/`. Run `./mtgjson/run` in the main checkout, or point a worktree script at the main checkout's file.
- `cards` has one row per printing, so group by `name` (or use `uuid`) when you want one row per card.
