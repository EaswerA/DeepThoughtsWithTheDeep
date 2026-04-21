import heapq
from datetime import date
from typing import List, Tuple
from src.models import Problem


def get_due_problems(problems: List[Problem]) -> List[Problem]:
    today = date.today()
    return [p for p in problems if p.next_review <= today]


def greedy_schedule(problems: List[Problem], available_minutes: int) -> List[Tuple[Problem, bool]]:
    """
    Returns list of (problem, is_due) tuples.
    Fills time budget with due problems first (by urgency ratio),
    then pads remaining time with upcoming problems (by soonest due date).
    """
    today = date.today()

    due = sorted(
        [p for p in problems if p.next_review <= today],
        key=lambda p: p.urgency_score() / max(p.estimated_minutes, 1),
        reverse=True
    )
    upcoming = sorted(
        [p for p in problems if p.next_review > today],
        key=lambda p: p.next_review
    )

    schedule: List[Tuple[Problem, bool]] = []
    remaining = available_minutes

    for p in due:
        if p.estimated_minutes <= remaining:
            schedule.append((p, True))
            remaining -= p.estimated_minutes
        if remaining <= 0:
            break

    for p in upcoming:
        if remaining <= 0:
            break
        if p.estimated_minutes <= remaining:
            schedule.append((p, False))
            remaining -= p.estimated_minutes

    return schedule
