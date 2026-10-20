# Website playbook: finding jobs and filling forms on real sites

How Claude gets through careers sites and application forms in the user's Chrome (Claude in Chrome).
Everything here was learned the hard way on real applications. Read the matching section before working
on a site, and add what you learn to `data/site-notes.md` (company-specific) or to this file's
"Lessons" (system-wide) so the next run is faster.

Golden rules, always:
- Work in a NEW, VISIBLE tab. Screenshots and typed keys fail when the Chrome window is minimized or behind
  other windows (form_input and JS read-back still work).
- Never click Submit, never type a password, never solve or bypass a CAPTCHA, never type a government ID
  number, never tick terms/consent boxes or sign e-signatures, never click "Apply with LinkedIn/Indeed" or any
  job-board autofill. These belong to the user.
- Cookie banners: pick the most private option ("Reject all" / "Decline all" / "Necessary only").
- Don't loop. About 10 tries per stubborn field or site, then hand it to the user with exact instructions
  (status `needs_you`) and move on.

---

## Part 1: Finding the job list on a careers site

1. Read the company's section in `data/site-notes.md`. If it has a filtered-list URL or a tool command, start there.
2. No careers page known: web search "<company> careers <country>" and open the company's own site (never a
   job board). The "Careers" / "Jobs" / "Join us" link is usually in the page footer.
3. Work out which hiring system it uses. The address bar usually tells you:

   | Address contains | System | Fastest way to the list |
   |---|---|---|
   | myworkdayjobs.com | Workday | `PY tools/careers.py workday <site url> "<city>" out.json` |
   | successfactors, jobs.sap.com, `/search/?q=&locationsearch=` | SAP SuccessFactors | `PY tools/careers.py sf <base url> "<country>" out.json` |
   | boards.greenhouse.io, job-boards.greenhouse.io | Greenhouse | public feed: `PY tools/feeds.py discover "<Company>"` |
   | jobs.lever.co | Lever | public feed (feeds.py) |
   | jobs.ashbyhq.com | Ashby | public feed (feeds.py) |
   | jobs.smartrecruiters.com | SmartRecruiters | public feed (feeds.py) |
   | apply.workable.com | Workable | public feed (feeds.py) |
   | taleo.net | Oracle Taleo | browser: left-hand filters, "Next" pages |
   | oraclecloud.com ... CandidateExperience | Oracle Recruiting Cloud | browser: location box, then scroll |
   | icims.com | iCIMS | browser, or the company page's own search |
   | avature.net | Avature | browser: location filter, "Load more" |
   | eightfold.ai, or careers pages with "Career Hub" | Eightfold | read page text after filtering |
   | careers.<company>.com with `window.phApp` | Phenom | JS: `window.phApp.ddo.eagerLoadRefineSearch.data.jobs` |
   | teamtailor.com, careers.<company>.<tld>/jobs | Teamtailor | browser; apply at `<job url>/applications/new` |
   | personio, recruitee, breezy, bamboohr, jobvite, pinpoint | small-company systems | plain pages: WebFetch usually works |

4. Narrow FIRST, scroll LAST: set the location filter (city / country / "remote" if the user wants remote), via
   the filter panel, a dropdown, a location box, or the site's own search API. Then search by title if you're
   looking for one job. Many sites put the filter in the URL; if so, save that URL in site-notes.
5. Only after narrowing: "Load more" / next page, at most 5 times. Many lists are 20-25 per page.
6. Page shows nothing? Wait a few seconds and read again (lists often load after the page). Try
   `get_page_text`, then scroll and screenshot. Check for an iframe (the list may live on another domain:
   open that URL directly).
7. Confirm each job's location on its own posting page (filters can be loose).
8. Collect EVERY job on the filtered list, not just the first few. Score them all.
9. Still stuck after ~10 steps: `PY tools/sweep.py failed "<Company>" "<what you tried>"`, set `manual_url` for
   the company in data/careers-pages.json (it shows on the checklist as "please check manually"), move on.
10. Update `data/site-notes.md` with what worked, and `PY tools/sweep.py done "<Company>" "<filtered url>" --found N`.

Useful tricks:
- Many sites have a JSON search endpoint behind the page (look at what the page loads, or try the site's own
  "search.json" / "/api/jobs"). Reading JSON is faster and more reliable than clicking.
- Global companies often list one posting for 50+ offices. Check the posting text for the user's city.
- A posting that only exists on a job board (LinkedIn etc.) and nowhere on the company's own site or official
  careers email can't be applied to under the rules: cull it.

---

## Part 2: Filling an application form

### Before typing
1. Open the company's application page in a new tab (Lever: add `/apply` to the job URL; Teamtailor:
   `/applications/new`).
2. List every field: `get_page_text` + `read_page`, THEN scroll the whole form top to bottom with
   screenshots. Page text misses custom fields (whole "Additional information" sections have been invisible to it).
3. Multi-step forms: note the step count ("Step 2 of 12") so you know when you're really done.

### The ladder: what to try when a field won't take a value
Go down the ladder only as far as needed. After each attempt, READ THE VALUE BACK.

1. `form_input` on the field's ref. Works on plain HTML forms (Lever, Teamtailor, Taleo, most small systems).
2. Click the field, then type with real keystrokes (`computer` type).
3. Field already has text (pre-filled from an old application or a parsed resume)? Typing over it can DOUBLE
   the text ("LinkedInLinkedIn"), and Ctrl+A can type the letter "a" instead of selecting. Select the existing
   text first with JS: focus the field, then `document.activeElement.select()`, then type.
4. Custom dropdowns (Workday, React selects, SAP UI5 combos, Eightfold):
   - Click the dropdown button, wait, then click the option by its visible text.
   - Click didn't register? Find the option element (`[role=option]` or `li` with the text) and dispatch the full
     event sequence on it: pointerdown, mousedown, pointerup, mouseup, click.
   - Searchable dropdowns (typeahead): click, type the first few letters, wait for the list, click the match.
   - Workday "prompt" fields (country, school, degree): type, press Enter, then pick from the results list.
5. Native `<select>`: `form_input`, or set `.value` and dispatch `input` and `change` events.
6. React / Vue inputs ignore a plain `.value =`. Use the native setter, then fire the event:
   `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el, v); el.dispatchEvent(new Event('input',{bubbles:true}))`
7. Web components / shadow DOM (custom component libraries, some SAP sites): JS setters often don't stick. Walk the
   shadow roots to find the input by name, call `el.click(); el.focus()`, then type with real keystrokes.
8. Date pickers: look at the placeholder for the format (MM/DD/YYYY vs DD/MM/YYYY). Type it and press Enter,
   then close the popup (Escape, or click a blank part of the page); popups that stay open block other fields.
   If a picker only allows future dates for a past date (a "graduation date" picker built for students),
   don't let it put in today's date: leave it, flag it, and tell the user.
9. Radio buttons, Yes/No buttons, toggles: click, then CHECK BY SCREENSHOT. Ref clicks on button-style Yes/No
   have silently failed.
10. Checkboxes JS can't tick (e.g. Taleo's "this document is a resume" tick): real click at the screenshot coordinates.
11. Buttons that reload the page ("Add another job", "Add education"): click ONE at a time and wait for the reload
    before the next. Clicking several quickly loses entries.
12. Fields that duplicate when set twice (Workable's address): set once, read back, don't retry blindly.

### File uploads (resume, cover letter)
- Use `file_upload` with the absolute path of THIS job's tailored PDF in `jobs/<id>/`.
- Then prove it worked, all three:
  1. JS: the file input's `files[0].name` and `files[0].size` match the PDF;
  2. the page shows that exact file name;
  3. any "uploaded" / "Success" confirmation appears (Lever also fills a hidden storage id).
- Make sure NO other resume is still attached or selected (sites keep old uploads). Remove or deselect old ones.
- Save on the job: `attached` = [{"name": <file name the site shows>, "confirmed": <time>}]. Can't confirm? Set
  `check_attachment` = a short note and status `needs_you`, never "ready".
- Upload hidden in a shadow DOM where `file_upload` can't reach (SmartRecruiters' one-click form): fill the
  rest, then `needs_you` with the exact path for the user to attach.
- Some sites drop the file when Submit is clicked. If the user reports that,
  give them the PDF to attach right before submitting, and note it in site-notes.

### Sites that remember you (the "old resume" trap)
Workday ("Use My Last Application"), Amazon, Avature, Eightfold, iCIMS and others pre-fill steps from an earlier
application and show them with green ticks, holding OLD data. Open EVERY step, even ticked ones, and check:
- the resume is this job's tailored file (replace anything else);
- address and postal code match me/personal/personal-details.md;
- "How did you hear about us?" is this job's real source (never a job board unless it came from that board's alert);
- "Have you applied here before?" matches me/target-companies/past-applications.md.
Read the final Review page in full before handing over. Some candidate profiles (often Eightfold career hubs) are read-only
and keep every resume ever uploaded: make sure only this job's file is selected.

### Shared profiles (one account, several applications)
On Avature-style sites one profile (resume, letter, education) serves every application. With two jobs at the same
company, the profile files belong to whichever is submitted first. Handle the swap yourself: after the user
submits the first, put the second job's files on the profile, then fill the second.

### Finishing a form
- Read every value back (one JS pass over all inputs, then screenshots of each section).
- Multi-step: after each "Save and continue", look for an error banner at the top ("Error - Personal
  information") and re-read the current step number. A form that looks done can still be on step 2.
- Scroll to the top, leave the tab open, status `filled`, and list what the user must do (tick the terms box,
  type the ID number, sign, click Submit).
- Save (draft) buttons are fine; Submit / Apply / Send buttons are never clicked. On some sites the button that
  submits is labelled "Apply" (SuccessFactors): know which is which before clicking anything.

---

## Part 3: Sign-ins

- Being signed in on a careers site does NOT mean signed in to its application system: many apply through a
  separate login (Amazon: passport.amazon.jobs; SuccessFactors: a career5.successfactors.* address; iCIMS:
  its own email + password). Check by clicking Apply, not by the header of the careers site.
- Workday has a separate account PER COMPANY, and sessions expire within about an hour.
- "Sign in with Google" for an EXISTING account is fine once the user has OK'd it in this session. Some
  Google sign-ins show a legal notice to accept first (that's the user's to accept).
- Never create accounts (including "Sign up with Google"), never type or autofill passwords, never click
  account-verification links. Pre-fill a sign-up form except the password if the user asks, then hand over.
- Government ID details saved in Chrome autofill: still the user's to pick (one click for them). Leave the
  field empty and point to it.

---

## Part 4: Tool gotchas

- JS results that contain "=" or URL-like text can come back as `[BLOCKED: Cookie/query string data]`.
  Return values without "=" (e.g. replace it), or return counts and short summaries instead of raw URLs.
- `read_page` can miss panels that open on click (edit panels, modals): use screenshots.
- Pages shift while you type (autocomplete lists, validation messages): screenshot after every few inputs.
- A background tab may never finish loading a modal or may freeze timed scripts: bring the tab to the front.
- Very long pages: use `find` or JS to locate a field instead of scrolling screen by screen.

---

## Lessons by system (add to these)

- **Workday:** "Use My Last Application" carries over old answers, files and typos: check every field. Dropdowns:
  click button, then dispatch pointer/mouse events on the `[role=option]`. Pre-filled text doubles when typed
  over: select() first. Separate account per company; sessions expire fast.
- **SAP SuccessFactors:** UI5 combo boxes (type + pick). "Save" keeps a draft; "Apply" submits (never click it).
  Application login is separate from the careers site.
- **Oracle Taleo:** plain HTML, JS setters work. "Add" buttons reload the page: one at a time. University lists
  can be country-only: pick "Other" and type the name. A reference may be required ("NA" has been accepted).
  Ticking a document as "Resume" needs a real click. The last steps can include an e-signature (user's).
- **iCIMS:** own login (email, privacy accept, password) per company. Remembers the last resume.
- **Greenhouse / Ashby:** plain forms; Ashby's Yes/No buttons must be verified by screenshot.
- **Lever:** plain HTML; JS setters and radio clicks work. Parses the resume and fills "Current company" from
  it: fix it if the user isn't employed there now. Verify the file is in the input and the storage id is set.
- **SmartRecruiters:** file input inside shadow DOM: user attaches the file. Never "Apply with Indeed".
- **Workable:** cookie banner (Decline all). Address field duplicates if set twice.
- **Teamtailor:** decline cookies; open `<job url>/applications/new` directly; JS setters work.
- **Avature:** one shared profile; set "Do you want to update your resume?" to Yes or the old file
  stays. A privacy acknowledgement step is the user's to tick.
- **Eightfold:** React selects (click, type, pick). Date pickers stick open: type MM/DD/YYYY + Enter,
  then hide the popup. Candidate profile is read-only and keeps old resumes.
- **Amazon (amazon.jobs):** separate login at passport.amazon.jobs. Pre-completed steps carry old data, including the
  resume. Some date pickers only accept future dates.
- **Sites built from web components (custom tags like `<x-input>`):** JS values don't stick: shadow-root walk, focus,
  real typing. Selects: click the custom select trigger, then the option text. Edit/Done buttons open and close panels.
