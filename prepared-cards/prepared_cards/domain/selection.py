from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Selection:
    """The card names the player wants. Each is wanted once; order of first mention is kept."""

    names: tuple[str, ...] = ()

    @classmethod
    def of(cls, names: Iterable[str]) -> "Selection":
        return cls(tuple(dict.fromkeys(n.strip() for n in names if n.strip())))

    def __len__(self) -> int:
        return len(self.names)
