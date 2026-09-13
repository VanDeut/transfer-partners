# Fully Automated Download & Sync

Set it and forget it! This workflow completely automates the download and update process.

## 🎯 How It Works

Every Monday at 8 AM UTC, GitHub Actions automatically:

1. ✅ **Downloads** the latest Roame CSV using browser automation
2. ✅ **Saves** it with today's date (`roame-source-2026-09-20.csv`)
3. ✅ **Compares** with your current data
4. ✅ **Updates** `transfer-partners.json` if rates changed
5. ✅ **Commits & pushes** everything to GitHub
6. ✅ Your app gets fresh data automatically

**Zero manual work required!**

## ⚙️ Setup (One-Time)

### Step 1: Ensure write permissions
Go to GitHub repo **Settings** → **Actions** → **General**:
- ✅ "Read and write permissions"
- ✅ "Allow GitHub Actions to create and approve pull requests"

### Step 2: Done!
The workflow is already set up and running.

## 🚀 What Happens Automatically

```
Every Monday, 8 AM UTC:
   ↓
🌐 Browser automation visits Roame
   ↓
📥 Clicks download button, saves CSV
   ↓
🔍 Compares rates with transfer-partners.json
   ↓
📊 Detects changes (if any)
   ↓
✏️ Auto-updates JSON
   ↓
💾 Commits & pushes to GitHub
   ↓
📱 Your app fetches updated file via:
   https://raw.githubusercontent.com/YOUR_ORG/transfer-partners/main/transfer-partners.json
   ↓
✨ Users see latest rates automatically!
```

## 📋 What You Need to Do

**Absolutely nothing!** 🎉

The workflow handles everything:
- ✅ Downloading
- ✅ Comparing
- ✅ Updating
- ✅ Committing
- ✅ Pushing

Your app automatically gets updates every week.

## 🔔 Notifications

You'll get notified if:
- ✅ **Download succeeds** → Workflow completes silently (no issue)
- ⚠️ **Download fails** → GitHub creates an issue with fallback instructions

If the workflow fails (rare), you'll get a notification and instructions to manually download once.

## 🕐 Customize Schedule

Want to run on a different day or time?

Edit `.github/workflows/auto-download-sync.yml`:

```yaml
schedule:
  - cron: '0 8 * * 1'  # Change this
```

Examples:
```yaml
# Daily at 9 AM UTC
- cron: '0 9 * * *'

# Every Friday at 10 AM UTC
- cron: '0 10 * * 5'

# Twice a week (Monday & Thursday)
- cron: '0 8 * * 1,4'
```

Reference: https://crontab.guru

## ⚡ Manual Trigger

You can also manually trigger anytime:
1. Go to **Actions** tab
2. Click **"Auto Download & Sync Roame"**
3. Click **Run workflow**

## 📊 View Results

Check what happened:
1. Go to **Actions** tab
2. Click **"Auto Download & Sync Roame"**
3. Click a run to see details

Look for:
- ✅ Download succeeded
- ✅ Changes detected (or "No changes")
- ✅ Committed to main

## ⚠️ If Download Fails

This is rare, but if it happens:

1. GitHub creates an issue with **fallback instructions**
2. You manually download once (2 minutes)
3. Commit to GitHub
4. Workflow resumes auto-downloading

**Why it might fail:**
- Roame changed their page structure
- Anti-bot protection triggered
- Network issue

**How to fix:**
- Roame changed something → Report to us (we update the script)
- Anti-bot protection → Wait a day and retry
- Network issue → Workflow automatically retries next Monday

## 🔐 How It Works (Technical)

The workflow uses:
- **Playwright** - Browser automation library
- **Chromium** - Headless browser
- **Python** - Automation script

Steps:
1. Launch headless Chromium browser
2. Navigate to Roame page
3. Find and click download button
4. Save CSV with date stamp
5. Run comparison script
6. Apply updates
7. Commit and push

## 🆘 Troubleshooting

**Q: Workflow runs but no file downloaded**  
A: Roame probably changed their page. GitHub creates an issue with manual fallback steps.

**Q: I see a GitHub issue "Auto-Download Failed"**  
A: Download failed. Follow the manual steps in the issue, then workflow resumes.

**Q: When does the sync run?**  
A: Every Monday at 8 AM UTC (configurable in `.github/workflows/auto-download-sync.yml`)

**Q: Can I run it more frequently?**  
A: Yes, change `cron: '0 8 * * 1'` to run daily or multiple times per week.

**Q: What if Roame is down for maintenance?**  
A: Workflow creates an issue. It'll retry next Monday. Meanwhile, your app uses cached data.

**Q: Does this cost anything?**  
A: No, GitHub Actions are free for public repos and includes 2000 minutes/month for private repos.

## ✨ Benefits Over Manual

| Aspect | Manual | Fully Automated |
|--------|--------|-----------------|
| Time per week | 5 minutes | 0 minutes |
| Frequency | Weekly | Weekly (or more) |
| Consistency | Manual mistakes possible | Always on time |
| Reliability | Depends on you | Automated |
| Audit trail | Git commits | Git commits |
| User experience | Updates weekly | Always fresh |

## 🎯 Recommended Schedule

**Most people use:** Monday 8 AM UTC
- Covers updates from weekend announcements
- Happens before work hours
- Regular, predictable

**But you can customize:**
- **Daily**: If you want latest possible rates
- **Twice weekly**: Monday & Thursday
- **Monthly**: If rate changes are rare

## 📱 App Side

Your app is already set up perfectly:
```
Remote URL: https://raw.githubusercontent.com/YOUR_ORG/transfer-partners/main/transfer-partners.json
Cache: 24 hours
Fallback: Bundled JSON
```

The app automatically gets updates every time the file changes on GitHub.

## 🚀 Getting Started

1. ✅ Workflow is already set up
2. ✅ Runs automatically every Monday 8 AM UTC
3. ✅ You don't need to do anything
4. ✅ Your app gets fresh data automatically

**That's it!** 🎉

---

## Advanced: If Roame Changes

If Roame changes their page structure and the workflow fails:

1. You get a GitHub issue with fallback instructions
2. Download manually once (2 minutes)
3. We update the automation script
4. Resume fully automated syncing

See `AUTOMATION.md` for how to manually download as fallback.

---

**Last Updated**: 2026-09-13  
**Status**: ✅ Ready to Deploy
