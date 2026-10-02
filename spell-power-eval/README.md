# spell-power-eval

Which classifier agrees best with you about whether a Magic spell is **weak**, **balanced**, or **powerful** for its mana cost?

You score a few cards by hand. The script asks each classifier about the same cards, then compares their answers to yours. You and every classifier give a **score from 0 to 2** (0 weak, 1 balanced, 2 powerful, decimals allowed) and the label is that score rounded.

| Arm | What it is |
| --- | ---------- |
| `always-balanced` | The floor: says "balanced" for everything. |
| `haiku`, `sonnet`, `opus` | Claude (`claude-haiku-4-5`, `claude-sonnet-5-5`, `claude-opus-5-5`), through the Anthropic SDK with structured output (a one-sentence reason, then a 0-2 score). |
| `jev-choice` | TypeSafe's Jev, asked to choose weak / balanced / powerful. Its label is the choice. Its score is the expected level from its probabilities (0.03 weak, 0.65 balanced, 0.32 powerful gives 1.29). |
| `jev-score` | Jev, asked to rate on an ordered three-level rubric. Its score is the one Jev returns. |

Background on Jev and why we compare it: `references/jev.md` in the infra repo. API facts: [reference/jev.md](../reference/jev.md).

## Usage

0. Want to look at the cards first? `./run --page` writes `cards.html`: card images, rules text, and a 0-2 slider per card (with quick buttons for weak, balanced, and powerful). Open it with `open cards.html`. It remembers your scores in the browser, starts from any scores already in `labels.txt`, and builds the `labels.txt` lines for you to copy. It shows no model answers and no popularity rank, so nothing anchors you.
1. Edit `labels.txt`. Replace each `?` with a score from 0 to 2 (`1.4 | Serra Angel`), or with `weak`, `balanced`, or `powerful` (0, 1, and 2). **Label before you look at any model's answer**, so the models can't anchor you. Add or swap cards freely; a card marked `?` is skipped and costs nothing.
2. Look at what the models will be asked (free; calls Scryfall once, no model):
   ```
   ./run --dry-run
   ```
3. Run it:
   ```
   ./run                  # always-balanced haiku sonnet jev-choice jev-score
   ./run haiku opus       # just these arms
   ```

The report prints a card-by-card table (each cell is the score, its label, and ✓ if the label matched yours), then one summary line per arm: estimated cost, exact matches, **mean steps off** (a weak card called balanced is 1 step off, called powerful is 2), and **mean score error** (the average distance from your score). The score error is the finer measure: your 1.4 and a model's 1.6 are close even if the labels differ. "Exact" and "steps off" compare labels, which are your score and the model's score rounded. Each run also writes `results/<timestamp>.json` with every classifier's reason (Claude) or probabilities (Jev), the tokens each call used, an estimated cost per answer (`cost_usd`) and per arm, plus a confusion count per arm.

Each cell in the report ends with that answer's estimated cost, and the summary has an `est. cost` column. The estimate is the tokens the API reported times the cached prices in `spell_power_eval/domain/pricing.py` (update them there). Claude's output tokens include thinking. The page shows the total in the ranking and each answer's cost in the hover read-out and the table view; runs from before cost tracking show a dash.

The `edhrec rank` column comes from Scryfall (lower means more popular in Commander). It is context for your labels, not ground truth, and no classifier sees it.

## Judging a prepared spell on its own

A prepared card is a creature with a spell on its back face. To judge the spell apart from the creature (say, for a deck with other ways to prepare creatures), name the spell in `labels.txt`: `1.4 | Unwind History`. The script finds the card (a search, since Scryfall's name lookup skips back faces; see [reference/scryfall.md](../reference/scryfall.md)) and hands every classifier only the spell: its own name, cost, mana value, type, and rules text, plus a note to judge the spell alone and ignore the creature. Name the creature (`Diviner of Victory`) and you get the whole card, as before. The spell's own mana cost is what you and the classifiers weigh it against; the creature's cost never enters.

## Looking at the results

```
./run --serve              # http://localhost:8780
PORT=8800 ./run --serve    # another port
```

This starts a local page (bound to 127.0.0.1, stop with Ctrl-C) that lists the runs in `results/`, newest first. Pick one in the menu. If the port is taken, the script says so and suggests another. The page shows:

1. **A ranking**: each classifier by mean score error (lower is better), with exact matches, mean steps off, and failures.
2. **Where they disagree with you**: one column per classifier, one 0-2 axis per cell. The ink tick is your score, the dot is the classifier's, and the line between them is the miss. Hover, focus, or click a cell for the score, label, confidence, and the reason (Claude) or probabilities (Jev). A failed call shows as `error` with its text in the same place.
3. **Where they miss in the same direction**: each classifier's score minus yours, per card, on a blue (weaker than you) to red (more powerful than you) scale, plus the average per classifier to show a lean.

The **Table view** button swaps the charts for the same data in tables, with every reason and the confusion counts. The cards can be ordered by your score, by biggest miss, or as the run has them. The theme button switches between auto, light, and dark. Runs written before `image_url` and `mana_cost` joined the JSON still show, without thumbnails.

The page reads `spell_power_eval/orchestration/results_page.html` on each request, so a browser refresh picks up edits. Routes: `/` (the page), `/api/runs` (the list), `/api/runs/<file>` (one run).

## Credentials (environment variables)

- Claude: the Anthropic SDK finds credentials itself: `ANTHROPIC_API_KEY` (create one in the Anthropic Console), or an `ant auth login` profile.
- Jev: `TYPESAFE_API_KEY`, from https://console.typesafe.ai/keys. Without it the `jev-*` arms are skipped with a message.

## Cost

Ten cards is a few cents at most. Each card is about 150-300 input tokens and a short answer. Prices ($ per million input/output tokens, cached 2026-09-25): Haiku 4.5 $1/$5, Sonnet 5.5 $2/$10, Opus 5.5 $4/$20, Jev $0.042 input and free output. Sonnet and Opus think by default, so they use more output tokens than Haiku. Every run now reports its own estimate (see above); the prices live in `spell_power_eval/domain/pricing.py`, and `reference/anthropic-api.md` and `reference/jev.md` give their source.

## Status

- Unit tests pass. Every arm (haiku, sonnet, opus, jev-choice, jev-score) has run against the real APIs. Haiku 4.5 accepts the SDK's structured-output call (`messages.parse`).
- **First comparison, 2026-10-02: Jess's ten cards, ten scores.** Mean score error (lower is better): jev-choice 0.32, jev-score 0.35, sonnet 0.40, haiku 0.41, always-balanced 0.55. Exact label matches: jev-choice 7/10, haiku 6, jev-score 6, sonnet 5, always-balanced 3.
- **Read that run as a hint, not a result.** Ten cards means one card moves a score by 0.05 or more, and the gaps between the four real arms are smaller than that noise. What it does show: all four beat the rubber stamp, and Jev is at least competitive on Magic cards despite being a small classifier. The next step is more cards.
- Keys live in an untracked `../.be` file (globally git-ignored). Run `source ../.be` before `./run`.

## Tests

```
uv run python -m unittest discover -s tests -t .
```

No network needed.

## Design

Three tiers; dependencies point downward only.

| Tier | Package | What lives there |
| ---- | ------- | ---------------- |
| I. Orchestration | `spell_power_eval/orchestration` | `evaluate` runs every classifier on every labeled card, and keeps going when one call fails. `report` builds the table and the results JSON. `http_app` serves the results page. |
| II. Domain | `spell_power_eval/domain` | `Card` (with `facts()`, the text every classifier sees), `Power`, `Usage` and `estimate_cost` (`pricing.py`), the shared `rubric`, `LabeledCard` (a card plus your score) and `Scorecard`, the `AlwaysBalanced` baseline, and the ports `Classifier`, `CardCatalog`, and `RunStore`. No I/O. |
| III. Interface | `spell_power_eval/adapters` | `ScryfallCatalog` (batched lookup, disk cache; the anti-corruption layer), `ClaudeClassifier`, `JevClassifier`, `LabelsFile`, `write_results`, `cards_page` (the HTML for `--page`). |

Every arm gets identical card facts and identical rubric wording (`domain/rubric.py`). Arithmetic such as power plus toughness per mana is computed in `Card.facts()`, because Jev's docs say to keep arithmetic in code.

## Ideas for later

- A results viewer: `./run --serve` serving an HTML page that draws a run's JSON (your score against each arm's, the error by card and arm, and each arm's reasons).
- More cards (the first run's gaps are inside the noise), and a second label source (17Lands win rates for one set).
- Self-consistency: ask Claude several times and compare to Jev's confidence.
- Few-shot examples in the card state, to see whether Jev's lack of fine-tuning matters.
