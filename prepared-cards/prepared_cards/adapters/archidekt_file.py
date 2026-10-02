"""Keeps the selection in a text file in Archidekt's import format: one `1 Card Name` per line."""
import os

from ..domain.selection import Selection


class ArchidektImportFile:
    def __init__(self, path: str):
        self.path = path

    def load(self) -> Selection:
        if not os.path.exists(self.path):
            return Selection()
        with open(self.path) as f:
            lines = (line.strip() for line in f)
            return Selection.of(line.split(" ", 1)[1] for line in lines if " " in line)

    def render(self, selection: Selection) -> str:
        return "".join(f"1 {name}\n" for name in selection.names)

    def save(self, selection: Selection) -> None:
        with open(self.path, "w") as f:
            f.write(self.render(selection))
