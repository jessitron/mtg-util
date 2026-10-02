import json
import os


def write_results(directory: str, stamp: str, results: dict) -> str:
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{stamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        f.write("\n")
    return path


class ResultsDirectory:
    """The RunStore over a directory of <timestamp>.json files. Names are file names; the caller vets them."""

    def __init__(self, directory: str):
        self.directory = directory

    def names(self) -> list[str]:
        if not os.path.isdir(self.directory):
            return []
        return sorted((n for n in os.listdir(self.directory) if n.endswith(".json")), reverse=True)

    def read(self, name: str):
        try:
            with open(os.path.join(self.directory, name), encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, NotADirectoryError):
            return None
