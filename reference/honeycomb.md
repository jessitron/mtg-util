# Honeycomb (GenAI / agent telemetry)

Source: https://docs.honeycomb.io/send-data/use-cases/agents (read 2026-10-02). Honeycomb takes OpenTelemetry, and its GenAI views key off the GenAI semantic-convention fields.

## Sending

- OTLP over HTTP: `POST https://api.honeycomb.io/v1/traces` (EU: `https://api.eu1.honeycomb.io`), header `x-honeycomb-team: <ingest key>`. The docs page names no endpoint; this is Honeycomb's general OTLP setup.
- The dataset is named for the resource attribute `service.name`.
- Keep the ingest key in `HONEYCOMB_API_KEY` (`.be` at the repo root).

## Fields the agents page lists

Required on spans: `gen_ai.conversation.id`, `gen_ai.agent.name`, `gen_ai.operation.name` (`chat`, `invoke_agent`, `execute_tool`, `embeddings`, ...).

Optional on spans: `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.request.model`, `gen_ai.response.model`, `gen_ai.response.finish_reasons` (string array), and for tools `gen_ai.tool.name`, `gen_ai.tool.call.id`, `gen_ai.tool.call.arguments`, `gen_ai.tool.call.result`.

Span events: `gen_ai.input.messages`, `gen_ai.output.messages` (JSON; may hold PII), `gen_ai.evaluation.result` (feeds the GenAI tab).

Span names follow `{operation} {identifier}`, such as `chat claude-haiku-4-5`. Errors use `error.type` and `error.message`.

## Shapes we chose (from the OTel GenAI semconv, not the Honeycomb page)

- Messages are JSON strings: `[{"role": "user", "parts": [{"type": "text", "content": "..."}]}]`. OTel attributes can't hold nested objects.
- The inference event is named `gen_ai.client.inference.operation.details`; the messages and `gen_ai.system_instructions` ride on it.
- The evaluation event carries `gen_ai.evaluation.name`, `.score.value`, `.score.label`, `.explanation`.
- `gen_ai.provider.name` names the vendor (`anthropic`).

See [spell-power-eval](../spell-power-eval/README.md) for which of our own fields (`spell_eval.*`) sit beside them.

## What arrived in Honeycomb (checked 2026-10-02, via the Honeycomb MCP)

- **Honeycomb recognizes the trace as GenAI.** `get_aiconversation` classifies the root as `agentInvocation` and each `chat` span as `llmOperation`, and counts the LLM calls and tokens. Honeycomb also adds `io.honeycomb.gen_ai.cost.*` columns to spans whose model it can price (Claude yes, Jev no).
- **Events arrive as real span events** (`meta.annotation_type = span_event`), not columns on the span. They share the span's `trace.parent_id`, so query them with a filter on `meta.annotation_type exists`.
- **Event attributes are namespaced columns**: `gen_ai.evaluation.score.value` (float), `gen_ai.evaluation.score.label`, `gen_ai.evaluation.explanation`. A bare `score.value` is not a column.
- **Arrays are flattened to a JSON string.** We send `gen_ai.response.finish_reasons` as a list; the column is a string holding `["end_turn"]`. Match it with `contains`, not as an array.
- **`gen_ai.provider.name` for Jev is `typesafe`**; its `gen_ai.response.model` is the pinned version (`jev-1.13.0`), while Claude's is the dated name (`claude-haiku-4-5-20251001`).
- **`get_aiconversation` can miss the last span.** Its window is truncated to whole seconds, so a span that starts just after the last second is left out ("LLM Calls: 1" for a trace with two). Pass `event_timestamp` a second or so after the run to see them all.
- **Column names are checked per dataset.** A column that no event has written does not exist, and a query on it fails with "unknown column". `get_dataset_columns` lists what is there.
- **Boards need saved query runs.** Run each query first (`run_query` returns a `query_run_pk`), then pass the run PKs to `create_board`. The spell-power-eval board is linked from its README.
