"""The human's labels, kept in a plain text file you edit by hand: `powerful | Lightning Bolt`."""
from dataclasses import dataclass

from ..domain.power import Power


def _parse_score(text: str, where: str) -> float:
    try:
        score = float(text)
    except ValueError:
        return float(Power.from_label(text).value)
    if not 0 <= score <= 2:
        raise ValueError(f"{where}: a score runs from 0 (weak) to 2 (powerful), got {text}")
    return score


@dataclass(frozen=True)
class LabelsFile:
    path: str

    def names(self) -> list[str]:
        """Every card named in the file, judged or not, in file order."""
        labels, unlabeled = self.read()
        in_file = {*labels, *unlabeled}
        with open(self.path, encoding="utf-8") as f:
            ordered = [line.partition("|")[2].strip() for line in f if "|" in line and not line.lstrip().startswith("#")]
        return [name for name in ordered if name in in_file]

    def read(self) -> tuple[dict[str, float], list[str]]:
        """Returns (your 0-2 score by card name, names still marked `?`). A word is its level: weak 0, balanced 1, powerful 2."""
        labels: dict[str, float] = {}
        unlabeled: list[str] = []
        with open(self.path, encoding="utf-8") as f:
            for number, line in enumerate(f, start=1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                label, bar, name = line.partition("|")
                name = name.strip()
                if not bar or not name:
                    raise ValueError(f"{self.path}:{number}: expected `<0 to 2|weak|balanced|powerful|?> | <card name>`, got {line!r}")
                label = label.strip()
                if label in ("", "?"):
                    unlabeled.append(name)
                else:
                    labels[name] = _parse_score(label, f"{self.path}:{number}")
        return labels, unlabeled
