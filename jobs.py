"""Add scored jobs to the dashboard.

Usage (PY = .venv\\Scripts\\python.exe on Windows, .venv/bin/python on Mac):
  PY tools/jobs.py add <file.json>
      <file.json> holds a list of jobs (written by Claude after scoring). Fields:
        title, company, location, work_setup, employment_type, source, original_url,
        apply_url, posting_text, score, score_reason, target_company, flags, status
      status: "drafting" (Claude drafts next), "new" (kept, drafted after the top jobs),
              "filtered" (breaks a hard limit; score_reason says which), "not_eligible"
      Skips duplicates (same company + title + place already in jobs/ or in data/removed-jobs.json)
      and exact roles already in past-applications.md. Marks each apply_url / original_url as seen.
  PY tools/jobs.py seen <id-or-url> ...
      Mark Gmail thread ids or URLs as processed so they aren't read again.
  PY tools/jobs.py is-seen <id-or-url> ...
      Print which of these are already processed.
  PY tools/jobs.py remove <job_id> "<reason>"
      Cull a job: record it in data/removed-jobs.json (so it never comes back), then move its
      folder to the Recycle Bin / Trash (recoverable), never a permanent delete.
"""
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.feeds import SEEN, mark_seen, norm  # noqa: E402
from tools.common import norm_company, place_noise  # noqa: E402
from tools.sources import classify  # noqa: E402

JOBS = ROOT / "jobs"
PAST = ROOT / "me" / "target-companies" / "past-applications.md"
REMOVED = ROOT / "data" / "removed-jobs.json"  # [{company, title, location, reason, date}] so deleted jobs never come back


def past_roles():
    rows = []
    if not PAST.exists():
        return rows
    for line in PAST.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 4 and re.match(r"\d{4}-\d{2}-\d{2}", cells[0]):
            rows.append((norm_company(cells[1]), norm(cells[2])))
    return rows


def add(path):
    incoming = json.loads(Path(path).read_text(encoding="utf-8"))
    def same_place(a, b):
        """'Lyon' vs 'Lyon, France' is the same place; 'Lyon' vs 'Paris' is not."""
        noise = place_noise()
        a, b = set(norm(a).split()) - noise, set(norm(b).split()) - noise
        return not a or not b or a <= b or b <= a

    existing = [json.loads(f.read_text(encoding="utf-8")) for f in JOBS.glob("*/job.json")]
    existing += json.loads(REMOVED.read_text(encoding="utf-8")) if REMOVED.exists() else []  # jobs deleted as no match
    seen_jobs = [(norm(j["company"]), norm(j["title"]), j.get("location", "")) for j in existing]

    def is_dup(job):
        c, t = norm(job["company"]), norm(job["title"])
        return any(c == c2 and t == t2 and same_place(job.get("location", ""), loc2) for c2, t2, loc2 in seen_jobs)

    past = past_roles()
    added, skipped = [], []
    for job in incoming:
        if is_dup(job):
            skipped.append(f"{job['company']}: {job['title']} (already in the dashboard)")
            continue
        if any(c and c == norm_company(job["company"]) and r == norm(job["title"]) for c, r in past):
            skipped.append(f"{job['company']}: {job['title']} (already applied)")
            continue
        job_id = f"{date.today().isoformat()}_{re.sub(r'[^A-Za-z0-9]+', '-', job['company'])[:30]}_{re.sub(r'[^A-Za-z0-9]+', '-', job['title'])[:40]}".strip("-")
        while (JOBS / job_id).exists():  # same title elsewhere: give it its own folder
            job_id += "-2"
        job.update({"id": job_id, "date_found": job.get("date_found") or date.today().isoformat()})
        job.setdefault("source_type", classify(job.get("source")))
        job.setdefault("flags", [])
        job.setdefault("drafts", {})
        job.setdefault("history", []).append({"date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                              "event": f"Found via {job.get('source', 'unknown')}"})
        (JOBS / job_id).mkdir(parents=True, exist_ok=True)
        (JOBS / job_id / "job.json").write_text(json.dumps(job, indent=2, ensure_ascii=False), encoding="utf-8")
        seen_jobs.append((norm(job["company"]), norm(job["title"]), job.get("location", "")))
        added.append(f"{job_id} [{job.get('status')}, {job.get('score')}]")
    mark_seen([u for j in incoming for u in (j.get("apply_url"), j.get("original_url")) if u])
    print(f"Added {len(added)}:")
    for a in added:
        print("  " + a)
    if skipped:
        print(f"Skipped {len(skipped)}:")
        for s in skipped:
            print("  " + s)


def recycle(folder):
    """Move a folder to the Recycle Bin (Windows) or Trash (Mac). Returns True if it worked."""
    import subprocess
    folder = Path(folder).resolve()
    if sys.platform == "win32":
        ps = ("Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteDirectory("
              f"'{folder}', 'OnlyErrorDialogs', 'SendToRecycleBin')")
        return subprocess.run(["powershell", "-NoProfile", "-Command", ps]).returncode == 0
    trash = Path.home() / (".Trash" if sys.platform == "darwin" else ".local/share/Trash/files")
    trash.mkdir(parents=True, exist_ok=True)
    target = trash / folder.name
    if target.exists():
        target = trash / f"{folder.name}-{datetime.now():%H%M%S}"
    import shutil
    shutil.move(str(folder), str(target))
    return True


def remove(job_id, reason):
    path = JOBS / job_id / "job.json"
    if not path.exists():
        sys.exit(f"No job {job_id}")
    job = json.loads(path.read_text(encoding="utf-8"))
    removed = json.loads(REMOVED.read_text(encoding="utf-8")) if REMOVED.exists() else []
    removed.append({"id": job_id, "company": job["company"], "title": job["title"], "location": job.get("location", ""),
                    "reason": reason, "date": date.today().isoformat()})
    REMOVED.write_text(json.dumps(removed, indent=1, ensure_ascii=False), encoding="utf-8")
    print("removed (in the Recycle Bin / Trash)" if recycle(JOBS / job_id) else "recorded, but couldn't move the folder")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "add":
        add(sys.argv[2])
    elif len(sys.argv) >= 3 and sys.argv[1] == "seen":
        mark_seen(sys.argv[2:])
        print("marked")
    elif len(sys.argv) >= 3 and sys.argv[1] == "is-seen":
        seen = set(json.loads(SEEN.read_text(encoding="utf-8"))) if SEEN.exists() else set()
        for x in sys.argv[2:]:
            print(x, "SEEN" if x in seen else "new")
    elif len(sys.argv) == 4 and sys.argv[1] == "remove":
        remove(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
