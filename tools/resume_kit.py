"""Build a tailored resume.tex from the master (content changes only; layout untouched).

The master (me/samples/master-resume.tex) marks every experience entry with a comment line:
    % JOB: <key>          e.g.  % JOB: acme
followed by its \\resumeSubheading ... \\resumeItemListStart ... \\resumeItemListEnd block.
An optional two-cell Skills table (left cell items joined by $\\cdot$, right cell items by \\newline) can be refilled.

Used by Claude when drafting:
    import sys; sys.path.insert(0, "tools"); from resume_kit import make_resume, fit, entry_keys, old_bullets
    tex = make_resume(jobs=[("acme", [bullets...]), ("beta", None)], left=[...], right=[...], extra=None)

- jobs: (key, bullets) in the order they should appear (keep date order, newest first). bullets are
        LaTeX-escaped text; None keeps the master's bullets. Leave a key out to drop that job.
- left / right: new contents of the Skills table cells (plain text, '&' and '%' escaped here). None = keep master.
- extra: optional (section_title, [bullets]) added after the experience section (e.g. "Academic Projects").
- fit(job_id, ...): write + compile with tools/build.py, trimming until it fits the page limit.
- old_bullets(tex): {key: [bullets]} from an older tailored resume, to rebuild it on a changed master.
"""
import json
import re
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.common import JOBS, ME, profile  # noqa: E402

MASTER = ME / "samples" / "master-resume.tex"
ENTRY = r"^([ \t]*% JOB: {key}[ \t]*\n)(.*?\\resumeItemListStart\n)(.*?)([ \t]*\\resumeItemListEnd\n)"


def esc(s):
    return s.replace("&", r"\&").replace("%", r"\%")


def master_text():
    return MASTER.read_text(encoding="utf-8")


def entry_keys(tex=None):
    """Experience keys in the order they appear in the master."""
    return re.findall(r"^\s*% JOB: ([\w\-]+)\s*$", tex or master_text(), flags=re.M)


def _entries(tex):
    out = {}
    for key in entry_keys(tex):
        m = re.search(ENTRY.format(key=re.escape(key)), tex, flags=re.S | re.M)
        if m:
            out[key] = (m.group(2), m.group(3), m.group(4), m.start(), m.end())
    return out


def old_bullets(tex):
    out = {}
    for key, (_, body, _, _, _) in _entries(tex).items():
        out[key] = re.findall(r"\\resumeItem\{(.*)\}\s*$", body, flags=re.M)
    return out


def make_resume(jobs, left=None, right=None, extra=None):
    tex = master_text()
    rows = re.search(r"\\\\\[1pt\]\n(.*?)\n&\n(.*?)\\\\\n\\end\{tabularx\}", tex, flags=re.S)
    if rows and (left is not None or right is not None):
        l_txt = r" $\cdot$ ".join(esc(t) for t in left) if left is not None else rows.group(1)
        r_txt = (r" \newline ".join(esc(c) for c in right) + " ") if right is not None else rows.group(2)
        tex = tex[:rows.start(1)] + l_txt + tex[rows.end(1):rows.start(2)] + r_txt + tex[rows.end(2):]
    entries = _entries(tex)
    if not entries:
        raise ValueError("No '% JOB: <key>' markers found in the master resume")
    first = min(e[3] for e in entries.values())
    last = max(e[4] for e in entries.values())
    parts = []
    for key, bullets in jobs:
        head, body, end, _, _ = entries[key]
        if bullets is not None:
            body = "".join(f"      \\resumeItem{{{b}}}\n" for b in bullets)
        parts.append(f"  % JOB: {key}\n{head}{body}{end}")
    tex = tex[:first] + "\n".join(parts) + tex[last:]
    if extra:
        title, bullets = extra
        add = (f"\n%-----------{title.upper()}-----------\n\\section{{{esc(title)}}}\n"
               "\\resumeSubHeadingListStart\n\\item\n\\resumeItemListStart\n"
               + "".join(f"  \\resumeItem{{{b}}}\n" for b in bullets)
               + "\\resumeItemListEnd\n\\resumeSubHeadingListEnd\n")
        tex = tex.replace(r"\end{document}", add + "\n\\end{document}")
    return tex


def fit(job_id, jobs, left=None, right=None, extra=None, cut_order=(), why_cut=""):
    """Write + compile; trim until it fits. Returns (checks, trimmed list).

    There is no fixed ranking of experiences: cut_order lists keys from LEAST to most relevant for THIS
    job ("extra" = the extra section). Bullets are cut from the end of each list, so order bullets most
    relevant first. Keys in me/profile.json resume.always_keep are never dropped and keep 2 bullets.
    """
    from tools import build
    keep = set(profile()["resume"].get("always_keep", []))
    folder = JOBS / job_id
    jobs = [(k, list(b) if b is not None else old_bullets(master_text()).get(k, [])) for k, b in jobs]
    extra = (extra[0], list(extra[1])) if extra else None
    trimmed = []
    reason = f" ({why_cut})" if why_cut else " (least relevant to this posting)"
    for _ in range(25):
        (folder / "resume.tex").write_text(make_resume(jobs, left, right, extra), encoding="utf-8")
        checks = build.build_resume(job_id)
        if not any(c["text"].startswith("Length:") and c["level"] == "error" for c in checks):
            return checks, trimmed
        cut = False
        for key in cut_order:
            if key == "extra":
                if extra and extra[1]:
                    trimmed.append(f"Cut from {extra[0]}: \"{extra[1].pop()[:70]}...\"{reason}")
                    if not extra[1]:
                        extra = None
                    cut = True
                    break
                continue
            idx = next((i for i, (k, _) in enumerate(jobs) if k == key), None)
            if idx is None:
                continue
            bullets = jobs[idx][1]
            floor = 2 if key in keep else 1
            if len(bullets) > floor:
                trimmed.append(f"Cut from {key}: \"{bullets.pop()[:70]}...\"{reason}")
                cut = True
                break
            if key not in keep:
                jobs.pop(idx)
                trimmed.append(f"Dropped {key} entirely{reason}")
                cut = True
                break
        if not cut:
            return checks, trimmed
    return checks, trimmed


def rebuild(job_id, left=None, right=None, changes=None, cut_order=()):
    """Re-tailor a job's resume on the CURRENT master, keeping its tailored bullets (use after the master changes)."""
    folder = JOBS / job_id
    old = (folder / "resume.tex").read_text(encoding="utf-8")
    shutil.copy(folder / "resume.tex", folder / f"resume-before-{date.today()}.tex")
    ob = old_bullets(old)
    jobs = [(k, ob[k]) for k in entry_keys(old) if k in ob and k in entry_keys()]
    checks, trimmed = fit(job_id, jobs, left, right, cut_order=cut_order)
    p = folder / "job.json"
    j = json.loads(p.read_text(encoding="utf-8"))
    d = j.setdefault("drafts", {})
    d["resume_changes"] = ["Rebuilt on the current master resume."] + (changes or []) + trimmed
    j.setdefault("history", []).append({"date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                        "event": "Resume rebuilt on the current master." + (" Trimmed: " + "; ".join(trimmed) if trimmed else "")})
    p.write_text(json.dumps(j, indent=2, ensure_ascii=False), encoding="utf-8")
    return checks, trimmed
