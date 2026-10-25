# JobGetter

**Your own job-application assistant, run by Claude on your computer.**

Every morning JobGetter finds new jobs that fit you, writes a tailored resume and cover letter for each one,
and fills in the application forms on the companies' websites. It stops right before Submit: you check
everything and click Submit yourself.

You set it up by pasting one message into Claude. Claude installs everything, asks you a few rounds of
questions, and does the rest.

---

## What it does

- **Finds jobs** from your job-alert emails, companies' own careers pages, public job feeds and the web.
  It works for wherever you live: you tell it your city and the kind of work you want, and it finds the
  employers around you. Every morning it also **discovers new companies** (start-ups that just raised money,
  big employers, companies like the ones you applied to) and remembers each one so it never checks the same
  company twice for nothing. Say "morning run for <city>" to search just one other place.
- **Scores every job** out of 100 and explains why, so the best fits come first.
- **Writes a one-page resume and a cover letter for each job.** It works from a master resume it builds with
  you, and uses only true facts about you, in your voice.
- **Fills in the application** in your own Chrome, including the tricky parts: dropdowns, uploads, and
  multi-step forms. When it isn't sure of an answer it fills in its best guess and flags it for you to check.
- **Stops before Submit.** You review each filled tab and submit it yourself.
- **Keeps track** on a simple dashboard on your computer: jobs, drafts, questions, and every application you've
  sent. It can also ping your phone when applications are ready.
- **Learns from you.** Correct something once, say "save this to the rules", and it never makes that mistake again.

## What it never does

- Click Submit for you.
- Type, store or reset your passwords. Chrome's password manager keeps those.
- Create accounts for you, accept terms for you, or get around CAPTCHAs.
- Use LinkedIn or other job boards directly. Their rules ban bots and could get your account blocked. It reads
  their job-alert *emails* and applies on the company's own website instead.
- Share your data. Everything stays on your computer. This repository contains the program only, no personal
  information.

## What you need

- **A paid Claude plan (Pro or Max)** and the **Claude desktop app** ([claude.ai/download](https://claude.ai/download)).
- **Google Chrome** with the **Claude in Chrome** extension (from the Chrome Web Store).
- **Gmail**, connected to Claude, so it can read your job alerts.
- A Windows or Mac computer, and your current resume (PDF or Word).
- About 45 minutes for setup, mostly Claude working.

## Get started

Full click-by-click guide: **[START-HERE.md](START-HERE.md)**. The short version:

1. Make an empty folder called **JobGetter** in your Documents.
2. In the Claude desktop app, open the **Code** tab, start a new session, and choose that folder.
3. Paste this message and press Enter:

```
Set up JobGetter for me. Download https://github.com/yelli-taha/jobgetter/archive/refs/heads/main.zip,
unzip it, and put everything from inside its jobgetter-main folder directly into this folder (no git
needed). Then read SETUP.md and follow it step by step. I'm not technical: do everything you can
yourself and explain anything I have to do in plain words.
```

4. Drag your resume into the chat when Claude asks, and answer its questions.

## Using it every day

| You type | Claude does |
|---|---|
| *(nothing: it runs every morning)* | Finds new jobs, drafts applications, reads the forms, pings your phone |
| **fill all ready** | Fills every prepared application in Chrome and stops before Submit |
| **signed in** | Continues with sites you just signed in to |
| **save this to the rules** | Turns your correction into a permanent rule |
| **update JobGetter** | Gets the newest version without touching your files |

Open the dashboard any time by double-clicking **Start Dashboard** in your JobGetter folder.

## How it works (for the curious)

- `CLAUDE.md`: the standing rules Claude follows. `SETUP.md`: the setup interview. `MORNING-RUN.md`: the daily run.
- `docs/website-playbook.md`: everything learned about getting through real careers sites and application forms.
- `app.py`, `templates/`, `static/`: the dashboard (Python and Flask, runs only on your computer at localhost:5050).
- `tools/`: job feeds, careers-site readers, resume and letter builder (LaTeX), sign-in checklist, phone notifications.
- Your own files are created in `me/`, `jobs/` and `data/`. They're excluded from git and never uploaded.

Made by [yelli-taha](https://github.com/yelli-taha), built with Claude.
