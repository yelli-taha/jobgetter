"""Where a job came from: one standard type + a readable label.

Types (set `source_type` on every job; `source` keeps the detail):
  alert_linkedin, alert_wuzzuf, alert_bayt, alert_other  job alert emails
  link_added        a link/description the user added
  sweep             target company careers-page sweep      (source: "Target company sweep: <Company>")
  browsing          extra job found on a filtered careers list (source: "Found while browsing <Company> careers page")
  feed              public job feed (Greenhouse, Lever, Ashby, SmartRecruiters, Workable)
  web_search        broad web search
  sample            made-up sample job
"""
import re

LABELS = {
    "alert_linkedin": "LinkedIn job alert",
    "alert_wuzzuf": "Wuzzuf job alert",
    "alert_bayt": "Bayt job alert",
    "alert_other": "Job alert email",
    "link_added": "Link you added",
    "sweep": "Target company sweep",
    "browsing": "Found while browsing",
    "feed": "Company job feed",
    "web_search": "Web search",
    "sample": "Sample",
}


def classify(source):
    s = (source or "").lower()
    if "sample" in s:
        return "sample"
    if "found while browsing" in s:
        return "browsing"
    if "sweep" in s:
        return "sweep"
    if "you added" in s or "manual" in s or "add a job" in s:
        return "link_added"
    if "linkedin" in s:
        return "alert_linkedin"
    if "wuzzuf" in s:
        return "alert_wuzzuf"
    if "bayt" in s:
        return "alert_bayt"
    if "alert" in s:
        return "alert_other"
    if re.search(r"\bfeed\b", s):
        return "feed"
    if "search" in s:
        return "web_search"
    return "web_search"


def label(job):
    t = job.get("source_type") or classify(job.get("source"))
    src = job.get("source", "")
    if t in ("sweep", "browsing"):
        return t, src  # already reads "Target company sweep: X" / "Found while browsing X careers page"
    if t == "feed":
        m = re.match(r"(\w+) feed", src, re.I)
        return t, f"Company job feed ({m.group(1).title()})" if m else LABELS["feed"]
    return t, LABELS.get(t, t.replace("_", " ").capitalize())
