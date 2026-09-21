import os
from flask import Flask, render_template, request, jsonify
import db

app = Flask(__name__)


@app.route("/")
def index():
    db.init_db()
    category = request.args.get("category", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    categories = db.get_categories()
    jobs = db.get_jobs(
        category=category if category and category.lower() != "all" else None,
        start_date=start_date or None,
        end_date=end_date or None,
    )
    stats = db.get_stats()

    return render_template(
        "index.html",
        jobs=jobs,
        categories=categories,
        selected_category=category,
        start_date=start_date,
        end_date=end_date,
        stats=stats,
    )


@app.route("/api/jobs")
def api_jobs():
    db.init_db()
    category = request.args.get("category", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    jobs = db.get_jobs(
        category=category if category and category.lower() != "all" else None,
        start_date=start_date or None,
        end_date=end_date or None,
    )
    return jsonify({"count": len(jobs), "jobs": jobs})


if __name__ == "__main__":
    db.init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)
