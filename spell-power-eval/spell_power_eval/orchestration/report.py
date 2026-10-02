from .evaluation import Evaluation


def _dollars(cost) -> str:
    return "-" if cost is None else f"${cost:.4f}"


def _cell(evaluation: Evaluation, name: str, classifier: str, expected) -> str:
    attempt = evaluation.attempts[(name, classifier)]
    if attempt.verdict is None:
        return "ERROR"
    mark = "✓" if attempt.verdict.power == expected else "✗"
    return f"{attempt.verdict.score:.1f} {attempt.verdict.power.label} {mark} {_dollars(attempt.cost(classifier))}"


def _table(rows: list[list[str]]) -> str:
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    return "\n".join("  ".join(cell.ljust(width) for cell, width in zip(row, widths)).rstrip() for row in rows)


def text_report(evaluation: Evaluation) -> str:
    header = ["card", "yours", *evaluation.classifiers, "edhrec rank"]
    rows = [header]
    for labeled in evaluation.cards:
        name = labeled.card.name
        rank = labeled.card.edhrec_rank
        rows.append([name, f"{labeled.score:.1f} {labeled.expected.label}", *(_cell(evaluation, name, c, labeled.expected) for c in evaluation.classifiers), str(rank) if rank else "-"])

    summary = [["classifier", "exact", "mean steps off", "mean score error", "failed", "est. cost"]]
    for classifier in evaluation.classifiers:
        card = evaluation.scorecard(classifier)
        summary.append([classifier, f"{card.exact}/{card.answered}", f"{card.mean_ordinal_error:.2f}", f"{card.mean_score_error:.2f}", str(card.failed), _dollars(evaluation.cost(classifier))])

    errors = [
        f"  {classifier} on {name}: {attempt.error}"
        for (name, classifier), attempt in evaluation.attempts.items()
        if attempt.error
    ]
    parts = [_table(rows), "", _table(summary)]
    if errors:
        parts += ["", "Errors:", *errors]
    parts += ["", "edhrec rank: lower is more popular in Commander. It is context, not ground truth."]
    parts += ["est. cost: tokens the API reported times cached prices (domain/pricing.py); Claude's output tokens include thinking."]
    return "\n".join(parts)


def _usage_json(usage) -> dict | None:
    return {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens} if usage else None


def results_json(evaluation: Evaluation, models: dict) -> dict:
    """Everything needed to look at a run later, including each classifier's reasons."""
    cards = []
    for labeled in evaluation.cards:
        answers = {}
        for classifier in evaluation.classifiers:
            attempt = evaluation.attempts[(labeled.card.name, classifier)]
            answers[classifier] = (
                {"error": attempt.error}
                if attempt.error
                else {"power": attempt.verdict.power.label, "score": attempt.verdict.score, "confidence": attempt.verdict.confidence, "detail": attempt.verdict.detail, "usage": _usage_json(attempt.verdict.usage), "cost_usd": attempt.cost(classifier)}
            )
        cards.append({"name": labeled.card.name, "image_url": labeled.card.image_url, "mana_cost": labeled.card.mana_cost, "yours": labeled.expected.label, "yours_score": labeled.score, "edhrec_rank": labeled.card.edhrec_rank, "answers": answers})
    scorecards = {
        c: {
            "exact": s.exact,
            "answered": s.answered,
            "failed": s.failed,
            "mean_ordinal_error": s.mean_ordinal_error,
            "mean_score_error": s.mean_score_error,
            "cost_usd": evaluation.cost(c),
            "confusion": {f"{expected}->{got}": n for (expected, got), n in s.confusion.items()},
        }
        for c in evaluation.classifiers
        for s in [evaluation.scorecard(c)]
    }
    return {"models": models, "cards": cards, "scorecards": scorecards}
