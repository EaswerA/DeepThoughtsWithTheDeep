import heapq
from datetime import date
from typing import List
from src.models import Problem, UserProfile


def build_heap(problems: List[Problem]) -> List[Problem]:
    heap = problems[:]
    heapq.heapify(heap)
    return heap


def get_due_problems(problems: List[Problem]) -> List[Problem]:
    today = date.today()
    due = [p for p in problems if p.next_review <= today]
    heapq.heapify(due)
    return due


def greedy_schedule(problems: List[Problem], available_minutes: int) -> List[Problem]:
    """
    Greedy: pick problems by highest urgency_score / estimated_minutes ratio
    until time budget is exhausted.
    """
    due = get_due_problems(problems)

    candidates = sorted(
        due,
        key=lambda p: p.urgency_score() / max(p.estimated_minutes, 1),
        reverse=True
    )

    schedule = []
    remaining = available_minutes

    for problem in candidates:
        if problem.estimated_minutes <= remaining:
            schedule.append(problem)
            remaining -= problem.estimated_minutes
        if remaining <= 0:
            break

    return schedule
