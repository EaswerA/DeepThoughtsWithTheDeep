from dataclasses import dataclass, field
from datetime import date


@dataclass
class Problem:
    id: str
    title: str
    topic: str
    difficulty: str
    estimated_minutes: int
    times_reviewed: int = 0
    ease_factor: float = 2.5
    interval: int = 1
    next_review: date = field(default_factory=date.today)
    confidence: int = 0

    def urgency_score(self) -> float:
        days_overdue = (date.today() - self.next_review).days
        difficulty_weight = {"easy": 1.0, "medium": 1.5, "hard": 2.0}.get(self.difficulty, 1.0)
        low_confidence_boost = max(0, (3 - self.confidence) * 0.5)
        return days_overdue * difficulty_weight + low_confidence_boost

    def __lt__(self, other: "Problem") -> bool:
        # Reversed so heapq (min-heap) behaves as max-heap by urgency
        return self.urgency_score() > other.urgency_score()

    def __le__(self, other: "Problem") -> bool:
        return self.urgency_score() >= other.urgency_score()

    def __gt__(self, other: "Problem") -> bool:
        return self.urgency_score() < other.urgency_score()

    def __ge__(self, other: "Problem") -> bool:
        return self.urgency_score() <= other.urgency_score()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Problem):
            return False
        return self.id == other.id


@dataclass
class UserProfile:
    name: str
    daily_minutes: int
    topic_weights: dict = field(default_factory=dict)
