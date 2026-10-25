# Morning run

The scheduled task "JobGetter: morning run" sends: "Read MORNING-RUN.md in the project folder and follow it."
The user can also start it any time by typing "run the morning run".

This run usually happens with nobody watching. So: don't ask questions and don't wait for answers. Take the
most sensible reading, note it in the summary, and carry on. All Safety rules in CLAUDE.md apply. In an
unattended run, do NOT type anything into application forms (that's Part 2, only when the user asks), and do
NOT use "Sign in with Google" unless the user OK'd it in this same session.

## 0. Once a day
Read data/last_scan.txt. If it already has today's date and the user didn't start this run themselves, stop:
nothing to do. Otherwise read CLAUDE.md, me/my-rules.md, PROGRESS.md and me/search-criteria/search-criteria.md.

Location: if the user named a place ("morning run for Lyon"), the whole run covers ONLY that place (CLAUDE.md
"Run location"): add `--place "Lyon"` to the feeds and discover commands below and use that place's rules.
Otherwise it covers their normal area.

## 1. Collect
1. Feeds: `PY tools/feeds.py scan` -> data/candidates.json (public Greenhouse/Lever/Ashby/SmartRecruiters/
   Workable feeds, filtered by settings.json location_keywords; jobs removed earlier never come back).
2. Gmail: search recent job-alert emails, e.g. `newer_than:2d (job OR jobs OR hiring OR vacancy OR "job alert")`
   (widen to the days since data/last_scan.txt if runs were missed). Skip thread ids `PY tools/jobs.py is-seen`
   already knows. From each alert take title, company and location of postings in the user's area. Mark threads
   done with `PY tools/jobs.py seen <threadId> ...`. Never open the links inside alerts from blocked sites.
3. For each alert job: web search for the same posting on the company's OWN site (exclude the blocked sites).
   Found -> use its text and apply link (and `PY tools/feeds.py discover "<Company>"` if it may have a feed).
   Not found anywhere but the job board -> cull it (keep = apply).
4. Discovery: `PY tools/discover.py plan`, run its searches, add new companies to the memory, investigate up to
   discovery_companies_per_run companies and record each one (CLAUDE.md "Discovering companies").

## 2. Score and add
Score every job against me/ (CLAUDE.md "Collecting and scoring"). Write them as a list in a JSON file and run
`PY tools/jobs.py add <file>`. It skips duplicates, removed jobs and past applications. Then cull what isn't worth
applying to (`PY tools/jobs.py remove <id> "<reason>"`) when keep_means_apply is on.

## 3. Prepare
Part 1 PREPARE from CLAUDE.md for top jobs, up to max_fills_per_run: draft, build, self-check, read the
application form (read only), check sign-in. Then work down the `new` jobs if there's room.

## 4. Queue and records
- Process data/queue.json (every `pending` item).
- Check "## Questions waiting for me" for answers from the dashboard and file them.
- Write today's date + a one-line result to data/last_scan.txt and data/last_run.txt
  (e.g. "2026-10-21 07:05: 12 new jobs, 5 prepared, 2 need you, 3 culled").
- Update PROGRESS.md.

## 5. Tell the user
- Phone (counts only): `PY tools/notify.py "<P> applications prepared, <N> need you, <S> sites need sign-in. Open Claude and type: fill all ready"`
  (<S> from `PY tools/signin.py count`). Skip if ntfy_topic is empty.
- Summary message, short and in plain words:
  1. The Sign-in checklist (`PY tools/signin.py checklist`), if anything is on it.
  2. Prepared jobs: company, role, score, one line each.
  3. What needs the user (personal-fact questions as ONE numbered list; answers to check).
  4. What you culled and why (one line each, grouped).
  5. New companies found today (`PY tools/discover.py new-today`), one line each.
  6. Next step: "Type **fill all ready** and I'll fill these in Chrome and stop before Submit."
