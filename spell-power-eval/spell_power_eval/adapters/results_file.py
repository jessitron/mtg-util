import json
import os


def write_results(directory: str, stamp: str, results: dict) -> str:
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{stamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        f.write("\n")
    return path
