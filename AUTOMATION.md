# Bi-Monthly Automation

Completely hands-off transfer rate updates every 2 months.

## 🎯 **What You Need to Do**

**Nothing.** The automation handles everything.

GitHub Actions runs automatically on:
- **September 30**
- **November 30**
- **January 31**
- **March 31**
- **May 31**
- **July 31**

---

## 🤖 **What Happens Automatically**

1. ✅ Fetches the latest Roame Transfer Partners page
2. ✅ Extracts transfer partner names and ratios
3. ✅ Detects any changes from the last sync
4. ✅ Updates `transfer-partners.json` if rates changed
5. ✅ Auto-commits to GitHub
6. ✅ Your app gets fresh data

---

## 📊 **Schedule**

- **Frequency**: Every 2 months
- **Timing**: Last day of the month at midnight UTC
- **Duration**: ~2 minutes

```
September 30 → November 30 → January 31 → March 31 → May 31 → July 31
```

Then it repeats.

---

## 🔍 **How It Works**

The workflow:
1. Checks the Roame website legally (verified by robots.txt)
2. Parses the transfer partners table
3. Compares with your current data
4. Updates only if rates changed
5. Commits with a clear message

**No manual work required.**

---

## ✅ **Verify It's Working**

Go to **Actions** tab on GitHub:
- Click **"Bi-Monthly Roame Sync"**
- See all runs and their status
- Each run shows what changed

---

## 🆘 **Manual Trigger**

Want to run it now instead of waiting?

1. Go to **Actions** tab
2. Click **"Bi-Monthly Roame Sync"**
3. Click **"Run workflow"**

---

## 📝 **What's in the JSON**

The workflow updates:
- Transfer partner names
- Exchange ratios (e.g., 1.0, 0.8, 1.25)
- Last updated timestamp

It does NOT include:
- Promotional bonuses (those are temporary)
- Transfer speeds
- Program descriptions

This keeps the data clean and focused on core rate information.

---

## 🚀 **Your App**

Your app fetches from:
```
https://raw.githubusercontent.com/YOUR_ORG/transfer-partners/main/transfer-partners.json
```

It gets:
- ✅ Fresh rates every 2 months
- ✅ Historical version tracking (git history)
- ✅ Automatic verification (validation script runs)

---

## 💡 **Why Every 2 Months?**

- ✅ Transfer rates don't change constantly
- ✅ Respectful of Roame's servers
- ✅ Reduces unnecessary commits
- ✅ Still keeps data reasonably fresh
- ✅ Scheduled far enough apart to avoid looking like a bot

---

**That's it. Your transfer rates stay current with zero effort.** 🎉

Last Updated: 2026-09-13
