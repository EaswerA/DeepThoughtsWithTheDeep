import json
import os
from datetime import date
from typing import List
from src.models import Problem, UserProfile

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
PROBLEMS_FILE = os.path.join(DATA_DIR, "problems.json")
PROFILE_FILE = os.path.join(DATA_DIR, "profile.json")


def _date_to_str(d: date) -> str:
    return d.isoformat()


def _str_to_date(s: str) -> date:
    return date.fromisoformat(s)


def save_problems(problems: List[Problem]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    data = []
    for p in problems:
        d = p.__dict__.copy()
        d["next_review"] = _date_to_str(d["next_review"])
        data.append(d)
    with open(PROBLEMS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_problems() -> List[Problem]:
    if not os.path.exists(PROBLEMS_FILE):
        return []
    with open(PROBLEMS_FILE) as f:
        data = json.load(f)
    problems = []
    for d in data:
        d["next_review"] = _str_to_date(d["next_review"])
        problems.append(Problem(**d))
    return problems


def save_profile(profile: UserProfile) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PROFILE_FILE, "w") as f:
        json.dump(profile.__dict__, f, indent=2)


def load_profile() -> UserProfile:
    if not os.path.exists(PROFILE_FILE):
        return None
    with open(PROFILE_FILE) as f:
        data = json.load(f)
    return UserProfile(**data)
