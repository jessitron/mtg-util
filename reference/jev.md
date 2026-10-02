# Jev (TypeSafe AI)

A "System One" model: it reads a state and answers typed questions with probabilities. It writes no text.

Docs: https://docs.typesafe.ai/ (index for agents: https://docs.typesafe.ai/llms.txt). Read from the docs on 2026-10-02; no live call has been made yet.

## HTTP API

- `POST https://api.typesafe.ai/v1/systemone`
- Headers: `Authorization: Bearer <API_KEY>`, `Content-Type: application/json`
- Body: `model` (`"jev-latest"`), `state` (string, object, or array), `questions` (a map of your own ids to question objects).
- Several questions in one request are allowed. Errors: 401 bad key, 422 invalid body, 429 rate limited, 529 overloaded.
- The key's environment variable name, `TYPESAFE_API_KEY`, comes from a LangChain write-up and is unconfirmed. The docs index lists a Python SDK (`TypeSafeClient`) and a JavaScript SDK.

## Question types

```json
{"type": "choice", "instructions": "...", "criteria": {"option_name": "description of that option"}}
{"type": "score",  "instructions": "...", "criteria": ["level 0 description", "level 1 description", "level 2 description"]}
{"type": "noul",   "instructions": "..."}
```

- Choice: up to 255 options. Answer: `{"type":"choice","choice":"option_name","confidence":0.95,"probabilities":{...}}`.
- Score: 2 to 10 levels, listed in order. Answer: `{"type":"score","score":1.43,"confidence":0.35,"legend":{"0":"...","1":"..."},"probabilities":{"0":0.0,"1":0.57,"2":0.43}}`. Probabilities are keyed by level number.
- Noul: yes/no, answer is a probability from 0 to 1.
- Response: `{"model":"jev-1.13.0","answers":{"<id>":{...}},"usage":{"input_tokens":N,"output_tokens":N}}`.

## Writing questions

- Describe situations, not degrees. "Use as many levels as you can describe distinctly."
- Keep each Score to one dimension.

## Known weak spots (Jev 1.13)

From https://docs.typesafe.ai/model-jaggedness/jev-1.13.md:

- Does not count reliably, is poor at arithmetic, and compares numbers badly. "Keep the arithmetic in code."
- Quite literal. Double negatives and indirection fail.
- Large irrelevant state hurts accuracy. Adversarial content in the state can steer it.
- Not trained to generate text; no fine-tuning offered.

## Corrections to what third parties wrote

A DEV Community article showed an OpenRouter call (`typesafe/jev-1.13`) with `questions` as a list of `{type, text, options}`. That does not match TypeSafe's own docs above. Trust the docs.

## Used by

- [spell-power-eval](../spell-power-eval/README.md)
