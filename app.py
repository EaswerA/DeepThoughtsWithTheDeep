from flask import Flask, jsonify, request, render_template
from datetime import date, timedelta
import calendar as cal_module
from src.models import Problem, UserProfile
from src.sm2 import apply_sm2
from src.scheduler import greedy_schedule, get_due_problems
from src.storage import load_problems, save_problems, load_profile, save_profile

app = Flask(__name__)


def problem_to_dict(p: Problem, is_due: bool = True) -> dict:
    today = date.today()
    leetcode_url = f"https://leetcode.com/problems/{p.leetcode_slug}/" if p.leetcode_slug else None
    last_review = None
    if p.times_reviewed > 0:
        last_review = (p.next_review - timedelta(days=p.interval)).isoformat()
    return {
        "id": p.id,
        "title": p.title,
        "topic": p.topic,
        "difficulty": p.difficulty,
        "estimated_minutes": p.estimated_minutes,
        "leetcode_slug": p.leetcode_slug,
        "leetcode_url": leetcode_url,
        "times_reviewed": p.times_reviewed,
        "ease_factor": round(p.ease_factor, 3),
        "interval": p.interval,
        "next_review": p.next_review.isoformat(),
        "confidence": p.confidence,
        "urgency": round(p.urgency_score(), 2),
        "days_overdue": (today - p.next_review).days,
        "is_due": p.next_review <= today,
        "is_scheduled_fill": not is_due,
        "last_review": last_review,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/profile", methods=["GET"])
def get_profile():
    profile = load_profile()
    if not profile:
        return jsonify(None), 200
    return jsonify(profile.__dict__)


@app.route("/api/profile", methods=["POST"])
def create_profile():
    data = request.get_json()
    if not data or not data.get("name") or not data.get("daily_minutes"):
        return jsonify({"error": "name and daily_minutes required"}), 400
    profile = UserProfile(name=data["name"], daily_minutes=int(data["daily_minutes"]))
    save_profile(profile)
    return jsonify(profile.__dict__)


@app.route("/api/schedule", methods=["GET"])
def get_schedule():
    profile = load_profile()
    if not profile:
        return jsonify({"error": "No profile found"}), 400
    problems = load_problems()
    pairs = greedy_schedule(problems, profile.daily_minutes)
    due_count = len(get_due_problems(problems))

    schedule = [problem_to_dict(p, is_due) for p, is_due in pairs]
    total_mins = sum(p["estimated_minutes"] for p in schedule)
    overdue_count = sum(1 for p in schedule if p["days_overdue"] > 0)

    return jsonify({
        "schedule": schedule,
        "due_count": due_count,
        "total_scheduled_minutes": total_mins,
        "overdue_count": overdue_count,
        "profile": profile.__dict__,
        "today": date.today().isoformat(),
    })


@app.route("/api/problems", methods=["GET"])
def get_problems():
    problems = load_problems()
    today = date.today()
    return jsonify([problem_to_dict(p, p.next_review <= today) for p in problems])


@app.route("/api/problems/<problem_id>/review", methods=["POST"])
def review_problem(problem_id):
    data = request.get_json()
    if not data or "rating" not in data:
        return jsonify({"error": "rating required"}), 400
    rating = int(data["rating"])
    if not (1 <= rating <= 5):
        return jsonify({"error": "rating must be 1-5"}), 400

    problems = load_problems()
    for i, p in enumerate(problems):
        if p.id == problem_id:
            updated = apply_sm2(p, rating)
            problems[i] = updated
            save_problems(problems)
            return jsonify(problem_to_dict(updated))

    return jsonify({"error": "Problem not found"}), 404


@app.route("/api/progress", methods=["GET"])
def get_progress():
    problems = load_problems()
    today = date.today()
    topics: dict = {}

    for p in problems:
        if p.topic not in topics:
            topics[p.topic] = []
        topics[p.topic].append(p)

    topic_stats = {}
    for topic, probs in topics.items():
        avg_conf = sum(p.confidence for p in probs) / len(probs)
        reviewed_count = sum(1 for p in probs if p.times_reviewed > 0)
        topic_stats[topic] = {
            "total": len(probs),
            "reviewed": reviewed_count,
            "avg_confidence": round(avg_conf, 2),
            "problems": [problem_to_dict(p, p.next_review <= today) for p in probs],
        }

    due_today = [problem_to_dict(p) for p in problems if p.next_review <= today]
    upcoming = sorted(
        [problem_to_dict(p) for p in problems if p.next_review > today],
        key=lambda p: p["next_review"]
    )[:15]

    # Build heatmap: last 60 days activity (approximated from last review date)
    heatmap = {}
    for p in problems:
        if p.times_reviewed > 0:
            last_review_date = (p.next_review - timedelta(days=p.interval)).isoformat()
            heatmap[last_review_date] = heatmap.get(last_review_date, 0) + 1

    # Overall mastery: weighted by confidence
    total_conf = sum(p.confidence for p in problems)
    max_conf = len(problems) * 5
    overall_mastery = round((total_conf / max_conf) * 100, 1) if max_conf > 0 else 0

    return jsonify({
        "topics": topic_stats,
        "due_today": due_today,
        "upcoming": upcoming,
        "total_problems": len(problems),
        "total_reviewed": sum(1 for p in problems if p.times_reviewed > 0),
        "overall_mastery": overall_mastery,
        "heatmap": heatmap,
    })


@app.route("/api/calendar", methods=["GET"])
def get_calendar():
    try:
        year = int(request.args.get("year", date.today().year))
        month = int(request.args.get("month", date.today().month))
    except ValueError:
        return jsonify({"error": "invalid year/month"}), 400

    problems = load_problems()
    today = date.today()

    by_date: dict = {}
    for p in problems:
        key = p.next_review.isoformat()
        if key not in by_date:
            by_date[key] = []
        by_date[key].append(problem_to_dict(p, p.next_review <= today))

    cal = cal_module.Calendar(firstweekday=6)
    weeks = cal.monthdatescalendar(year, month)

    weeks_out = []
    for week in weeks:
        week_out = []
        for day in week:
            key = day.isoformat()
            probs = by_date.get(key, [])
            week_out.append({
                "date": key,
                "day": day.day,
                "in_month": day.month == month,
                "is_today": day == today,
                "is_past": day < today,
                "problems": probs,
                "easy_count": sum(1 for p in probs if p["difficulty"] == "easy"),
                "medium_count": sum(1 for p in probs if p["difficulty"] == "medium"),
                "hard_count": sum(1 for p in probs if p["difficulty"] == "hard"),
            })
        weeks_out.append(week_out)

    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1

    return jsonify({
        "year": year,
        "month": month,
        "month_name": cal_module.month_name[month],
        "weeks": weeks_out,
        "prev": {"year": prev_year, "month": prev_month},
        "next": {"year": next_year, "month": next_month},
        "today": today.isoformat(),
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
