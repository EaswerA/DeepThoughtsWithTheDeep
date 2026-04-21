from flask import Flask, jsonify, request, render_template
from datetime import date
from src.models import Problem, UserProfile
from src.sm2 import apply_sm2
from src.scheduler import greedy_schedule, get_due_problems
from src.storage import load_problems, save_problems, load_profile, save_profile

app = Flask(__name__)


def problem_to_dict(p: Problem) -> dict:
    return {
        "id": p.id,
        "title": p.title,
        "topic": p.topic,
        "difficulty": p.difficulty,
        "estimated_minutes": p.estimated_minutes,
        "times_reviewed": p.times_reviewed,
        "ease_factor": round(p.ease_factor, 3),
        "interval": p.interval,
        "next_review": p.next_review.isoformat(),
        "confidence": p.confidence,
        "urgency": round(p.urgency_score(), 2),
        "days_overdue": (date.today() - p.next_review).days,
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
    schedule = greedy_schedule(problems, profile.daily_minutes)
    return jsonify({
        "schedule": [problem_to_dict(p) for p in schedule],
        "due_count": len(get_due_problems(problems)),
        "profile": profile.__dict__,
        "today": date.today().isoformat(),
    })


@app.route("/api/problems", methods=["GET"])
def get_problems():
    problems = load_problems()
    return jsonify([problem_to_dict(p) for p in problems])


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
            "problems": [problem_to_dict(p) for p in probs],
        }

    today = date.today()
    due_today = [problem_to_dict(p) for p in problems if p.next_review <= today]
    upcoming = sorted(
        [problem_to_dict(p) for p in problems if p.next_review > today],
        key=lambda p: p["next_review"]
    )[:10]

    return jsonify({
        "topics": topic_stats,
        "due_today": due_today,
        "upcoming": upcoming,
        "total_problems": len(problems),
        "total_reviewed": sum(1 for p in problems if p.times_reviewed > 0),
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
