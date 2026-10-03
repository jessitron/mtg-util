# prepared-cards

Pick cards from a Scryfall search (default `o:prepared`) on a web page, and copy the picks as an Archidekt import list.

## Usage

```
source ../.be   # ANTHROPIC_API_KEY
./run
```

Opens a tiny local server (Python 3; `uv` installs the `anthropic` SDK, see `pyproject.toml`) at http://localhost:8765. If an earlier copy is still listening on the port, `./run` stops it first.

1. First run fetches the search from Scryfall and caches it in `scryfall-cache.json`. Delete that file, or visit `/api/refresh`, to refetch.
2. The page shows every card in one list, most powerful first, each with its power score (0 weak to 2 powerful) and a bar. Scores come from a `PowerScore` when the page loads: `LlmPowerScore` asks Claude to rate each card's spell (the back face, judged alone at its own cost, not the creature). `power-scores-<model>.json` remembers them, one file per model so scores from different scorers never mix (delete it to rescore). The first load makes one API call per card (75 for `o:prepared`) and the page waits for them; after that it is instant. The header says who ranked them and what it took, such as "Ranked by claude-haiku-4-5 in 118.3 seconds for $0.063" (Jev: 13.0 seconds for $0.0015, measured 2026-10-03 on the 75 `o:prepared` cards). The time and cost are the sum over the cards on the page, kept in the score file beside each score, so they survive restarts; the cost is an estimate from tokens times cached prices (`adapters/pricing.py`) and reads "an unknown cost" for a model with no price listed or a score file from before this was recorded. The prompt and rubric come from the [spell-power-eval](../spell-power-eval/README.md) PoC, copied here, with no dependency on it. Tick a card's checkbox to pick it. Clicking the card itself opens its Gatherer search in a new window.
3. "Copy selection to clipboard" puts one `1 Card Name` per line in the clipboard (it works on `http://localhost`, which browsers treat as a secure context). It also writes `selected.txt`, so picks reload when you reopen the page.
4. In Archidekt, use the deck's import feature and paste.

## Settings (environment variables)

- `QUERY`: Scryfall search. Default `o:prepared`.
- `PORT`: default `8765`.
- `POWER_MODEL`: the model that scores. Default `claude-haiku-4-5` (about as close to Jess's labels as Sonnet in the PoC, and the fastest). `jev-latest` uses TypeSafe's Jev (its `score` question on the same rubric) instead; any other value goes to Claude. The cache file is named for it (`power-scores-jev-latest.json`).
- `TYPESAFE_API_KEY`: for Jev, from `../.be`.
- `MTGJSON_DB`: path to `AllPrintings.sqlite`. Default is the main checkout's copy.
- `ANTHROPIC_API_KEY`: from `../.be`, or an `ant auth login` profile.

## Tests

```
uv run python -m unittest discover -s tests -t .
```

No network needed; the LLM adapter is tested with a fake client.

## Design

Three tiers; dependencies point downward only.

| Tier | Package | What lives there |
| ---- | ------- | ---------------- |
| I. Orchestration | `prepared_cards/orchestration` | `CardPicker` use cases; the HTTP server and page that drive them. |
| II. Domain | `prepared_cards/domain` | `Card`, `CardPool` (`ranked` orders it by a `PowerScore`, the only ordering), `ScoredCard`, `Selection`, `CardRules` (every face with its own cost and text; `spell` is the last face), and the ports `PowerScore`, `Scorer` (works out a score the slow way and says what it cost), `EffortLedger` (what scores took, as a `RankingEffort`), `CardCatalog`, `RulesText`, and `SelectionStore`. No I/O. |
| III. Interface | `prepared_cards/adapters` | `ScryfallCatalog` (anti-corruption layer for Scryfall JSON), `CachedCatalog` (JSON file decorator), `LlmPowerScore` (the real scorer: asks Claude about `rules.spell`, which it gets from a `RulesText`), `JevPowerScore` (the same question put to TypeSafe's Jev over HTTP; both LLM scorers share `spell_rubric`: the question, the three levels, and the text of the spell), `RandomPowerScore` (a fake scorer for offline work; `main.py` no longer uses it), `CachedPowerScore` (turns a `Scorer` into the `PowerScore` the app uses: a JSON file of card name to score, seconds, and cost, written after each new score; it is also the `EffortLedger` behind the header), `pricing` (tokens to dollars), `MtgjsonRulesText` (the `RulesText` adapter: finds a card's faces in the local MTGJSON database by Scryfall id), `ArchidektImportFile` (the import-format file). |

`main.py` is the composition root: it picks the adapters and wires them to `CardPicker`. `LlmPowerScore` and `JevPowerScore` take the `RulesText` and send only the spell face. `POWER_MODEL` picks between them.

`Card.scryfall_id` is how `MtgjsonRulesText` finds a card; one id covers every face of a printing. A `scryfall-cache.json` from before that field existed is refetched on the next run. The database is `../mtgjson/data/AllPrintings.sqlite` in the main checkout, opened read-only. All 75 `o:prepared` cards are in it. See [../reference/mtgjson.md](../reference/mtgjson.md).

Language boundaries: Scryfall says `cmc` and `card_faces`; Archidekt says `1 Name` lines; the domain says mana value and selection. Each adapter translates at its edge.

## Notes

- `prepared` cards have layout `prepare` and two faces. Their name is `Front // Back`. We write that full name to the import file. Untested in Archidekt; if it fails to match, switch to the front-face name only.
- Images come from the front face.
- The Copy button gives the clipboard a promise (`ClipboardItem` with a `Blob` promise), so the server formats the text and the click keeps its permission in Safari too. It needs a secure context (https or localhost); otherwise it shows an alert.
- Card links go to Gatherer's name search, on the front-face name. See [../reference/gatherer.md](../reference/gatherer.md).
- API details: see [../reference/](../reference/README.md).
