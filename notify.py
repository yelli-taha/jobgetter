"""Send a phone notification through ntfy (https://ntfy.sh).

Usage (PY = .venv\\Scripts\\python.exe on Windows, .venv/bin/python on Mac):
  PY tools/notify.py "<message>"
  PY tools/notify.py test

Only counts and generic words. Never put names, companies, roles or any personal details
in the message: ntfy.sh is a public relay, and the random topic name in settings.json is
the only thing keeping it private.
"""
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.common import profile, settings  # noqa: E402


def looks_personal(message):
    if re.search(r"@|\+?\d[\d\s-]{8,}\d", message):
        return True
    words = [w for w in re.split(r"\W+", profile()["name"].lower()) if len(w) >= 3]
    return any(re.search(rf"\b{re.escape(w)}\b", message.lower()) for w in words)


def send(message, title="JobGetter"):
    topic = settings().get("ntfy_topic")
    if not topic:
        sys.exit("No ntfy_topic in settings.json (phone notifications are off)")
    if looks_personal(message):
        sys.exit("Refused: message looks like it contains personal details")
    req = urllib.request.Request(f"https://ntfy.sh/{topic}", data=message.encode("utf-8"), method="POST",
                                 headers={"Title": title, "Tags": "briefcase"})
    with urllib.request.urlopen(req, timeout=15) as r:
        print("sent" if r.status == 200 else f"failed: {r.status}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    send("Test: JobGetter notifications work." if sys.argv[1] == "test" else sys.argv[1])
