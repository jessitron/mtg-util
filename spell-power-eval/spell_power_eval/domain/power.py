from enum import Enum


class Power(Enum):
    """How strong a spell is for its mana cost. The values are ordered, so the distance between two verdicts means something."""

    WEAK = 0
    BALANCED = 1
    POWERFUL = 2

    @property
    def label(self) -> str:
        return self.name.lower()

    @classmethod
    def from_label(cls, text: str) -> "Power":
        try:
            return cls[text.strip().upper()]
        except KeyError:
            raise ValueError(f"not a power label: {text!r} (use weak, balanced, or powerful)") from None

    @classmethod
    def nearest(cls, level: float) -> "Power":
        """The label closest to a fractional level, such as a Score answer of 1.43."""
        return cls(min(max(int(level + 0.5), 0), len(cls) - 1))
