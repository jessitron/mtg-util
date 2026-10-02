# Anthropic API (Claude)

Docs: https://platform.claude.com/docs. Facts below were checked on 2026-10-02 unless marked otherwise.

## Models and prices
Model IDs take no date suffix. Prices are $ per million input/output tokens, as cached 2026-09-25:

| Short name | ID | Price |
| --- | --- | --- |
| haiku | `claude-haiku-4-5` | $1 / $5 |
| sonnet | `claude-sonnet-5-5` | $2 / $10 |
| opus | `claude-opus-5-5` | $4 / $20 |

Look up current prices and capabilities with `client.models.list()` or `client.models.retrieve(id)` before trusting this table.

## Calling it from Python
- `pip install anthropic` (or `dependencies = ["anthropic"]` in `pyproject.toml`).
- `anthropic.Anthropic()` finds credentials itself: `ANTHROPIC_API_KEY`, then `ANTHROPIC_AUTH_TOKEN`, then an `ant auth login` profile. An unset `ANTHROPIC_API_KEY` alone does not mean no credentials.
- Structured output: `client.messages.parse(model=..., max_tokens=..., system=..., messages=[...], output_format=<pydantic model>)`, then read `response.parsed_output` (it is `None` when the request stopped early or refused; check `stop_reason`). Verified on haiku-4-5, sonnet-5-5, and opus-5-5.
- Field order in the pydantic model is the order the model writes them. Put a `reason` field before the answer to get a short rationale before the commitment.
- Sonnet 5.5 and Opus 5.5 think by default, so leave room in `max_tokens` (we use 4096). Haiku 4.5 does not think by default.
- The SDK retries 429 and 5xx by itself (2 retries). Do not write your own loop.

## Used by
- [spell-power-eval](../spell-power-eval/README.md)
