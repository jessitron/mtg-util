"""The human's labels, kept in a plain text file you edit by hand: `powerful | Lightning Bolt`."""
from dataclasses import dataclass

from ..domain.power import Power


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

    def read(self) -> tuple[dict[str, Power], list[str]]:
        """Returns (labels by card name, names still marked `?`)."""
        labels: dict[str, Power] = {}
        unlabeled: list[str] = []
        with open(self.path, encoding="utf-8") as f:
            for number, line in enumerate(f, start=1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                label, bar, name = line.partition("|")
                name = name.strip()
                if not bar or not name:
                    raise ValueError(f"{self.path}:{number}: expected `<weak|balanced|powerful|?> | <card name>`, got {line!r}")
                label = label.strip()
                if label in ("", "?"):
                    unlabeled.append(name)
                else:
                    labels[name] = Power.from_label(label)
        return labels, unlabeled
