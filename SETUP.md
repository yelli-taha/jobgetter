# JobGetter setup (for Claude to follow)

You're setting JobGetter up for someone who may never have used a terminal. Your job: do everything you can
yourself, ask everything you need UP FRONT in a few friendly rounds, and leave them with a working system.

Ground rules for setup:
- Plain words. No jargon. When they must do something, say exactly what to click and why, one step at a time.
- Ask in rounds of at most ~8 short numbered questions. Say "skip anything you don't know; I'll ask again only
  if an application needs it." Pre-fill what you already know (from their resume) and ask them to confirm.
- Never ask for passwords, card numbers or government ID / passport numbers. Never store them.
- Keep track in PROGRESS.md ("Setup: step N done", plus "Setup: remaining steps ...") so setup can resume if the
  chat is interrupted. If PROGRESS.md shows setup already started, continue from the next step instead of starting over.
- Check the files are in the right place: CLAUDE.md, SETUP.md and app.py must be directly in the project folder. If
  they're inside a `jobgetter-main` subfolder (that's how GitHub's ZIP unzips), move everything in it up one level
  and delete the empty subfolder.
- Read CLAUDE.md first: its Safety rules apply during setup too.
- `PY` = `.venv\Scripts\python.exe` (Windows) or `.venv/bin/python` (Mac).

---

## Step 0. Say hello (send this, in your own friendly words, before doing anything else)

> **Welcome to JobGetter!** Here's what it is and what happens next.
>
> **What it does for you, every day:**
> - Finds new jobs that fit you: from your job-alert emails, companies' own careers pages, and the web.
> - Scores each one and explains why, so the best ones come first.
> - Writes a tailored one-page resume and cover letter for each job, in your voice, using only true facts about you.
> - Fills in the application forms on the companies' websites in your Chrome, and **stops before Submit**.
>   You check everything and click Submit yourself.
> - Shows it all on a simple dashboard on your computer, and (optionally) pings your phone when applications are ready.
>
> **What it never does:** submit anything for you, type your passwords, create accounts for you, or share your
> data. Everything stays on this computer.
>
> **What happens now (about 30-45 minutes, mostly me working):**
> 1. I set up your computer (install a couple of free tools; you may need to click "Yes" on a popup or two).
> 2. I read your resume and ask you a few rounds of questions: where you live, what jobs you want, a few stories
>    about your work, and standard form answers. Skip anything you're unsure about.
> 3. I build your master resume, find companies near you that hire for your kind of role, and connect everything.
> 4. I show you the dashboard and set up a daily morning run.
>
> When I ask permission to run something, it's me setting up JobGetter: choose **Allow** (or "always allow" for
> this project). To start, **please drag your current resume (PDF or Word) into this chat**, and paste your
> LinkedIn link if you have one. If you have a cover letter you liked, add that too.

While they find their resume, start Step 1.

## Step 1. Set up the computer
Check the operating system first.

**Windows**
1. Python 3.10+: `py --version` or `python --version` (a "python" that opens the Microsoft Store doesn't count).
   Missing: `winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements`.
   Right after installing, the new Python isn't on PATH in this session: use its full path,
   `%LOCALAPPDATA%\Programs\Python\Python312\python.exe`. No winget: ask them to install from
   python.org/downloads (tick "Add python.exe to PATH"), with clear click-by-click steps.
2. LaTeX: `pdflatex --version`. Missing: `winget install -e --id MiKTeX.MiKTeX --accept-package-agreements --accept-source-agreements`,
   then turn on automatic package installs: `initexmf --set-config-value=[MPM]AutoInstall=1` (the exe is under
   `%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64\` if not on PATH). Tell them a MiKTeX window may pop up: click Yes/Install.
3. In the project folder: `<that python> -m venv .venv` (full path if needed), then `PY -m pip install -r requirements.txt`.

**Mac**
1. Python: `python3 --version` (3.9+ is fine). If macOS offers to install "command line developer tools", tell them to click Install and wait.
2. LaTeX: `pdflatex --version`. Missing: install TinyTeX for this user (no admin password needed):
   `curl -sL "https://yihui.org/tinytex/install-bin-unix.sh" | sh`, then
   `~/Library/TinyTeX/bin/*/tlmgr install titlesec enumitem marvosym preprint fancyhdr xcolor hyperref babel-english tools glyphlist`
   (and `tlmgr install <package>` for any "File X.sty not found" error later). If the installer asks for a password
   to link programs into /usr/local/bin, skip that part: JobGetter finds TinyTeX in ~/Library/TinyTeX by itself.
3. `python3 -m venv .venv`, then `.venv/bin/python -m pip install -r requirements.txt`. Make the launcher clickable:
   `chmod +x "Start Dashboard.command"`.

**Both:** create the user's folders by copying from starter/ WITHOUT overwriting anything that exists:
- `starter/me/` -> `me/` (all files except profile.template.json), `starter/data/` -> `data/`,
  `starter/settings.json` -> `settings.json`, and create an empty `jobs/` folder.
- Test the tools: `PY tools/build.py check me/samples/master-resume.tex` must compile (one page). Fix problems now.
- Check Claude in Chrome: list the browser tabs. If the Chrome tools aren't there or don't answer, walk them
  through: install "Claude in Chrome" from the Chrome Web Store, sign in with the same Claude account, keep Chrome open.
- Check Gmail: run a small Gmail search. If Gmail isn't connected, tell them: Claude app -> Settings ->
  Connectors -> Gmail -> Connect, then come back and say "done".

## Step 2. Read their resume (and anything else they attached)
Extract everything: name, contact, education (with dates, grades), every job/internship/volunteer role
(employer, title, location, dates, bullets), skills, tools, languages, certificates, achievements.
Tell them in 3-4 lines what you found. Then draft (don't show yet):
- one file per job in me/experience/<key>.md (template in me/experience/_how-to.md; keys short, lowercase),
- me/education/education.md, me/skills/skills.md, me/achievements/achievements.md,
- the contact fields for me/profile.json (written at the end).
No resume? Ask them to paste it as text, or to describe their jobs and studies; work from that.

## Step 3. Interview rounds (one message per round; wait for answers between rounds)
Pre-fill from the resume wherever you can ("I have X; correct?").

**Round 1: You and where you live**
1. Full name as it should appear on applications, and the first name you go by.
2. Email for applications (ideally the Gmail connected to Claude) and phone number with country code.
3. Where do you live? City and area. (Used to judge commutes; your full street address only if you want me to
   fill it on forms that require it.)
4. How long a commute is OK? Would you relocate (where)? Remote jobs: only employers in your country, or anywhere?
5. Which countries can you work in without a visa? Will you need sponsorship anywhere?
6. Languages you can work in, and your level.
7. Forms often ask for date of birth, nationality, gender, and (in some countries) military service status.
   Want me to fill those when asked? If yes, give them now; if not, I'll leave those fields for you.

**Round 2: The jobs you want**
1. What kinds of roles? (Titles or fields; examples help. Several is fine.)
2. Anything you definitely don't want (roles, industries, companies)?
3. Your experience level: student, fresh graduate, 1-2 years, more? Roles asking for how many years at most?
4. Full-time only, or also internships, part-time, contract?
5. Salary: a number to put on forms (with currency, monthly or yearly), and is pay a deal-breaker?
6. When can you start? Any notice period?
7. Dream companies, if any? And companies you've already applied to (roughly when, which role, any result)?

**Round 3: Your stories** (this is what makes the cover letters sound like you; a few sentences each is plenty)
1. Why this field or these roles? What draws you?
2. The achievement you're proudest of: what you did, how, the result (numbers if you have them).
3. A problem you solved or a time something went wrong and you turned it around.
4. A time you worked with or led others.
5. What do you look for in an employer? What do you care about at work?
6. Anything that must NEVER appear in applications (health, family matters, a gap, anything private)?
   And if you have a gap in your history, how would you like it explained if a form asks?
7. How should your letters sound? (Use a multiple-choice question: Warm and personal / Confident and direct /
   Formal and polished / Let Claude match my sample letter.) Any words or phrases you love or hate?

**Round 4: Standard form answers**
1. Driving licence? Willing to travel for work?
2. Diversity questions (gender, ethnicity, disability): answer them, or "prefer not to say"?
3. References: names and contacts, or "available on request"?
4. Emergency contact (optional; I'll ask when a form needs it).
5. Should your grade/GPA appear on your resume?
6. Which job sites send you job-alert emails now (LinkedIn, Indeed, local job boards)? To the connected Gmail?
7. Do you already have accounts on any company job sites (e.g. Workday at a company)? Rough list is fine.
8. When a site lets you "Sign in with Google" and you already have an account that way, may I click it?
   (I'll still ask once per session.)

## Step 4. Write their files
From the resume and answers, fill every file in me/ (replace the template prompts with their content; delete
sections that don't apply). In particular:
- me/personal/personal-details.md, me/search-criteria/search-criteria.md, me/stories/stories.md (Private section
  = their never-mention list), me/standard-answers/standard-answers.md, me/target-companies/past-applications.md
  (table rows, newest first), me/writing-rules/* (add their tone, phrases, never-rules).
- me/checks.json: add their banned phrases; a `letter_banned_patterns` entry for each private topic
  (`{"\\bword\\b": "Private topic (never in applications)"}`); `never_together` for rules like "never mention tool X
  with employer Y" (`{"a": "Employer", "b": "Tool", "job_key": "<key>", "where": "both", "why": "..."}`);
  skills lists to match skills.md (left = tools; right default = always-included; stockpile = picked per job).
- settings.json: `home_country`, `location_keywords` (lowercase names of their city, nearby cities and areas,
  the country, and ", <country code>"; add "remote" if they want remote jobs), `blocked_sites` (+ local job boards
  whose rules forbid bots), `discovery_roles` (5-20 short job titles from their role types, e.g. "business
  analyst", "graduate program"), `discovery_places` (their city and 1-3 nearby cities/areas) and
  `discovery_sectors` (industries they like; leave empty for a broad mix). Keep top_job_threshold 60 and
  max_fills_per_run 10 unless they asked otherwise.
- data/accounts.md: one row per job site they already have an account on (Round 4, question 7), sign-in method
  "Google" or "Password". Their answer to question 8 is noted in my-rules.md, but you still ask once per session.
Write me/profile.json LAST in this step (from starter/me/profile.template.json): name, email, phone, linkedin,
`file_prefix` (e.g. "Sara_Ahmed"), `paper` ("letterpaper" for the US/Canada, otherwise "a4paper"),
`resume.always_keep` (their current or most important job keys). Don't add "setup_complete" yet.

## Step 5. Build the master resume
1. Fill me/samples/master-resume.tex from their resume, keeping the template's layout: header, Education,
   Skills table (Tools | Core Competencies, or labels that fit their field), Courses & Certifications (remove if
   none), Experience with a `% JOB: <key>` line before every entry (same keys as me/experience/). Set the paper
   size to match profile.json. Strong verbs, results, numbers they gave you, nothing invented.
2. `PY tools/build.py master` -> me/samples/master-resume.pdf. Must be exactly one page.
3. Open the PDF for them (and send it in chat if you can). Ask: "Anything wrong or missing?" Fix and rebuild until
   they're happy. This master is what every tailored resume starts from.

## Step 6. Find their companies
1. Research employers in their area that hire for their roles (web search; ~30-80 companies): big local
   employers, multinationals with offices there, strong startups, government/NGO if relevant, plus their
   dream companies. Group by industry; mark 5-10 as priority (dream companies and the best fits).
2. Write me/target-companies/target-companies.md. Show them the list in short groups and ask them to strike any
   they don't want and add any missing.
3. For each company: `PY tools/feeds.py discover "<Company>" ...` (finds public job feeds; check each found feed
   really is that company). For the rest, add {"company", "url" (careers page if known), "priority": true/false}
   to data/careers-pages.json. Then `PY tools/discover.py seed` copies them all into the company memory
   (data/companies.json). Explain: this list makes their jobs rank higher, and every morning JobGetter also
   discovers new companies by itself.
4. If they're in Egypt, copy the matching companies from docs/known-sites-egypt.md into data/site-notes.md.
   (If a known-sites file exists for their country, do the same.)

## Step 7. Job alerts
Job-alert emails are the biggest source of jobs. If they don't have alerts going to their Gmail, give them short
click-by-click steps to create alerts themselves on the job sites they use (LinkedIn: Jobs -> search a title and
location -> "Set alert"; same idea on other boards), 2-4 alerts for their main role types and area. You never
open those sites yourself; you only read the alert emails.

## Step 8. Phone notifications (optional, ~3 minutes)
Ask if they want a ping on their phone when applications are ready. If yes:
1. Make a random topic: `jobgetter-` + 12 random lowercase letters/digits. Save it as settings.json `ntfy_topic`.
2. Tell them: install "ntfy" from the App Store / Play Store; open it; tap +; type the topic exactly; leave the
   server as ntfy.sh; Subscribe; allow notifications. The topic works like a private address.
3. `PY tools/notify.py test` and ask if it arrived.

## Step 9. Show the dashboard
First set `"setup_complete": true` in me/profile.json (the dashboard shows a welcome page until then), and write
PROGRESS.md "Setup: steps 1-9 done; remaining: 10 (morning run), 11 (first run)". Then start it (`Start Dashboard.bat` on Windows: double-click, or run it; Mac: `Start Dashboard.command`) and open
http://localhost:5050. Walk them through it in 5 lines: Review (jobs and drafts), Ready to submit (filled forms and
the sign-in checklist), Questions for you, Tracker, Add a job (paste any posting link). Tell them: to open it later,
double-click "Start Dashboard" in the JobGetter folder, or ask Claude "open the dashboard".

## Step 10. The morning run
Ask what time they usually open their computer. Create a scheduled task (use your scheduled-task tool if you have
one): name "JobGetter: morning run", daily at that time (a bit before is fine: it runs when Claude opens), folder =
this project folder, instructions: `Read MORNING-RUN.md in the project folder and follow it.`
If you can't create it yourself, give them the steps to create it in the Claude app's scheduled tasks, with that
exact instruction text. Explain: the computer and the Claude app need to be on for it to run; if they miss a day,
the next run catches up.

## Step 11. First run and wrap-up
1. Write PROGRESS.md: setup done (date), what's configured, anything still missing (no "remaining" steps left).
2. Ask: "Want me to do the first job search now? It takes about 20-40 minutes and you don't need to watch."
   If yes, follow MORNING-RUN.md (this run may ask them questions since they're here).
3. Finish with this cheat sheet (in your own words):
   - Every morning JobGetter finds jobs and prepares the best ones. You get a phone ping.
   - Type **fill all ready**: I fill the forms in Chrome and stop before Submit. Keep Chrome open and visible.
   - Some sites need you to sign in or create an account first: they appear on the **Sign-in checklist** with
     direct links. Sign in (let Chrome save your password), then type **signed in**.
   - Check each filled tab, fix anything, click Submit, then click "Mark as submitted" on the dashboard.
   - Didn't like something? Tell me, and say **save this to the rules** so it never happens again.
   - **update JobGetter** gets the newest version; your files are never touched.
