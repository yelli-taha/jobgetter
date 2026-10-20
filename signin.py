"""Sign-in checklist: which job sites the user must sign in to (or create an account on), with direct links.

Usage (PY = .venv\\Scripts\\python.exe on Windows, .venv/bin/python on Mac):
  PY tools/signin.py checklist     # markdown checklist (top of Claude's summary)
  PY tools/signin.py count         # "N sites need sign-in" (phone notification text)
  PY tools/signin.py add <key> "<site name>" <sign-in link> [create-account link]
The dashboard's review sheet calls checklist_data().

Sites live in data/sites.json: {key: {"name", "sign_in", "create", "google_needs_you"}}. Links must be the
sign-in / register page itself, not the company homepage. A job waits on a site when its status is
needs_you / prepared / approved and it has `sign_in_first` = that key.
Sites listed in data/accounts.md -> "Sign in"; others -> "Create a new account".
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.common import DATA, JOBS, read_json  # noqa: E402

ACCOUNTS = DATA / "accounts.md"
SITES_FILE = DATA / "sites.json"
WAITING = ("needs_you", "prepared", "approved")
DONE = ("submitted", "interview", "offer", "rejected", "withdrawn", "not_applying")


def sites():
    return read_json(SITES_FILE, {})


def accounts():
    """{key: sign-in method} for sites where the user has an account (table in data/accounts.md)."""
    if not ACCOUNTS.exists():
        return {}
    keys = {}
    for line in ACCOUNTS.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 5 and re.fullmatch(r"[a-z0-9_-]+", cells[0]) and cells[0] != "key":
            keys[cells[0]] = cells[5] if len(cells) > 5 else "Password"
    return keys


def load_jobs():
    return [json.loads(p.read_text(encoding="utf-8")) for p in JOBS.glob("*/job.json")]


def checklist_data(jobs=None):
    jobs = jobs if jobs is not None else load_jobs()
    have, known = accounts(), sites()
    out = {}
    for j in sorted(jobs, key=lambda j: -(j.get("score") or 0)):
        key = j.get("sign_in_first")
        if not key or j.get("status") not in WAITING or j.get("signed_in_ok"):
            continue
        info = known.get(key, {})
        s = out.setdefault(key, {"key": key, "site": info.get("name", key), "jobs": [], "account": key in have})
        s["jobs"].append(f"{j['company']}: {j['title']}")
        link = info.get("sign_in") if s["account"] else (info.get("create") or info.get("sign_in"))
        s.setdefault("link", link or j.get("apply_url"))
        google = have.get(key, "").lower() == "google" and not info.get("google_needs_you")
        s["action"] = ("Sign in with Google (Claude can click it once you OK it this session)" if google
                       else "Sign in" if s["account"] else "Create a new account")
        s["claude"] = google
    email = [{"job": f"{j['company']}: {j['title']}", "note": j.get("email_draft")} for j in jobs
             if j.get("email_draft") and j.get("status") in WAITING]
    manual = []
    pages = read_json(DATA / "careers-pages.json", [])
    for p in pages if isinstance(pages, list) else pages.get("companies", []):
        if p.get("last_failed") and p.get("manual_url"):
            manual.append({"company": p["company"], "link": p["manual_url"], "why": p["last_failed"]})
    old = [{"job": f"{j['company']}: {j['title']}", "note": j["old_files"]} for j in jobs
           if j.get("old_files") and j.get("status") not in DONE]
    check = [{"job": f"{j['company']}: {j['title']}", "note": j["check_attachment"]} for j in jobs
             if j.get("check_attachment") and j.get("status") not in DONE]
    return {"sites": list(out.values()), "email": email, "manual": manual, "old": old, "check": check}


def markdown(d):
    out = ["## Sign-in checklist"]
    if not d["sites"]:
        out.append("No sign-ins needed right now.")
    for s in d["sites"]:
        out.append(f"- [ ] **{s['site']}**: [{s['action']}]({s['link']}) ({len(s['jobs'])} waiting: {'; '.join(s['jobs'])})")
    if d["email"]:
        out.append("\n**Email applications (Gmail drafts waiting, never sent):**")
        out += [f"- {e['job']}: {e['note']}" for e in d["email"]]
    if d["old"] or d["check"]:
        out.append("\n**Check the attached files:**")
        out += [f"- {o['job']}: {o['note']}" for o in d["old"] + d["check"]]
    if d["manual"]:
        out.append("\n**Couldn't read: please check manually**")
        out += [f"- {m['company']}: [job search]({m['link']})" for m in d["manual"]]
    return "\n".join(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["checklist"]:
        print(markdown(checklist_data()))
    elif a == ["count"]:
        n = len(checklist_data()["sites"])
        print(f"{n} site{'s' if n != 1 else ''} need{'s' if n == 1 else ''} sign-in")
    elif a[:1] == ["add"] and len(a) in (4, 5):
        all_sites = sites()
        all_sites[a[1]] = {"name": a[2], "sign_in": a[3], "create": a[4] if len(a) == 5 else None}
        SITES_FILE.write_text(json.dumps(all_sites, indent=2, ensure_ascii=False), encoding="utf-8")
        print("saved", a[1])
    else:
        sys.exit(__doc__)
