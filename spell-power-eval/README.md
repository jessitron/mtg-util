# spell-power-eval

Which classifier agrees best with you about whether a Magic spell is **weak**, **balanced**, or **powerful** for its mana cost?

You label a few cards by hand. The script asks each classifier about the same cards, then compares their answers to yours.

| Arm | What it is |
| --- | ---------- |
| `always-balanced` | The floor: says "balanced" for everything. |
| `haiku`, `sonnet`, `opus` | Claude (`claude-haiku-4-5`, `claude-sonnet-5-5`, `claude-opus-5-5`), through the Anthropic SDK with structured output (a one-sentence reason, then the verdict). |
| `jev-choice` | TypeSafe's Jev, asked to choose weak / balanced / powerful. |
| `jev-score` | Jev, asked to rate on an ordered three-level rubric. A score of 1.43 rounds to balanced. |

Background on Jev and why we compare it: `references/jev.md` in the infra repo. API facts: [reference/jev.md](../reference/jev.md).

## Usage

1. Edit `labels.txt`. Replace each `?` with `weak`, `balanced`, or `powerful`. **Label before you look at any model's answer**, so the models can't anchor you. Add or swap cards freely; a card marked `?` is skipped and costs nothing.
2. Look at what the models will be asked (free; calls Scryfall once, no model):
   ```
   ./run --dry-run
   ```
3. Run it:
   ```
   ./run                  # always-balanced haiku sonnet jev-choice jev-score
   ./run haiku opus       # just these arms
   ```

The report prints a card-by-card table (✓ means it matched your label), then one summary line per arm: exact matches, and the **mean steps off**. Calling a weak card balanced is 1 step off. Calling it powerful is 2. Each run also writes `results/<timestamp>.json` with every classifier's reason (Claude) or probabilities (Jev), plus a confusion count per arm.

The `edhrec rank` column comes from Scryfall (lower means more popular in Commander). It is context for your labels, not ground truth, and no classifier sees it.

## Credentials (environment variables)

- Claude: the Anthropic SDK finds credentials itself: `ANTHROPIC_API_KEY` (create one in the Anthropic Console), or an `ant auth login` profile.
- Jev: `TYPESAFE_API_KEY`, from https://console.typesafe.ai/keys. Without it the `jev-*` arms are skipped with a message.

## Cost

Ten cards is a few cents at most. Each card is about 150-300 input tokens and a short answer. Prices ($ per million input/output tokens, cached 2026-09-25): Haiku 4.5 $1/$5, Sonnet 5.5 $2/$10, Opus 5.5 $4/$20, Jev $0.042 input and free output. Sonnet and Opus think by default, so they use more output tokens than Haiku.

## Status

- Unit tests pass, and the Scryfall lookup is verified live.
- **The Claude and Jev adapters have never called the real APIs.** Their request shapes come from SDK docs and TypeSafe's docs, and the tests use fakes. Expect to fix something on the first real run. Whether Haiku 4.5 accepts the SDK's structured-output call (`messages.parse`) is unconfirmed.

## Tests

```
uv run python -m unittest discover -s tests -t .
```

No network needed.

## Design

Three tiers; dependencies point downward only.

| Tier | Package | What lives there |
| ---- | ------- | ---------------- |
| I. Orchestration | `spell_power_eval/orchestration` | `evaluate` runs every classifier on every labeled card, and keeps going when one call fails. `report` builds the table and the results JSON. |
| II. Domain | `spell_power_eval/domain` | `Card` (with `facts()`, the text every classifier sees), `Power`, the shared `rubric`, `Scorecard`, the `AlwaysBalanced` baseline, and the ports `Classifier` and `CardCatalog`. No I/O. |
| III. Interface | `spell_power_eval/adapters` | `ScryfallCatalog` (batched lookup, disk cache; the anti-corruption layer), `ClaudeClassifier`, `JevClassifier`, `LabelsFile`, `write_results`. |

Every arm gets identical card facts and identical rubric wording (`domain/rubric.py`). Arithmetic such as power plus toughness per mana is computed in `Card.facts()`, because Jev's docs say to keep arithmetic in code.

## Ideas for later

- More cards, and a second label source (17Lands win rates for one set).
- Self-consistency: ask Claude several times and compare to Jev's confidence.
- Few-shot examples in the card state, to see whether Jev's lack of fine-tuning matters.
