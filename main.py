from src.cli import onboard, dashboard
from src.storage import load_problems, load_profile


def main():
    profile = load_profile()
    if not profile:
        profile = onboard()

    problems = load_problems()
    if not problems:
        print("No problems found. Make sure data/problems.json exists.")
        return

    while True:
        dashboard(profile, problems)


if __name__ == "__main__":
    main()
