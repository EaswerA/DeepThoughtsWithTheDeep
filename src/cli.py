import sys
from datetime import date
from src.models import Problem, UserProfile
from src.sm2 import apply_sm2
from src.scheduler import greedy_schedule, get_due_problems
from src.storage import load_problems, save_problems, load_profile, save_profile


SEPARATOR = "-" * 55


def onboard() -> UserProfile:
    print("\n  Welcome to DSA Revision Planner")
    print(SEPARATOR)
    name = input("  Your name: ").strip()
    minutes = int(input("  Daily study time (minutes): ").strip())
    profile = UserProfile(name=name, daily_minutes=minutes)
    save_profile(profile)
    print(f"\n  Profile saved. Let's go, {name}!\n")
    return profile


def dashboard(profile: UserProfile, problems: list) -> None:
    print(f"\n  {SEPARATOR}")
    print(f"  DSA Planner — {date.today()}  |  Budget: {profile.daily_minutes} min")
    print(f"  {SEPARATOR}")

    schedule = greedy_schedule(problems, profile.daily_minutes)
    due_count = len(get_due_problems(problems))

    print(f"  Problems due today: {due_count}")
    print(f"  Scheduled for you : {len(schedule)} problems\n")

    if not schedule:
        print("  Nothing due today. Come back tomorrow!")
        return

    for i, p in enumerate(schedule, 1):
        overdue = (date.today() - p.next_review).days
        overdue_str = f"  (+{overdue}d overdue)" if overdue > 0 else ""
        print(f"  [{i}] {p.title:<35} {p.topic:<15} {p.difficulty:<8} ~{p.estimated_minutes}min{overdue_str}")

    print()
    choice = input("  Enter problem number to solve, (p)rogress, or (q)uit: ").strip().lower()

    if choice == "q":
        print("\n  See you tomorrow!\n")
        sys.exit(0)
    elif choice == "p":
        show_progress(problems)
    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(schedule):
            solve_flow(schedule[idx], problems)
        else:
            print("  Invalid choice.")
    else:
        print("  Invalid choice.")


def solve_flow(problem: Problem, problems: list) -> None:
    print(f"\n  {SEPARATOR}")
    print(f"  Problem : {problem.title}")
    print(f"  Topic   : {problem.topic}")
    print(f"  Difficulty: {problem.difficulty}  |  Est. time: {problem.estimated_minutes} min")
    print(f"  {SEPARATOR}")
    input("  Press Enter when you're done solving...")

    print("\n  Rate your confidence:")
    print("    1 = Complete blackout")
    print("    2 = Incorrect but remembered upon seeing answer")
    print("    3 = Correct with significant difficulty")
    print("    4 = Correct after hesitation")
    print("    5 = Perfect recall")

    while True:
        try:
            rating = int(input("\n  Your rating (1-5): ").strip())
            if 1 <= rating <= 5:
                break
            print("  Please enter a number between 1 and 5.")
        except ValueError:
            print("  Please enter a number between 1 and 5.")

    updated = apply_sm2(problem, rating)

    for i, p in enumerate(problems):
        if p.id == updated.id:
            problems[i] = updated
            break

    save_problems(problems)

    print(f"\n  Saved! Next review in {updated.interval} day(s) ({updated.next_review})")
    print(f"  Ease factor: {updated.ease_factor:.2f}\n")


def show_progress(problems: list) -> None:
    print(f"\n  {SEPARATOR}")
    print("  Progress by Topic")
    print(f"  {SEPARATOR}")

    topics = {}
    for p in problems:
        if p.topic not in topics:
            topics[p.topic] = []
        topics[p.topic].append(p)

    for topic, probs in sorted(topics.items()):
        avg_confidence = sum(p.confidence for p in probs) / len(probs)
        reviewed = sum(1 for p in probs if p.times_reviewed > 0)
        bar = "#" * int(avg_confidence * 2)
        print(f"  {topic:<20} {reviewed}/{len(probs)} reviewed  conf: [{bar:<10}] {avg_confidence:.1f}/5")

    print()
    due_today = [p for p in problems if p.next_review <= date.today()]
    upcoming = sorted([p for p in problems if p.next_review > date.today()], key=lambda p: p.next_review)[:5]

    print(f"  Due today: {len(due_today)} problems")
    if upcoming:
        print("  Upcoming reviews:")
        for p in upcoming:
            print(f"    - {p.title:<35} due {p.next_review}")
    print()
