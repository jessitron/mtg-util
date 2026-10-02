# mtg-util

Utilities and scripts for Magic: The Gathering, built on Scryfall, Archidekt, and related APIs.

This repo also collects what we learn about those APIs. See [reference/](reference/).

## Scripts

Each script lives in its own directory with its own README.

| Script | What it does |
| ------ | ------------ |
| [prepared-cards](prepared-cards/README.md) | Browse Scryfall's `o:prepared` cards by mana value, check the ones you want, export an Archidekt import list. |
| [spell-power-eval](spell-power-eval/README.md) | Compare Claude and Jev against your hand labels of whether MTG spells are weak, balanced, or powerful for their cost. |
| [mtgjson](mtgjson/README.md) | Download MTGJSON's full card database as a read-only SQLite file that other scripts can query. |

## Reference

API notes and other resources live in [reference/](reference/README.md).

## Adding a script

1. Create a directory: `<script-name>/`
2. Put the script and a `README.md` in it (purpose, usage, examples, gotchas).
3. Add a row to the table above.
4. Record any new API knowledge in `reference/`.
