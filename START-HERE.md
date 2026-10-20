# Start here: setting up JobGetter

No technical knowledge needed. Follow these steps in order. Steps 1 to 4 take about 10 minutes; then Claude
takes over.

## 1. Get a paid Claude plan and the desktop app
1. Sign up or log in at [claude.ai](https://claude.ai) and choose the **Pro** plan or higher. JobGetter
   needs Claude Code, which comes with paid plans. Filling many forms uses a lot of Claude: on Pro, if you hit
   your usage limit, just continue later or ask Claude to fill fewer applications per run.
2. Download the **Claude desktop app** from [claude.ai/download](https://claude.ai/download), install it,
   and sign in.

## 2. Add Claude to Chrome
1. Open **Google Chrome**. Other browsers won't work for this part.
2. Search the Chrome Web Store for **"Claude in Chrome"**, click **Add to Chrome**, then sign in with the
   same Claude account.
3. Pin it to your toolbar: click the puzzle-piece icon, then the pin next to Claude.
4. In the Claude desktop app: **Settings → Connectors**. If **Claude in Chrome** is listed there, turn it on.

## 3. Connect Gmail
In the Claude app: **Settings → Connectors → Gmail → Connect**, and allow access. Claude uses this to read
your job-alert emails. It never sends an email without you.

## 4. Make a folder and paste the message
1. Make a new, empty folder called **JobGetter** in your **Documents** folder.
2. In the Claude desktop app, open the **Code** tab and start a new session. When it asks for a folder,
   choose the **JobGetter** folder.
3. Copy this message, paste it into the chat, and press Enter:

```
Set up JobGetter for me. Download https://github.com/yelli-taha/jobgetter/archive/refs/heads/main.zip,
unzip it, and put everything from inside its jobgetter-main folder directly into this folder (no git
needed). Then read SETUP.md and follow it step by step. I'm not technical: do everything you can
yourself and explain anything I have to do in plain words.
```

## 5. What happens next
Claude introduces JobGetter, then:
- **Sets up your computer.** It installs Python and a document tool called MiKTeX (or TinyTeX on a Mac).
  If Windows asks "Do you want to allow this app to make changes?", click **Yes**.
- **Asks to run commands.** That's Claude setting things up. Click **Allow**, or "always allow" for this
  project so it stops asking.
- **Reads your resume.** Drag your resume file (PDF or Word) into the chat when it asks.
- **Asks four short rounds of questions:** where you live, the jobs you want, a few stories about your work,
  and standard form answers. Skip anything you're unsure about.
- **Builds your master resume** and shows it to you. Tell it what to change until you're happy.
- **Finds companies** near you that hire for your kind of role. Strike any you don't want.
- **Sets up phone notifications** (optional) with the free **ntfy** app.
- **Shows you the dashboard** and sets up a daily morning run.

## 6. Every day after that
- In the morning, JobGetter finds jobs and prepares the best ones. Your phone gets a ping.
- Open the Claude app and type **fill all ready**. Keep Chrome open and on screen while it works.
- Some sites need you to sign in or create an account first. They appear on the **Sign-in checklist** with
  direct links. Sign in (let Chrome save the password), then type **signed in**.
- Check each filled tab, fix anything you want, click **Submit**, then click **Mark as submitted** on the
  dashboard's "Ready to submit" page (or on the job's own page).

## If something goes wrong
- **GitHub says "Too many requests":** wait 15 minutes, or switch networks (your phone's hotspot), then try again.
- **The dashboard doesn't open:** double-click **Start Dashboard** in your JobGetter folder (on a Mac:
  **Start Dashboard.command**; if the Mac blocks it, right-click it, then choose **Open**). Then go to
  http://localhost:5050 in your browser.
- **Claude can't control Chrome:** make sure Chrome is open, the Claude extension is signed in, and the Chrome
  window isn't minimized.
- **Anything else:** tell Claude what you see, in your own words. It can fix JobGetter itself.
