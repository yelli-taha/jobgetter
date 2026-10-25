"""Shared helpers: where things live, and the user's profile, checks and settings.

Everything personal lives in me/ (created by the setup interview in SETUP.md):
  me/profile.json   name, contact details, file-name prefix, letter format
  me/checks.json    rules the document builder enforces mechanically (banned phrases, allowed skills, ...)
  settings.json     platform settings (thresholds, locations, phone topic, blocked sites)
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ME = ROOT / "me"
DATA = ROOT / "data"
JOBS = ROOT / "jobs"
SETTINGS_FILE = ROOT / "settings.json"
PROFILE_FILE = ME / "profile.json"
CHECKS_FILE = ME / "checks.json"

DEFAULT_SETTINGS = {
    "home_country": "",
    "location_keywords": [],
    "top_job_threshold": 60,
    "strong_match_threshold": 75,
    "max_fills_per_run": 10,
    "sweep_per_run": 15,
    "discovery_roles": [],
    "discovery_places": [],
    "discovery_sectors": [],
    "discovery_searches_per_run": 4,
    "discovery_companies_per_run": 8,
    "discovery_recheck_days": 30,
    "ntfy_topic": "",
    "auto_submit": False,
    "keep_means_apply": True,
    "blocked_sites": ["linkedin.com", "indeed.com", "glassdoor.com", "wuzzuf.net", "bayt.com", "naukri.com"],
}

DEFAULT_PROFILE = {
    "name": "", "email": "", "phone": "", "linkedin": "", "website": "",
    "file_prefix": "",
    "paper": "a4paper",
    "letter": {"salutation": "Dear Hiring Manager,", "signoff": "Sincerely,",
               "min_words": 250, "max_words": 500, "max_pages": 1},
    "resume": {"max_pages": 1, "always_keep": []},
}

DEFAULT_CHECKS = {
    "letter_banned_phrases": [],
    "letter_banned_patterns": {},
    "resume_banned_patterns": {},
    "never_together": [],
    "no_em_dashes": True,
    "no_paragraph_headers": True,
    "skills_left": [],
    "skills_right_default": [],
    "skills_right_stockpile": [],
    "skills_right_rejected": [],
    "skills_right_count": [],
    "max_skill_chars": 0,
}


def read_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def merged(defaults, found):
    out = json.loads(json.dumps(defaults))
    for k, v in (found or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k].update(v)
        else:
            out[k] = v
    return out


def settings():
    return merged(DEFAULT_SETTINGS, read_json(SETTINGS_FILE, {}))


def profile():
    p = merged(DEFAULT_PROFILE, read_json(PROFILE_FILE, {}))
    if not p["file_prefix"] and p["name"]:
        p["file_prefix"] = re.sub(r"[^A-Za-z0-9]+", "_", p["name"]).strip("_")
    return p


def checks():
    return merged(DEFAULT_CHECKS, read_json(CHECKS_FILE, {}))


def first_name():
    name = profile()["name"].strip()
    return name.split()[0] if name else "you"


def blocked(url):
    """True for sites Claude must never open or automate (LinkedIn and other job boards)."""
    u = (url or "").lower()
    return any(b.lower() in u for b in settings()["blocked_sites"])


def setup_done():
    """Setup is finished only when SETUP.md's last step sets profile.json "setup_complete": true."""
    return bool(read_json(PROFILE_FILE, {}).get("setup_complete"))


COMPANY_NOISE = {"inc", "ltd", "llc", "corp", "corporation", "group", "company", "the", "co", "plc", "gmbh", "sa",
                 "sae", "limited", "holding", "holdings"}


def norm_company(name):
    """'Acme Ltd (Paris)' ~ 'acme'. Used to match past applications and duplicates."""
    name = re.sub(r"\(.*?\)", "", (name or "").lower())
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    return " ".join(w for w in name.split() if w not in COMPANY_NOISE | place_noise())


def place_noise():
    """Words that don't help tell two locations apart ('Lyon' vs 'Lyon, France')."""
    words = {"governorate", "province", "state", "county", "region", "district", "city", "metro", "area", "greater"}
    country = settings().get("home_country", "")
    words |= set(re.sub(r"[^a-z0-9 ]", " ", country.lower()).split())
    return words
