# mtgjson

A local, read-only copy of [MTGJSON](https://mtgjson.com)'s full card database as SQLite, plus small scripts so any agent or script in this repo can query it, including from a worktree.

What is in the database, and when we downloaded it: [reference/mtgjson.md](../reference/mtgjson.md).

## Quick start for agents

The scripts use absolute paths into the main checkout, so run them by full path from anywhere:

```
BIN=/Users/jessitron/code/jessitron/mtg-util/mtgjson/bin

$BIN/mtgjson-card "Lightning Bolt"                 # one record per face, key fields
$BIN/mtgjson-schema                                # list tables
$BIN/mtgjson-schema cards                          # columns of one table
$BIN/mtgjson-query "select name, manaValue from cards where name like 'Jace%' group by name"
$BIN/mtgjson-query -json "select ..."              # also -csv, -line, -list
```

| Script | What it does |
| ------ | ------------ |
| `bin/mtgjson-query [-mode] "SQL"` | Run any SQL, read-only. Default output is a headed column table. |
| `bin/mtgjson-card [-mode] "Name"` | Look up a card by exact name (or one face's name). Default output is `-line`. |
| `bin/mtgjson-schema [table]` | List tables, or show a table's columns and types. |
| `run [--force]` | Download or refresh the database. |

Why absolute paths: the database file is git-ignored, so it exists only in the main checkout. A worktree has no `mtgjson/data/`, but these scripts still find the main copy.

If the database is missing, each script says so and prints the `run` command.

## Refreshing the data

```
/Users/jessitron/code/jessitron/mtg-util/mtgjson/run           # download if missing or different in size from upstream
/Users/jessitron/code/jessitron/mtg-util/mtgjson/run --force   # re-download regardless
```

The file lands at `mtgjson/data/AllPrintings.sqlite` (~690 MB, git-ignored, mode 444). The download goes to a `.part` file first and replaces the old copy only after a sanity query succeeds. MTGJSON rebuilds daily. After a refresh, update the "Downloaded" line in [reference/mtgjson.md](../reference/mtgjson.md). Requires `curl` and `sqlite3`.

## Using it from Python

Open it read-only so nothing can modify it:

```python
import sqlite3

DB = "/Users/jessitron/code/jessitron/mtg-util/mtgjson/data/AllPrintings.sqlite"
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
rows = con.execute("select name, manaValue from cards where name = ?", ("Lightning Bolt",)).fetchall()
```

## Gotchas

- `cards` has one row per printing, so `group by name` (or filter on `uuid`) when you want one row per card. `mtgjson-card` already does this.
- Multi-face cards have one row per face (`side` is `a` or `b`). `name` is the full `A // B` name; `faceName` is one face.
- Names keep their diacritics ("Lim-Dûl's Vault"), so an exact lookup for "Lim-Dul's Vault" finds nothing. Use `like`, or match the `asciiName` column.
- List-valued columns (`colors`, `keywords`, `subtypes`, `printings`) are comma-separated text.
- SQL with `$` or backticks inside double quotes gets expanded by the shell; use single quotes around the SQL and double the quotes inside SQL strings.
