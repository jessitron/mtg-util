"""Gateway to Honeycomb: one OpenTelemetry span per API call, in the GenAI semantic conventions.
Field names come from https://docs.honeycomb.io/send-data/use-cases/agents (see reference/honeycomb.md)."""
import json
import os
from contextlib import contextmanager
from typing import Optional

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter
from opentelemetry.trace import SpanKind, Status, StatusCode

from ..domain.ports import RecordedCall
from ..domain.power import Power

KEY_VARIABLE = "HONEYCOMB_API_KEY"
ENDPOINT_VARIABLE = "HONEYCOMB_API_ENDPOINT"  # https://api.eu1.honeycomb.io for EU teams
DEFAULT_ENDPOINT = "https://api.honeycomb.io"
SERVICE = "spell-power-eval"  # Honeycomb names the dataset after this
AGENT = "spell-power-eval"


def _text_message(role: str, text: str) -> dict:
    return {"role": role, "parts": [{"type": "text", "content": text}]}


def _score_error(call: RecordedCall) -> float:
    return abs(call.verdict.score - call.human_score)


class HoneycombTelemetry:
    def __init__(self, exporter: SpanExporter, processor_class=BatchSpanProcessor):
        self._provider = TracerProvider(resource=Resource.create({"service.name": SERVICE}))
        self._provider.add_span_processor(processor_class(exporter))
        self._tracer = self._provider.get_tracer(SERVICE)

    @classmethod
    def from_environment(cls) -> Optional["HoneycombTelemetry"]:
        """None when HONEYCOMB_API_KEY is not set, so the caller can say telemetry is off."""
        api_key = os.environ.get(KEY_VARIABLE)
        if not api_key:
            return None
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter  # deferred, so it costs nothing when off

        endpoint = os.environ.get(ENDPOINT_VARIABLE, DEFAULT_ENDPOINT).rstrip("/")
        return cls(OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces", headers={"x-honeycomb-team": api_key}))

    @contextmanager
    def run(self, run_id: str):
        attributes = {"gen_ai.operation.name": "invoke_agent", "gen_ai.agent.name": AGENT, "gen_ai.conversation.id": run_id}
        with self._tracer.start_as_current_span(f"invoke_agent {AGENT}", attributes=attributes):
            yield

    def record_call(self, call: RecordedCall) -> None:
        verdict = call.verdict
        model = verdict.call if verdict else None
        name = f"chat {model.request_model if model else call.classifier}"
        span = self._tracer.start_span(name, kind=SpanKind.CLIENT, start_time=call.started_ns)
        span.set_attributes(
            {
                "gen_ai.operation.name": "chat",
                "gen_ai.agent.name": AGENT,
                "gen_ai.conversation.id": call.run_id,
                "spell_eval.classifier": call.classifier,
                "spell_eval.card": call.card.name,
                "spell_eval.human_score": call.human_score,
                "spell_eval.human_label": Power.nearest(call.human_score).label,
            }
        )
        if model:
            span.set_attributes({"gen_ai.provider.name": model.provider, "gen_ai.request.model": model.request_model, "gen_ai.response.model": model.response_model})
            if model.finish_reasons:
                span.set_attribute("gen_ai.response.finish_reasons", list(model.finish_reasons))
            # Span events are deprecated, so the messages ride on the span itself.
            span.set_attributes(
                {
                    "gen_ai.input.messages": json.dumps([_text_message("user", model.input)]),
                    "gen_ai.output.messages": json.dumps([_text_message("assistant", model.output)]),
                }
            )
            if model.system:
                span.set_attribute("gen_ai.system_instructions", json.dumps([{"type": "text", "content": model.system}]))
        if verdict and verdict.usage:
            span.set_attributes({"gen_ai.usage.input_tokens": verdict.usage.input_tokens, "gen_ai.usage.output_tokens": verdict.usage.output_tokens})
        if call.cost_usd is not None:
            span.set_attribute("spell_eval.cost_usd", call.cost_usd)
        if call.error:
            span.set_attributes({"error.type": call.error.split(":")[0], "error.message": call.error})
            span.set_status(Status(StatusCode.ERROR, call.error))
        else:
            self._add_evaluation(span, call)
        span.end(end_time=call.ended_ns)

    def _add_evaluation(self, span, call: RecordedCall) -> None:
        verdict = call.verdict
        human = Power.nearest(call.human_score)
        steps_off = abs(verdict.power.value - human.value)
        facts = {
            "spell_eval.score": verdict.score,
            "spell_eval.label": verdict.power.label,
            "spell_eval.score_error": _score_error(call),  # distance from Jess's score
            "spell_eval.score_diff": verdict.score - call.human_score,  # signed: positive means more powerful than Jess said
            "spell_eval.steps_off": steps_off,
            "spell_eval.label_match": steps_off == 0,
            "spell_eval.reason": verdict.detail,
        }
        if verdict.confidence is not None:
            facts["spell_eval.confidence"] = verdict.confidence
        span.set_attributes(facts)
        explanation = f"{call.classifier} scored {verdict.score:.2f} ({verdict.power.label}); Jess scored {call.human_score:.2f} ({human.label}); off by {_score_error(call):.2f}."
        span.add_event(
            "gen_ai.evaluation.result",
            {
                "gen_ai.evaluation.name": "agreement_with_human_score",
                "gen_ai.evaluation.score.value": _score_error(call),
                "gen_ai.evaluation.score.label": "match" if steps_off == 0 else "mismatch",
                "gen_ai.evaluation.explanation": explanation,
            },
            timestamp=call.ended_ns,
        )

    def close(self) -> None:
        self._provider.shutdown()  # flushes the batch
