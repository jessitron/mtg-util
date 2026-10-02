# prepared-cards

Pick cards from a Scryfall search (default `o:prepared`) on a web page, and write the picks as an Archidekt import list.

## Usage

```
./run
```

Opens a tiny local server (Python 3, standard library only) at http://localhost:8765.

1. First run fetches the search from Scryfall and caches it in `scryfall-cache.json`. Delete that file, or visit `/api/refresh`, to refetch.
2. The page shows every card, grouped and sorted by mana value. Click a card to check it.
3. "Save selection" writes `selected.txt`, one `1 Card Name` per line. Saved picks reload when you reopen the page.
4. In Archidekt, use the deck's import feature and paste (or upload) `selected.txt`.

## Settings (environment variables)

- `QUERY`: Scryfall search. Default `o:prepared`.
- `PORT`: default `8765`.

## Tests

```
python3 -m unittest discover -s tests -t .
```

No network needed.

## Design

Three tiers; dependencies point downward only.

| Tier | Package | What lives there |
| ---- | ------- | ---------------- |
| I. Orchestration | `prepared_cards/orchestration` | `CardPicker` use cases; the HTTP server and page that drive them. |
| II. Domain | `prepared_cards/domain` | `Card`, `CardPool` (grouped by mana value), `Selection`, and the ports `CardCatalog` and `SelectionStore`. No I/O. |
| III. Interface | `prepared_cards/adapters` | `ScryfallCatalog` (anti-corruption layer for Scryfall JSON), `CachedCatalog` (JSON file decorator), `ArchidektImportFile` (the import-format file). |

`main.py` is the composition root: it picks the adapters and wires them to `CardPicker`.

Language boundaries: Scryfall says `cmc` and `card_faces`; Archidekt says `1 Name` lines; the domain says mana value and selection. Each adapter translates at its edge.

## Notes

- `prepared` cards have layout `prepare` and two faces. Their name is `Front // Back`. We write that full name to the import file. Untested in Archidekt; if it fails to match, switch to the front-face name only.
- Images come from the front face.
- API details: see [../reference/](../reference/README.md).
