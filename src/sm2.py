from datetime import date, timedelta
from src.models import Problem


def apply_sm2(problem: Problem, rating: int) -> Problem:
    """
    SM-2 algorithm: updates interval, ease factor, and next review date.
    rating: 1 (blackout) to 5 (perfect recall)
    """
    if rating < 3:
        # Failed recall — reset repetitions and interval but keep ease_factor update
        problem.interval = 1
        problem.times_reviewed = 0
    else:
        if problem.times_reviewed == 0:
            problem.interval = 1
        elif problem.times_reviewed == 1:
            problem.interval = 6
        else:
            problem.interval = max(1, round(problem.interval * problem.ease_factor))

        problem.times_reviewed += 1

    # Update ease factor (minimum 1.3)
    problem.ease_factor = max(
        1.3,
        problem.ease_factor + 0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02)
    )

    problem.confidence = rating
    problem.next_review = date.today() + timedelta(days=problem.interval)
    return problem
