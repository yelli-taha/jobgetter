# Known careers sites: Egypt

Notes on how to reach Egyptian job lists on some big employers' careers sites (2026). Setup copies the companies
that match your targets into data/site-notes.md. Sites change: treat these as a head start, not gospel.
PY = .venv\\Scripts\\python.exe on Windows, .venv/bin/python on Mac.

## Vodafone Egypt
- Careers page: https://opportunities.vodafone.com/ (Vodafone Group site; web.vodafone.com.eg/en/careers links here)
- Job system: SuccessFactors career site
- Egypt list: https://opportunities.vodafone.com/search/?q=&locationsearch=Egypt (25 per page; add &startrow=25, 50, ...)
- How to filter: the "Search by Location" box = Egypt; the URL changes, so use it directly. Fastest: `PY tools/careers.py sf https://opportunities.vodafone.com Egypt <out.json>` then `PY tools/careers.py text <out.json> <titles>`.
- Confirm location: each row shows "Cairo, EG" / "Giza, EG"; posting pages repeat it.
- Unusual: cookie banner (click Reject). Many VOIS roles need German/Portuguese. Graduate "Customer Care Advisor" programme says max age 30.

## PwC (Middle East)
- Careers page: https://www.pwc.com/m1/en/careers/experienced-jobs.html (page table loads everything client-side; location checkboxes "Cairo" + "Cairo - ETIC"; grade checkboxes "Associate", "Intern/Trainee" narrow it to ~69)
- Job system: Workday — https://pwc.wd3.myworkdayjobs.com/Global_Experienced_Careers
- Egypt list: fastest is `PY tools/careers.py workday https://pwc.wd3.myworkdayjobs.com/Global_Experienced_Careers Cairo <out.json>` (search "Cairo" returns all Cairo + Cairo-ETIC jobs, including senior ones), then `PY tools/careers.py text <out.json> <titles>` for descriptions.
- Confirm location: Workday "location" field ("Cairo - ETIC" = New Cairo, Cairo Festival City).
- Unusual: the pwc.com table freezes timed scripts in a background tab; use Workday instead. Most Cairo roles are ETIC tech; graduate programmes are the best fits.

## Commercial International Bank (CIB)
- Careers page: https://www.cibeg.com/en/careers ("Apply now" -> Taleo)
- Job system: Taleo — public board https://cibeg.taleo.net/careersection/cib_ex/jobsearch.ftl?lang=en (NOT cibeg.taleo.net/careersection/ alone: that is the staff sign-in, never use it)
- Egypt list: everything is in Egypt; narrow with the left "Governorate" filter: tick your governorates. Filters don't change the URL. In a background tab, tick the boxes from JS (c.click()).
- Pages: 25 per page; collect with the "Next" link. Posting pages: jobdetail.ftl?job=<ID>&lang=en (fetchable from the page; text is URL-encoded inside the HTML).
- Unusual: "Better Together" and "(People With Disabilities)" roles are inclusion programmes (only for candidates they are meant for). Many "OUTSOURCE" agent roles (not CIB employees).

## Red Bull
- Careers page: https://jobs.redbull.com/eg-en/
- Job system: own site (COSMOS web components)
- Unusual: apply forms need real typing (see docs/website-playbook.md, Red Bull). Postings may show "Stay tuned" before opening.


## Namshi
- Careers page: no Cairo listings found on its SmartRecruiters page (Dubai and India only). Part of the noon group: check noon's careers page for Cairo roles.

## McKinsey
- Careers page: https://www.mckinsey.com/careers/search-jobs
- Unusual: the list shows every job worldwide with "Load more". Use the location filter (Cairo / Egypt) first. WebFetch times out; use the browser. Global postings list Cairo among 50-100+ offices: check the posting text for "Cairo". Apply = mckinsey.avature.net/careers/ApplicationMethods?folderId=<id> (account needed).

## Amazon
- Egypt list: JSON, no browser needed: https://www.amazon.jobs/en/search.json?normalized_country_code%5B%5D=EGY&result_limit=100&sort=recent (fields title, normalized_location, job_path, basic_qualifications, preferred_qualifications).
- Unusual: many roles are supervisors/managers or language-specific care associates; intern roles state graduation windows.

## PepsiCo
- Careers page: https://www.pepsicojobs.com/egypt/jobs (Jibe). Egypt list API from that page: fetch('/api/jobs?country=Egypt&limit=100&page=1') -> jobs[].data (title, city, req_id, description). Posting/apply: https://www.pepsicojobs.com/main/jobs/<req_id>?lang=en-us

## Unilever
- Egypt list: https://careers.unilever.com/en/search-jobs/Egypt/34155/2/357994/27/30/50/2 (links in #search-results-list). Apply goes to Workday unilever.wd3 (Unilever_Experienced_Professionals).

## P&G
- Egypt list: https://www.pgcareers.com/location-Egypt (Phenom: window.phApp.ddo.eagerLoadRefineSearch.data.jobs).

## Mastercard
- Egypt list: `PY tools/careers.py workday https://mastercard.wd1.myworkdayjobs.com/CorporateCareers Cairo <out.json>` (the Phenom site careers.mastercard.com shows the same list).
- Unusual: graduate/intern programmes state graduation windows: check eligibility.

## BCG
- Cairo postings: careers.bcg.com/global/en/job/<id>/... (Phenom). Search the site with location Cairo, or web search "BCG careers Cairo".

## EY
- Egypt list: `PY tools/careers.py sf https://careers.ey.com Egypt <out.json>` (SuccessFactors).

## Microsoft
- Egypt list: https://apply.careers.microsoft.com/careers?location=Egypt (Eightfold; read page text).

## Deloitte (Middle East)
- Careers page: https://middleeastjobs.deloitte.com/ (Avature). Search /careersME/SearchJobs/egypt shows results only 6 per page and the offset parameter didn't page; next time use the site's own Next button in the browser.
