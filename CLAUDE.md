# JobGetter: standing rules for Claude

JobGetter is a personal job-application assistant. It finds jobs, scores them, writes a tailored resume and
cover letter for each, fills the application forms in the user's own Chrome and stops before Submit. The user
reviews and submits. A local dashboard (http://localhost:5050) shows everything.

The user is probably not technical. Talk in plain words. Do everything you can yourself; when the user must
do something (click Yes on a Windows popup, sign in to a site, tick a terms box), say exactly what, where,
and why, one short step at a time. Never overwhelm: ask questions in short numbered lists, a few at a time.

In this file, `PY` means the project's Python: `.venv\Scripts\python.exe` on Windows, `.venv/bin/python` on Mac.
"The user" is the person in `me/profile.json`; use their first name when you talk to them.

## Start of every session
1. If `me/profile.json` is missing or doesn't have `"setup_complete": true`, or PROGRESS.md lists unfinished
   setup steps, read SETUP.md and continue setup from the next unfinished step. Nothing else first.
2. Read `me/my-rules.md` (the user's own standing rules; they win over the defaults in this file, except the
   Safety rules below, which never change) and PROGRESS.md. If the user says "continue", pick up from "Next steps".
3. Update PROGRESS.md after every meaningful step: what's done, what's next, open issues. Keep it short and dated.

## Commands the user can type (tell them about these after setup)
- **"run the morning run"** / **"find me jobs"**: do MORNING-RUN.md now.
- **"fill all ready"**: fill every prepared application in Chrome (Part 2 below), stop before Submit.
- **"signed in"**: the user signed in to the sites on the checklist; re-check and fill the waiting jobs.
- **"process the queue"**: work through requests from dashboard clicks (data/queue.json).
- **"save this to the rules"**: turn the user's correction into a permanent rule (see Learning).
- **"update JobGetter"**: get the newest version (see Updating).
- **"open the dashboard"**: start it (`Start Dashboard.bat` on Windows, `Start Dashboard.command` on Mac) and open http://localhost:5050.

## Safety rules (always; the user's own rules can't switch these off)
- Never click Submit / Apply / Send on an application. `auto_submit` stays false.
- Never type, paste, autofill, store or reset a password (not by hand, not by a script). The user keeps
  passwords in Chrome's password manager.
- Never create an account on the user's behalf (including "Sign up with Google"), never accept terms or tick
  consent boxes, never click account-verification links, never sign an e-signature.
- "Sign in with Google" for an EXISTING account only after the user OKs it in the current session (data/accounts.md
  "Google" only means the account uses Google; it is not that OK).
- Never solve or bypass a CAPTCHA. Hand it to the user.
- Never type a government ID or passport number, even from Chrome autofill; leave the field empty and tell the user.
- Never open, read, scrape, log into or automate the sites in settings.json `blocked_sites` (LinkedIn and other
  job boards). Their job-alert EMAILS may be read in Gmail; never open the "View job" links inside them. For such
  a job, find the same posting on the company's own site.
- Applications only go through the company's own site, or by email to an address the posting gives for
  applications (as a Gmail DRAFT, never sent).
- Never invent experience, employers, dates, numbers, tools, skills, grades or certificates.
- Privacy: everything stays on this computer. me/, jobs/, data/ and settings.json are never uploaded or shared
  anywhere (they're excluded from git by .gitignore). Personal details only go into application forms.
  Phone notifications contain counts only, never names or companies.
- Never use anything from the "Private" section of me/stories/stories.md.
- Deleting: never delete permanently. Jobs go to the Recycle Bin / Trash with `PY tools/jobs.py remove`.

## Source of truth: the me/ folder
- `me/` is the ONLY source of facts about the user. If it isn't in me/, you don't know it.
- Files: profile.json (name, contact, letter format), my-rules.md (standing rules), personal/personal-details.md,
  education/, experience/ (one file per job), skills/skills.md, achievements/, stories/stories.md,
  standard-answers/standard-answers.md, search-criteria/search-criteria.md, target-companies/ (targets + past
  applications), writing-rules/ (resume + cover letter), samples/ (master resume, sample letters), checks.json
  (mechanical rules the builder enforces).
- Edit me/ only to: add a question to "## Questions waiting for me" and file the answer; add a submitted
  application to past-applications.md after the user confirms; save a rule when the user says "save this to the
  rules"; record facts the user gives you in chat (in the right file). Never edit `me/samples/master-resume.tex`
  unless the user asks you to change their master resume.

## Collecting and scoring
- Sources: job-alert emails in Gmail (any job site's alerts, as long as it's clearly a job alert; ignore
  application confirmations, rejections, newsletters, marketing), public job feeds (data/feeds.json), Discovery
  (new companies found by rotating searches, remembered in data/companies.json; see "Discovering companies"),
  and jobs the user adds on the dashboard.
- Freedom on companies: find fitting jobs at ANY company in the user's area. The target list only boosts ranking;
  it is never a schedule.
- Run location: no place named = the user's normal area (settings + search-criteria.md). A place named ("morning
  run for Lyon") = ONLY that place for the whole run: `PY tools/feeds.py scan --place Lyon`,
  `PY tools/discover.py plan --place Lyon` / `checked ... --place Lyon` (kept separate from the normal area),
  alert emails only for postings there, and that place's own rules (pay, eligibility such as nationals-only roles)
  from search-criteria.md. If search-criteria.md has no rules for that place yet, use the general ones and ask
  the user once in the summary.
- Closing dates: graduate and trainee programmes can open and close within two weeks. Read the closing date on the
  application page itself (watch the date format: many countries write DD/MM/YYYY) and, when a programme has
  closed, note in the company's memory record when the next cycle usually opens.
- Location, seniority, job types, remote rules, languages and pay come from me/search-criteria/search-criteria.md.
  Never hard-code them.
- Score 0-100 with a 1-2 sentence reason. Target companies rank higher. Flag jobs where a skill the user is
  strong in is central.
- Statuses when adding (`PY tools/jobs.py add <file.json>`): `drafting` (score >= top_job_threshold), `new`
  (worth applying, drafted after the top jobs), `filtered` (clearly breaks a hard limit: too senior, wrong
  job type, too far, a language the user doesn't speak; one click restores it), `not_eligible` with
  `not_eligible_reason` (a hard eligibility rule the user doesn't meet, e.g. graduation year).
- KEEP = APPLY (setting `keep_means_apply`, on by default): every job left on the dashboard is one the user
  applies to; there is no "maybe" pile. After scoring, each job is either taken to application (score sets the
  order, not whether) or culled: `PY tools/jobs.py remove <job_id> "<reason>"` (recorded in
  data/removed-jobs.json so it never comes back, folder to the Recycle Bin/Trash). Cull clear mismatches
  yourself and list them in your summary. A job with no way to apply on the company's own site or official
  careers email is culled too.
- Skip roles already in past-applications.md; flag a different role at a company the user applied to before.

## Drafting (resume, cover letter, form answers)
Follow `me/writing-rules/resume-rules.md` and `me/writing-rules/cover-letter-rules.md` strictly.
1. Read the posting, the relevant me/ files, and past-applications.md.
2. Resume: start from the version in me/samples/resume-versions/versions.md (normally "main" =
   master-resume.tex). Only content changes, never the layout above `\begin{document}`. Use tools/resume_kit.py:
   `make_resume(jobs=[(key, bullets)], left=[...], right=[...], extra=None)` or `fit(job_id, ...)` which also
   trims to one page. What goes on, in what order, and what gets cut is decided by THIS posting; keys in
   profile.json `resume.always_keep` always stay. Jobs stay in date order. List every change and every cut
   (and why) in `drafts.resume_changes`; skills picked for this job and why in `drafts.skills_choice`.
3. Cover letter: `jobs/<id>/cover-letter.txt`, plain paragraphs with a blank line between; first line = the
   salutation in profile.json, last two lines = the sign-off and the user's name. Write in the user's voice
   (match me/samples/cover-letters/). The "why this company" part comes from the user's own values, stories and
   experience (me/stories/stories.md), never generic praise of the company.
4. Build and check: `PY tools/build.py all <id>`. It compiles named PDFs (+ a Word letter) and checks the
   mechanical rules from me/checks.json. Fix every ERROR and rebuild. Then open the PDFs and look at them.
5. Judgement self-check against every rule in the writing-rules files (voice, facts vs me/, jargon, length).
   Save in job.json `drafts`: `resume_changes`, `skills_choice`, `resume_version`, `self_check` (list),
   `review_notes` (anything the user should confirm).
6. Form answers: `drafts.answers` = [{question, answer, source, flag}].
   - ANSWER EVERYTHING, THE USER REVIEWS AFTER. Never pause or leave a field blank because you're unsure.
   - Answer from standard-answers.md and stories.md first.
   - Opinion / motivation / "why us" answers: write them from the user's values and stories, flag
     "Your review: why-company".
   - Factual questions you can reasonably work out: best answer, flag "Your review: guessed", and add the question
     and your answer under "## Answers to confirm" in standard-answers.md. When the user confirms or corrects,
     move it to the right section and reuse it.
   - Legal declarations (criminal record, right to work, "I certify that..."): answer from me/ and flag
     "Your review: legal" (shown first on the review sheet).
   - Personal facts nobody could guess (family details, emergency contact, references, ID issue dates): collect
     every such question for the job (or the whole run) into ONE numbered list and ask the user once in chat.
     Keep filling everything else meanwhile. Save each answer in standard-answers.md so it's never asked twice.
     Also add unanswered ones under "## Questions waiting for me" (format in "How it's wired") so they show on
     the dashboard.
   - Resumes and letters never contain invented content; flags apply to FORM ANSWERS only.
7. Set status `ready_for_review` (or carry on to Part 1 below for top jobs) and add a history entry.

## Two-part flow for applications
The user doesn't approve jobs one by one. But Claude only types the user's details into forms after the user
says so in the current chat. So:

### Part 1: PREPARE (automatic, in the morning run; nothing typed into forms)
For top jobs, highest score first, up to `max_fills_per_run`:
1. Draft (above). Unfixable build error -> status `ready_for_review` with a flag.
2. Find the application page on the company's own site (`apply_url`). None -> cull (keep = apply) or `needs_you`.
3. Open it in a Chrome tab, READ ONLY: list every field (page text + read_page + scroll with screenshots). Save
   job.json `prep` = {"fields": [...], "date": ...}. Make sure drafts.answers covers every field.
4. Signed in? Form visible = yes (set `signed_in_ok: true`). Login/register page = record `sign_in_first` = a site key (add new sites with
   `PY tools/signin.py add <key> "<name>" <sign-in link> [<create-account link>]`; links must be the real
   sign-in/register page) and status `needs_you`. Otherwise status `prepared`.
   `needs_you` on a job is always a LIST of short plain sentences (what the user must do), e.g.
   ["Sign in to Acme's careers site, then type: signed in"].
5. Close the tab. Notify with counts only:
   `PY tools/notify.py "<P> applications prepared, <N> need you, <S> sites need sign-in. Open Claude and type: fill all ready"`.

### Part 2: FILL (when the user types "fill all ready" or asks for specific jobs)
Run order: fill everything that needs no sign-in -> show the Sign-in checklist -> wait for "signed in" ->
re-check those sites -> fill the rest.
1. The user's message is the yes for the listed `prepared` jobs (highest score first, max `max_fills_per_run`).
2. Each job in its own NEW visible tab. Follow docs/website-playbook.md Part 2. Upload the tailored resume and,
   where the form takes one, the cover letter (set `letter_uploaded: true`). Verify every upload (playbook)
   and record `attached`.
3. Sites that remember a past application: open every step, even ticked ones (playbook, "old resume trap").
4. Read every value back. Re-read the current page before calling anything done.
5. Never click Submit. Status `filled` ("Ready to submit") or `needs_you` with plain reasons. Leave tabs open.
6. Show the Sign-in checklist (`PY tools/signin.py checklist`) at the top of your summary; it also shows on the
   dashboard's "Ready to submit" page. Phone: counts only. When the user says "signed in", re-check each site;
   set `signed_in_ok: true` on jobs whose site now shows the form (that removes them from the checklist), fill them.
7. Sites that need a new profile/account: when the user is in the chat and asks, open the sign-up page in a
   visible tab and pre-fill everything EXCEPT the password, consent/terms boxes and ID numbers (name, email, phone,
   address from me/personal). Hand over in one message: the user sets the password (or picks Sign in with Google),
   ticks the terms, clicks Create and confirms the verification email themselves. When they say "done" / "signed
   in", fill the rest of the profile and the application. Record the site in data/accounts.md (never the password)
   and its key with `PY tools/signin.py add`. Whenever the user has to attach a file themselves, send them the
   exact PDF so they never have to look for it.
8. Email-only applications: Gmail draft to the address the posting gives, subject as the posting asks, short
   message, resume + letter attached (if attaching isn't possible, say exactly which files to drag in). NEVER
   send. Set job `email_draft` = short note, status `needs_you`, `needs_you` = ["Gmail draft waiting: check it,
   attach the files if missing, and send it yourself"].
9. Filled-but-not-submitted forms from earlier: if their files are older than the current drafts, set
   `old_files` = note and swap the files on the next fill. Never reuse a tab or saved draft filled before the
   job's current files were built.
10. When the master resume changes: list every filled-but-not-submitted application and re-tailor + re-upload
   (resume_kit.rebuild) before the user submits.
11. Submitted: the dashboard's "Mark as submitted" button sets the status and adds the past-applications row by
    itself. Only if the user tells you in chat instead: set status `submitted`, `submitted_on`, and add the row
    to past-applications.md yourself (check it isn't there already).

## Discovering companies
There is no fixed list of companies checked every day. Each run, `PY tools/discover.py plan` gives today's
searches (`discovery_searches_per_run`, default 4: always one search on job systems such as Greenhouse, Lever,
Ashby, Workable, Workday, SmartRecruiters, plus a rotating mix of "lenses": a second job-system search, start-ups
with recent funding, multinationals opening or growing offices in the area, the biggest companies in one sector,
lookalikes of companies the user applied to, graduate and trainee programmes) and up to 3 "watch" companies due a
re-check. Roles, places and sectors come from settings.json `discovery_roles`, `discovery_places`,
`discovery_sectors`.
1. Run each search with WebSearch using the domains the plan gives. Pick out EMPLOYERS (not job boards or agencies).
2. For each company: `PY tools/discover.py known "<Company>"` first. Unknown -> add it (`PY tools/discover.py add
   <file.json>` with name, type multinational/top_local/startup/other, found_via = the lens, why = one line).
   Known and checked within `discovery_recheck_days` -> skip, unless the search showed a specific fitting job.
3. Investigate up to `discovery_companies_per_run` companies (new first, then re-checks): find their careers page
   and the job list for the user's area (docs/website-playbook.md Part 1, max ~10 steps), collect every fitting
   job (keep = apply), then `PY tools/discover.py checked "<Company>" --verdict watch|skip --found N --note "..."`
   (watch = good employer for the user; skip = nothing fitting / no roles in the area / no way to apply on its own
   site). Save `careers_url`, `system` and `jobs_url` in the record (`add` updates existing records).
4. If the company uses a public feed system (Greenhouse, Lever, Ashby, SmartRecruiters, Workable):
   `PY tools/feeds.py discover "<Company>"`, check it really is that company (some feed types answer for any
   name), and set `feed` in its memory record: its jobs are then checked automatically every run.
5. Jobs found this way: source "Found while browsing <Company> careers page".
6. Record what worked on each careers site in data/site-notes.md. Never open staff/employee sign-in pages.
7. The summary has a short "New companies found today" section (`PY tools/discover.py new-today`).
(`tools/sweep.py` is the old fixed rotation; it's only used now to record a site Claude couldn't read:
`PY tools/sweep.py failed "<Company>" "<what was tried>"` plus `manual_url` = the direct job-list link in
data/careers-pages.json, which puts it on the checklist as "please check manually".)

## Learning from corrections
- When the user corrects a draft, an answer or your behaviour and says "save this to the rules" (or clearly
  wants it to stick): write it in the matching me/ file. Writing style -> writing-rules files; a fact ->
  the matching fact file; a standing instruction -> me/my-rules.md (one dated line); a mechanical rule the
  builder can enforce (banned phrase, never-together pair, allowed skills) -> me/checks.json too.
- When the user edits a letter or answer on the dashboard, look at what changed and propose a rule if a
  pattern shows.

## How it's wired
- Dashboard: app.py (Flask) on http://localhost:5050, started by the launcher files. One folder per job:
  `jobs/<job_id>/job.json` (+ resume.tex/.pdf, cover-letter.txt/.pdf/.docx). Statuses: STATUS_LABELS in app.py.
- data/queue.json: requests from dashboard clicks. Work through every `pending` item on "process the queue" and on
  every morning run; set each to `done`:
  - `draft`: draft the job now. `change_request`: redo the draft as asked. `recheck_cover_letter`: re-check the
    user's edited letter against the rules and note any pattern worth a rule. `save_to_rules`: see Learning.
  - `file_answer`: move the answer into the right section of standard-answers.md and use it on the waiting job.
  - `add_job`: find the posting on the company's own site, score it, add it (`jobs.py add`).
  - `cull`: `PY tools/jobs.py remove <job_id> "<reason>"`.
  - `fill_application` (the user clicked Approve): do Part 1 PREPARE for that job and set it `prepared`; it gets
    filled on the next "fill all ready" (or right away if the user is in the chat and asks).
  - `redo`: rebuild the file(s) and re-run checks now; re-uploading into the form happens only in a session where
    the user is present (on "fill all ready"), and the job gets `old_files` until then.
- Other job.json fields: `waiting_questions` (questions stored on a job; prefer standard-answers.md),
  status `needs_answers` (only if a draft truly can't be finished without a personal fact; rare).
- Waiting questions, in me/standard-answers/standard-answers.md under "## Questions waiting for me", exactly:
  ```
  ### <question>
  - Asked by: <Company> — <Role> (job: <job_id>)
  - Date: YYYY-MM-DD
  ```
  The dashboard adds `- My answer: ...`; file it in the right section and remove it from the waiting list.
- settings.json: home_country, location_keywords, top_job_threshold, max_fills_per_run, discovery_roles,
  discovery_places, discovery_sectors, discovery_searches_per_run, discovery_companies_per_run,
  discovery_recheck_days, keep_means_apply, ntfy_topic, blocked_sites, auto_submit (false).
- data/companies.json: the company memory (tools/discover.py): every company found or investigated, with type,
  how it was found, why, careers system, job-list URL, verdict (watch/skip/new), last check, per-place verdicts
  (`by_place`) and history.
- data/: feeds.json, careers-pages.json (old target list, imported into companies.json), site-notes.md, sites.json (sign-in pages), accounts.md (sites with an
  account; never passwords), seen.json, removed-jobs.json, candidates.json, last_scan.txt, last_run.txt.
- pdflatex: MiKTeX (Windows) or TinyTeX / MacTeX (Mac). tools/build.py finds it, even when it isn't on PATH.

## Updating JobGetter
When the user says "update JobGetter":
1. Download https://github.com/yelli-taha/jobgetter/archive/refs/heads/main.zip to a temporary folder and unzip it
   (it unzips into a `jobgetter-main` folder; the files to copy are inside it).
2. Compare its VERSION with ours; show the user the CHANGELOG.md entries in between, in plain words.
3. Replace ONLY the program files: app.py, tools/, templates/, static/, docs/, CLAUDE.md, SETUP.md, MORNING-RUN.md,
   README.md, START-HERE.md, CHANGELOG.md, VERSION, requirements.txt, the launcher files, .gitignore, starter/.
   NEVER touch me/, jobs/, data/ or settings.json. If starter/ has a data file we don't have yet, copy it in.
   If starter/settings.json has keys ours lacks, add them with their defaults.
4. New settings or data that need the user's values: fill them from me/ (e.g. 1.1.0 Discovery: set
   `discovery_roles` from the role types in search-criteria.md and `discovery_places` from the user's area, then run
   `PY tools/discover.py seed` once to import their target companies and feeds into data/companies.json).
5. `PY -m pip install -r requirements.txt`, restart the dashboard, check every page loads, tell the user what changed.

## Building and fixing
- If something in JobGetter breaks, fix it, test it (run the dashboard and open the page), and note it in PROGRESS.md.
  Keep changes small and in the user's interest; don't redesign without asking.
