# Weekly Automation Guide

Simple, reliable automation for keeping transfer rates current.

## 🎯 The Recommended Workflow

**Every week (takes 2 minutes):**

1. Download latest Roame data
2. Commit to GitHub
3. GitHub Actions auto-compares and updates
4. Done! ✨

## 📋 Your Weekly Routine

### Step 1: Download (1 minute)
```
1. Go to: https://roame.travel/transfer-partners-cheat-sheet
2. Click Download button
3. Save as: roame-source-2026-09-20.csv
   (Use today's date)
```

### Step 2: Commit to GitHub (1 minute)
```bash
git add roame-source-*.csv
git commit -m "Add Roame source data for weekly sync"
git push origin main
```

### Step 3: GitHub Does the Rest (Automatic)
- ✅ Workflow runs automatically
- ✅ Compares rates with current JSON
- ✅ Updates transfer-partners.json if changes found
- ✅ Auto-commits with descriptive message
- ✅ Your app gets fresh data

---

## ⏰ Workflow Schedule

The GitHub Actions workflow runs every **Monday at 9 AM UTC** (when you push the Roame file).

Change the time by editing `.github/workflows/weekly-sync.yml`:

```yaml
schedule:
  - cron: '0 9 * * 1'  # Change this
```

Examples:
```yaml
# Daily at 9 AM UTC
- cron: '0 9 * * *'

# Friday at 10 AM UTC
- cron: '0 10 * * 5'
```

Reference: https://crontab.guru

---

## 🔔 What You'll See

### Success (No Changes)
✅ Workflow runs  
✅ No rate changes detected  
✅ No new commits (that's fine!)  

### Success (With Changes)
✅ Workflow runs  
✅ Rate changes detected  
✅ Auto-commits to main  
✅ Your app gets updated data  

### Workflow Missing File
⚠️ GitHub creates an issue reminder  
→ Download and commit the file  
→ Workflow resumes  

---

## 🎯 Why This Approach?

| Aspect | Manual Download | Fully Automated |
|--------|---|---|
| Complexity | Simple | Complex |
| Reliability | 100% | Depends on automation |
| Time/week | 2 minutes | 0 minutes (but setup is hard) |
| Transparency | You see everything | Automated, less visibility |
| Troubleshooting | Easy | Complicated |

**The weekly manual approach gives you 95% of the benefit with 5% of the complexity.**

---

## 📊 View Workflow Status

In GitHub:
1. Go to **Actions** tab
2. Click **"Weekly Roame Sync"**
3. See all runs and their results

---

## ✅ Checklist: Week 1 Setup

- [ ] Push this repo to GitHub
- [ ] Go to **Settings** → **Actions** → **General**
- [ ] Enable "Read and write permissions"
- [ ] Download Roame CSV
- [ ] Commit to GitHub
- [ ] Check Actions tab - workflow runs!
- [ ] Done ✨

---

## 🔄 Recurring Weekly Task

**Every Monday (or whenever you want to check):**

```bash
# 1. Download from Roame

# 2. Commit
git add roame-source-*.csv
git commit -m "Add Roame data for weekly sync"
git push

# That's it!
```

---

## 🆘 Troubleshooting

**Q: Workflow didn't run?**  
A: Make sure you pushed the roame-source-*.csv file to GitHub

**Q: "No Roame file found" issue created?**  
A: Download and commit the file (2 minutes), then workflow resumes

**Q: Want to run it manually?**  
A: Go to Actions → Weekly Roame Sync → Run workflow

**Q: Want a different schedule?**  
A: Edit `.github/workflows/weekly-sync.yml` and change the cron time

---

## 🚀 That's It!

This is the complete, simple automation you need. Your app gets fresh transfer rates every week with minimal effort.

**Last Updated**: 2026-09-13
