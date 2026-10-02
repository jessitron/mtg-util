#!/usr/bin/env python3
"""Composition root: choose the adapters, hand them to the use case, print the report."""
import argparse
import os
import sys
from datetime import datetime, timezone

from spell_power_eval.adapters.claude_classifier import CLAUDE_MODELS, ClaudeClassifier
from spell_power_eval.adapters.jev_classifier import KEY_VARIABLE, JevClassifier
from spell_power_eval.adapters.labels_file import LabelsFile
from spell_power_eval.adapters.results_file import write_results
from spell_power_eval.adapters.scryfall_catalog import ScryfallCatalog
from spell_power_eval.domain.baseline import AlwaysBalanced
from spell_power_eval.domain.rubric import CLAUDE_SYSTEM_PROMPT
from spell_power_eval.domain.scoring import LabeledCard
from spell_power_eval.orchestration.evaluation import evaluate
from spell_power_eval.orchestration.report import results_json, text_report

HERE = os.path.dirname(os.path.abspath(__file__))

CLASSIFIERS = {
    "always-balanced": AlwaysBalanced,
    "haiku": lambda: ClaudeClassifier("haiku"),
    "sonnet": lambda: ClaudeClassifier("sonnet"),
    "opus": lambda: ClaudeClassifier("opus"),
    "jev-choice": lambda: JevClassifier("choice"),
    "jev-score": lambda: JevClassifier("score"),
}
DEFAULT_ARMS = ["always-balanced", "haiku", "sonnet", "jev-choice", "jev-score"]


def main():
    parser = argparse.ArgumentParser(description="Compare classifiers against your hand labels of MTG spells.")
    parser.add_argument("classifiers", nargs="*", metavar="CLASSIFIER",
                        help=f"any of: {', '.join(CLASSIFIERS)}. Default: {' '.join(DEFAULT_ARMS)}")
    parser.add_argument("--labels", default=os.path.join(HERE, "labels.txt"))
    parser.add_argument("--dry-run", action="store_true", help="look up the cards and print what the classifiers would be asked; call no model")
    args = parser.parse_args()
    unknown = [c for c in args.classifiers if c not in CLASSIFIERS]
    if unknown:
        parser.error(f"unknown classifier {unknown[0]!r}; choose from {', '.join(CLASSIFIERS)}")

    labels, unlabeled = LabelsFile(args.labels).read()
    if unlabeled:
        print(f"Skipping {len(unlabeled)} card(s) still marked `?` in {args.labels}: {', '.join(unlabeled)}", file=sys.stderr)
    if not labels:
        sys.exit(f"No labeled cards. Replace the `?` in {args.labels} with weak, balanced, or powerful.")

    try:
        cards = ScryfallCatalog(os.path.join(HERE, "scryfall-cache.json")).find(list(labels))
    except LookupError as e:
        sys.exit(str(e))
    labeled = [LabeledCard(card, labels[name]) for name, card in zip(labels, cards)]

    arms = args.classifiers or DEFAULT_ARMS
    if args.dry_run:
        print(f"SYSTEM PROMPT FOR CLAUDE\n{CLAUDE_SYSTEM_PROMPT}\n")
        for item in labeled:
            print(f"--- {item.card.name} (yours: {item.expected.label}, edhrec rank {item.card.edhrec_rank})\n{item.card.facts()}\n")
        print(f"Would run: {', '.join(arms)}", file=sys.stderr)
        return
    if not os.environ.get(KEY_VARIABLE):
        skipped = [a for a in arms if a.startswith("jev")]
        if skipped:
            print(f"Skipping {', '.join(skipped)}: {KEY_VARIABLE} is not set.", file=sys.stderr)
            arms = [a for a in arms if a not in skipped]

    evaluation = evaluate(labeled, [CLASSIFIERS[a]() for a in arms], on_progress=lambda m: print(m, file=sys.stderr))
    print(text_report(evaluation))
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = write_results(os.path.join(HERE, "results"), stamp, results_json(evaluation, {a: CLAUDE_MODELS.get(a, "") for a in arms}))
    print(f"\nWrote {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
