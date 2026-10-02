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
