# Changelog

## 1.1.1
- **New lesson for SAP SuccessFactors sites** (the newer candidate portals): Claude can't attach the resume on
  the first step there, so it sends you the PDF to attach yourself and then carries on. These sites also allow only
  one application in progress at a time, so Claude finishes one before starting the next.

## 1.1.0
- **Discovery: JobGetter now finds new companies by itself.** Instead of checking the same list of companies
  every day, each morning it runs a few different searches (job systems, start-ups that just raised money,
  big companies opening offices near you, the biggest companies in one industry, companies like the ones you
  applied to, graduate programmes) and remembers every company it finds. Your target list still makes their
  jobs rank higher. The morning summary now ends with "New companies found today".
- **Search another place for one run:** type "morning run for <city>" and that run looks only there, using that
  place's own rules from your search criteria (pay, nationals-only roles).
- **Help with new accounts:** when a site needs a profile, Claude can fill in the sign-up page for you (everything
  except the password, terms and ID numbers); you finish it and Claude fills the rest.
- **Fix:** jobs you removed no longer come back from the job feeds.
- **New lessons** for Workable, SmartRecruiters, Teamtailor and Avature forms, and for graduate programmes
  that close within two weeks.
- After updating, Claude sets up Discovery from your search criteria (nothing for you to do).

## 1.0.0 (2026-10-20)
First shared version. Daily job search (alert emails, company careers pages, public feeds, web), scoring,
tailored LaTeX resumes and cover letters with automatic rule checks, application filling in Chrome that stops
before Submit, sign-in checklist, dashboard, phone notifications, setup interview for any location.
