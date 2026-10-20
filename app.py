"""JobGetter dashboard.

A small local web app (http://localhost:5050) that shows jobs, drafts, questions
and the application tracker. All data lives in plain files:
  jobs/<job_id>/job.json   one folder per job (posting, score, drafts, status)
  data/queue.json          requests for Claude (draft anyway, changes, filling...)
  settings.json            platform settings (auto-submit is OFF by default)
  me/                      your files (source of truth, read here, rarely written)
"""
import json
import re
import uuid
from datetime import date, datetime
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, send_from_directory, url_for

from tools import build, signin, sources
from tools.common import first_name, norm_company, setup_done, settings as load_settings_full

ROOT = Path(__file__).resolve().parent
JOBS_DIR = ROOT / "jobs"
DATA_DIR = ROOT / "data"
QUEUE_FILE = DATA_DIR / "queue.json"
SETTINGS_FILE = ROOT / "settings.json"
ME = ROOT / "me"
STANDARD_ANSWERS = ME / "standard-answers" / "standard-answers.md"
PAST_APPLICATIONS = ME / "target-companies" / "past-applications.md"

# Statuses, in the order a job normally moves through them.
STATUS_LABELS = {
    "new": "New",
    "drafting": "Being drafted",
    "ready_for_review": "Ready for your review",
    "needs_answers": "Paused: needs your answer",
    "changes_requested": "Changes requested",
    "approved": "Approved, waiting to be filled in",
    "prepared": "Prepared: ready to fill",
    "needs_you": "Needs you",
    "filling": "Being filled in",
    "filled": "Ready to submit",
    "submitted": "Submitted",
    "interview": "Interview",
    "offer": "Offer",
    "rejected": "Rejected by employer",
    "withdrawn": "Withdrawn",
    "not_applying": "Not applying",
    "filtered": "Left out (breaks a hard limit)",
    "not_eligible": "Not eligible",
}
TRACKER_STATUSES = ["approved", "filling", "filled", "submitted", "interview", "offer", "rejected", "withdrawn"]
SHEET_STATUSES = ["filled", "needs_you", "prepared", "filling"]  # shown on the review sheet
REVIEW_STATUSES = ["ready_for_review", "needs_answers", "changes_requested", "drafting"]

app = Flask(__name__)


# ---------- storage helpers ----------

def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_settings():
    return load_settings_full()


def load_jobs():
    jobs = []
    for f in sorted(JOBS_DIR.glob("*/job.json")):
        job = read_json(f, None)
        if job:
            jobs.append(job)
    return jobs


def load_job(job_id):
    job = read_json(JOBS_DIR / job_id / "job.json", None)
    if not job:
        abort(404)
    return job


def save_job(job):
    write_json(JOBS_DIR / job["id"] / "job.json", job)


def log(job, event):
    job.setdefault("history", []).append({"date": now(), "event": event})


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def load_queue():
    return read_json(QUEUE_FILE, [])


def add_to_queue(kind, job_id, text=""):
    queue = load_queue()
    queue.append({"id": uuid.uuid4().hex[:8], "type": kind, "job_id": job_id,
                  "text": text, "created": now(), "status": "pending"})
    write_json(QUEUE_FILE, queue)


# ---------- reading your files in me/ ----------

def norm(name):
    """Normalise a company name or title for matching ('Acme Ltd' ~ 'acme')."""
    return norm_company(name)


def past_applications():
    """Rows of the table(s) in past-applications.md: | date | company | role | status |."""
    rows = []
    if not PAST_APPLICATIONS.exists():
        return rows
    text = PAST_APPLICATIONS.read_text(encoding="utf-8")
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 4 and re.match(r"\d{4}-\d{2}-\d{2}", cells[0]):
            rows.append({"date": cells[0], "company": cells[1], "role": cells[2], "status": cells[3]})
    return rows


def applied_before(company):
    key = norm(company)
    return [r for r in past_applications() if key and norm(r["company"]) == key]


def add_past_application(job):
    """Insert a row at the top of the table in past-applications.md."""
    if not PAST_APPLICATIONS.exists():
        return
    text = PAST_APPLICATIONS.read_text(encoding="utf-8")
    row = f"| {date.today().isoformat()} | {job['company']} | {job['title']} | Submitted |"
    marker = "|---|---|---|---|"
    if marker in text:
        text = text.replace(marker, marker + "\n" + row, 1)
        PAST_APPLICATIONS.write_text(text, encoding="utf-8")


def waiting_questions():
    """Questions under '## Questions waiting for me' in standard-answers.md.

    Format (one block per question):
      ### <question>
      - Asked by: <Company> — <Role> (job: <job_id>)
      - Date: YYYY-MM-DD
      - My answer: <text>        (added from the dashboard; Claude then files it)
    """
    if not STANDARD_ANSWERS.exists():
        return []
    text = STANDARD_ANSWERS.read_text(encoding="utf-8")
    part = text.split("## Questions waiting for me", 1)
    if len(part) < 2:
        return []
    section = re.split(r"\n## ", part[1], maxsplit=1)[0]
    questions = []
    for block in re.split(r"\n### ", "\n" + section)[1:]:
        lines = block.strip().splitlines()
        q = {"question": lines[0].strip(), "asked_by": "", "job_id": "", "date": "", "answer": "", "source": "file"}
        for line in lines[1:]:
            line = line.strip("- ").strip()
            if line.startswith("Asked by:"):
                q["asked_by"] = line[len("Asked by:"):].strip()
                m = re.search(r"\(job: ([\w\-]+)\)", line)
                q["job_id"] = m.group(1) if m else ""
            elif line.startswith("Date:"):
                q["date"] = line[len("Date:"):].strip()
            elif line.startswith("My answer:"):
                q["answer"] = line[len("My answer:"):].strip()
        questions.append(q)
    return questions


def write_answer_to_file(question, answer):
    """Add 'My answer' under the question (in the 'Questions waiting for me' section) in standard-answers.md."""
    text = STANDARD_ANSWERS.read_text(encoding="utf-8")
    answer = " / ".join(line.strip() for line in answer.splitlines() if line.strip())  # keep it on one line
    section = text.find("## Questions waiting for me")
    if section == -1:
        return False
    head = f"### {question}"
    idx = text.find(head + "\n", section)
    if idx == -1:
        idx = text.find(head, section)
        if idx == -1 or not text[idx + len(head):idx + len(head) + 1] in ("", "\n", "\r"):
            return False
    nxt = text.find("\n### ", idx + len(head))
    nxt2 = text.find("\n## ", idx + len(head))
    ends = [e for e in (nxt, nxt2) if e != -1]
    end = min(ends) if ends else len(text)
    block = text[idx:end].rstrip("\n")
    block = re.sub(r"\n- My answer:.*", "", block)
    block += f"\n- My answer: {answer}\n"
    text = text[:idx] + block + text[end:]
    STANDARD_ANSWERS.write_text(text, encoding="utf-8")
    return True


def all_questions(jobs):
    """Questions from the file, plus any stored only on a job."""
    questions = waiting_questions()
    known = {q["question"] for q in questions}
    for job in jobs:
        for q in job.get("waiting_questions", []):
            if q["question"] not in known:
                questions.append({"question": q["question"], "asked_by": f"{job['company']} — {job['title']}",
                                  "job_id": job["id"], "date": q.get("date", ""), "answer": q.get("answer", ""),
                                  "source": "job"})
    return questions


# ---------- view helpers ----------

def enrich(job, settings):
    """Add things computed on the fly: repeat-company flag, tier."""
    job = dict(job)
    flags = list(job.get("flags", []))
    prev = applied_before(job["company"])
    if prev and job.get("status") not in ("submitted", "interview", "offer", "rejected"):
        same = [p for p in prev if norm(p["role"]) == norm(job["title"])]
        if same:
            flags.insert(0, {"type": "danger", "text": "Already applied to this exact role on " + same[0]["date"]})
        else:
            roles = "; ".join(f"{p['role']} ({p['date']})" for p in prev)
            flags.insert(0, {"type": "info", "text": f"You applied to {job['company']} before for a different role: {roles}"})
    drafts = job.get("drafts", {})
    for a in drafts.get("answers", []):
        if a.get("flag"):
            flags.append({"type": "warn", "text": f"Answer to \"{a['question']}\": {a['flag']}"})
    for name, key in (("Resume", "resume_checks"), ("Cover letter", "letter_checks")):
        for c in drafts.get(key, []):
            if c["level"] == "error":
                flags.append({"type": "danger", "text": f"{name}: {c['text']}"})
    for n in drafts.get("review_notes", []):
        flags.append({"type": "warn", "text": n})
    job["source_type"], job["source_label"] = sources.label(job)
    job["score"] = job.get("score") or 0
    if isinstance(job.get("needs_you"), str):
        job["needs_you"] = [job["needs_you"]]
    job["all_flags"] = flags
    job["tier"] = "strong" if job.get("score", 0) >= settings["strong_match_threshold"] else "weaker"
    job["status_label"] = STATUS_LABELS.get(job.get("status"), job.get("status"))
    return job


@app.context_processor
def inject_counts():
    jobs = load_jobs()
    return {
        "nav_counts": {
            "review": sum(1 for j in jobs if j.get("status") in REVIEW_STATUSES),
            "questions": sum(1 for q in all_questions(jobs) if not q["answer"]),
            "queue": sum(1 for q in load_queue() if q["status"] == "pending"),
            "sheet": sum(1 for j in jobs if j.get("status") in ("filled", "needs_you")),
        },
        "settings": load_settings(),
        "user_first_name": first_name(),
        "set_up": setup_done(),
        "STATUS_LABELS": STATUS_LABELS,
        "last_scan": (DATA_DIR / "last_scan.txt").read_text(encoding="utf-8").strip()
                     if (DATA_DIR / "last_scan.txt").exists() else "never",
    }


# ---------- pages ----------

@app.route("/")
def home():
    if not setup_done():
        return render_template("welcome.html")
    settings = load_settings()
    jobs = [enrich(j, settings) for j in load_jobs()]
    source_counts = {}
    for j in jobs:
        if j.get("status") not in ("filtered", "not_eligible", "not_applying", "submitted"):
            source_counts[j["source_type"]] = source_counts.get(j["source_type"], 0) + 1
    chosen = request.args.get("source", "")
    if chosen:
        jobs = [j for j in jobs if j["source_type"] == chosen]
    jobs.sort(key=lambda j: (not j.get("target_company"), -(j.get("score") or 0)))
    review = [j for j in jobs if j.get("status") in REVIEW_STATUSES]
    weaker = [j for j in jobs if j.get("status") == "new"]
    filled = [j for j in jobs if j.get("status") == "filled"]
    filtered = [j for j in jobs if j.get("status") == "filtered"]
    not_eligible = [j for j in jobs if j.get("status") == "not_eligible"]
    attention = []
    for j in jobs:
        if j.get("status") in ("filtered", "not_eligible", "not_applying"):
            continue
        for f in j["all_flags"]:
            # warnings only for jobs you're reviewing; serious problems for any job
            if f["type"] == "danger" or (f["type"] == "warn" and j.get("status") in REVIEW_STATUSES):
                attention.append({"job": j, "flag": f})
    questions = [q for q in all_questions(jobs) if not q["answer"]]
    return render_template("home.html", review=review, weaker=weaker, filled=filled, filtered=filtered, not_eligible=not_eligible,
                           attention=attention, questions=questions, source_counts=source_counts,
                           source_labels=sources.LABELS, chosen_source=chosen)


@app.route("/job/<job_id>")
def job_page(job_id):
    settings = load_settings()
    job = enrich(load_job(job_id), settings)
    folder = JOBS_DIR / job_id
    cover = folder / "cover-letter.txt"
    job["cover_text"] = cover.read_text(encoding="utf-8") if cover.exists() else ""
    pending = [q for q in load_queue() if q["job_id"] == job_id and q["status"] == "pending"]
    return render_template("job.html", job=job, pending=pending)


@app.post("/job/<job_id>/action")
def job_action(job_id):
    job = load_job(job_id)
    action = request.form.get("action")
    if action == "approve":
        job["status"] = "approved"
        job["approved_on"] = now()
        log(job, "Approved by you")
        add_to_queue("fill_application", job_id, "Fill in the application on the company website. Stop before Submit.")
    elif action == "reject":
        job["status"] = "not_applying"
        log(job, "You chose not to apply" + (": " + request.form["note"] if request.form.get("note") else ""))
        if load_settings().get("keep_means_apply"):
            add_to_queue("cull", job_id, "You chose not to apply: remove this job (removed-jobs list + Recycle Bin/Trash).")
    elif action == "draft_anyway":
        job["status"] = "drafting"
        log(job, "You asked to draft it now")
        add_to_queue("draft", job_id, "Draft resume, cover letter and answers.")
    elif action == "request_changes":
        text = request.form.get("text", "").strip()
        if text:
            job["status"] = "changes_requested"
            job.setdefault("change_requests", []).append({"date": now(), "text": text})
            log(job, "Changes requested: " + text)
            add_to_queue("change_request", job_id, text)
    elif action == "save_to_rules":
        text = request.form.get("text", "").strip()
        if text:
            log(job, "Asked to save a correction to the rules: " + text)
            add_to_queue("save_to_rules", job_id, text)
    elif action == "submitted":
        job["status"] = "submitted"
        job["submitted_on"] = now()
        d = job.get("drafts", {})
        job["sent_versions"] = {"resume": d.get("resume_pdf", ""), "cover_letter": d.get("cover_letter_pdf", ""),
                                "recorded": now()}
        log(job, "You confirmed you submitted")
        if not job.get("sample"):
            add_past_application(job)
    elif action == "set_status":
        new = request.form.get("status")
        if new in STATUS_LABELS:
            job["status"] = new
            log(job, "Status changed to " + STATUS_LABELS[new])
    elif action == "redo":
        text = request.form.get("text", "").strip()
        if text:
            job.setdefault("change_requests", []).append({"date": now(), "text": text, "redo": True})
            job["redo_pending"] = text
            log(job, "Redo requested: " + text)
            add_to_queue("redo", job_id, text + "\n(Regenerate the file(s), re-run checks, re-upload in this job's Chrome tab; "
                                          "if the tab is gone, refill the application in a new tab.)")
    elif action == "restore":
        job["status"] = "new"
        log(job, "Restored to the list")
    save_job(job)
    return redirect(request.referrer or url_for("job_page", job_id=job_id))


@app.post("/job/<job_id>/save")
def job_save(job_id):
    """Save your own edits to the cover letter and answers."""
    job = load_job(job_id)
    folder = JOBS_DIR / job_id
    if "cover_text" in request.form:
        (folder / "cover-letter.txt").write_text(request.form["cover_text"].replace("\r\n", "\n"), encoding="utf-8")
        log(job, "You edited the cover letter")
        save_job(job)
        try:
            build.build_letter(job_id)  # rebuilds PDF + Word and re-runs the automatic checks
            job = load_job(job_id)
        except Exception as e:  # noqa: BLE001 - show any LaTeX problem as a flag
            job.setdefault("flags", []).append({"type": "danger", "text": f"Couldn't rebuild the cover letter PDF: {e}"})
        add_to_queue("recheck_cover_letter", job_id, "You edited the letter text. Claude re-checks the judgement rules (voice, facts) and learns from your edit.")
    answers = job.get("drafts", {}).get("answers", [])
    for i, a in enumerate(answers):
        key = f"answer_{i}"
        if key in request.form and request.form[key] != a["answer"]:
            a["answer"] = request.form[key].replace("\r\n", "\n")
            a["edited_by_user"] = True
            log(job, f"You edited the answer to: {a['question']}")
    save_job(job)
    return redirect(url_for("job_page", job_id=job_id) + "#drafts")


@app.route("/questions", methods=["GET", "POST"])
def questions_page():
    jobs = load_jobs()
    if request.method == "POST":
        question = request.form["question"]
        answer = request.form["answer"].strip()
        job_id = request.form.get("job_id", "")
        if answer:
            in_file = write_answer_to_file(question, answer)
            if job_id and (JOBS_DIR / job_id / "job.json").exists():
                job = load_job(job_id)
                for q in job.get("waiting_questions", []):
                    if q["question"] == question:
                        q["answer"] = answer
                log(job, f"You answered: {question}")
                save_job(job)
            add_to_queue("file_answer", job_id,
                         f"File the answer in the right section of standard-answers.md"
                         f"{'' if in_file else ' (question was stored on the job only)'}, then use it on the waiting application. "
                         f"Q: {question} A: {answer}")
        return redirect(url_for("questions_page"))
    return render_template("questions.html", questions=all_questions(jobs))


@app.route("/sheet")
def review_sheet():
    """Every application prepared or filled by a run, best scores first."""
    settings = load_settings()
    jobs = [enrich(j, settings) for j in load_jobs() if j.get("status") in SHEET_STATUSES]
    order = {"needs_you": 0, "filled": 1, "filling": 2, "prepared": 3}
    jobs.sort(key=lambda j: (order.get(j["status"], 9), -(j.get("score") or 0)))
    for j in jobs:
        d = j.get("drafts", {})
        j["unsure"] = [a for a in d.get("answers", []) if a.get("flag")]
        # legal declarations and guesses first, so they're checked before anything else
        j["unsure"].sort(key=lambda a: (0 if "legal" in a.get("flag", "").lower() else 1 if "guessed" in a.get("flag", "").lower() else 2))
    last_run = (DATA_DIR / "last_run.txt").read_text(encoding="utf-8").strip() if (DATA_DIR / "last_run.txt").exists() else "never"
    checklist = signin.checklist_data([j for j in load_jobs()])
    return render_template("sheet.html", jobs=jobs, last_run=last_run, checklist=checklist)


@app.route("/tracker")
def tracker():
    settings = load_settings()
    jobs = [enrich(j, settings) for j in load_jobs() if j.get("status") in TRACKER_STATUSES]
    jobs.sort(key=lambda j: j.get("submitted_on") or j.get("approved_on") or "", reverse=True)
    tracked = {(norm(j["company"]), norm(j["title"])) for j in jobs}
    past = [p for p in past_applications() if (norm(p["company"]), norm(p["role"])) not in tracked]
    return render_template("tracker.html", jobs=jobs, past=past, statuses=TRACKER_STATUSES)


@app.route("/add", methods=["GET", "POST"])
def add_job():
    if request.method == "POST":
        link = request.form.get("link", "").strip()
        desc = request.form.get("description", "").strip()
        company = request.form.get("company", "").strip()
        title = request.form.get("title", "").strip()
        if link or desc or company:
            add_to_queue("add_job", "", f"Company: {company}\nTitle: {title}\nLink: {link}\n\nDescription:\n{desc}".strip())
            return render_template("add.html", added=True)
    return render_template("add.html", added=False)


@app.route("/queue")
def queue_page():
    queue = sorted(load_queue(), key=lambda q: (q["status"] != "pending", q["created"]), reverse=False)
    names = {j["id"]: f"{j['company']} — {j['title']}" for j in load_jobs()}
    return render_template("queue.html", queue=queue, names=names)


@app.route("/files/<job_id>/<path:filename>")
def job_file(job_id, filename):
    if not re.fullmatch(r"[\w\-]+", job_id) or ".." in filename:
        abort(404)
    if job_id == "_master":
        return send_from_directory(ME / "samples", filename)
    return send_from_directory(JOBS_DIR / job_id, filename)


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5050
    app.run(host="127.0.0.1", port=port, debug=False)
