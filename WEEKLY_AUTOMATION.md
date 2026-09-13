# Weekly Automated Sync with Roame

Automated weekly workflow that checks for Roame updates and auto-commits changes.

## 🎯 How It Works

### Workflow: Every Monday at 9 AM UTC

1. **GitHub Actions triggers** automatically every Monday
2. **Checks for Roame data file** (`roame-source-*.csv`)
3. **If file exists**: Runs comparison and auto-commits changes
4. **If file missing**: Creates GitHub issue reminding you to download
5. **Reports status** in workflow summary and GitHub

### The Hybrid Approach

```
┌─────────────────────────────────────┐
│ GitHub Actions Workflow (Weekly)    │
│ Runs Every Monday 9 AM UTC          │
└─────────────────────────────────────┘
           ↓
    ┌──────────────────┐
    │ Check for        │
    │ roame-source file│
    └──────────────────┘
           ↓
    ┌──────────────────────────────────┐
    │ File found?                       │
    └──────────────────────────────────┘
        /                           \
    YES/                             \NO
    ↓                                 ↓
┌─────────────────┐          ┌──────────────────┐
│ Run compare     │          │ Create issue     │
│ Auto-update if  │          │ "Please download │
│ changes found   │          │  Roame data"     │
│ Auto-commit     │          │                  │
└─────────────────┘          └──────────────────┘
    ↓
    If changes: Commit & push
    If no changes: Skip
```

## 📋 Setup (One-Time)

### 1. Ensure write permissions enabled

Go to GitHub repo **Settings** → **Actions** → **General**:
- ✅ "Read and write permissions"
- ✅ "Allow GitHub Actions to create and approve pull requests"

### 2. That's it!

The workflow is ready to go. Commits happen automatically if you provide the Roame file.

## 🔄 Weekly Process

### You Only Need To Do This Once Per Week:

**Every week, at your preferred time:**

1. Visit https://roame.travel/transfer-partners-cheat-sheet
2. Click the **Download** button
3. Save as: `roame-source-YYYY-MM-DD.csv`
4. Commit to GitHub:
   ```bash
   git add roame-source-2026-09-20.csv
   git commit -m "Add Roame source data for weekly sync"
   git push
   ```

**Then the workflow automatically:**
- ✅ Detects the new file
- ✅ Runs comparison
- ✅ Updates transfer-partners.json if changes found
- ✅ Auto-commits the updates
- ✅ Sends you a notification (if configured)

## 🔔 Notifications

### Option 1: Email Notifications (Built-in)

GitHub automatically emails you when workflow runs complete:
1. Go to **Settings** → **Notifications**
2. Configure when you want workflow notifications

### Option 2: GitHub Issues (Automatic)

If the workflow can't find the Roame file, it creates a GitHub issue reminding you to download.

### Option 3: Slack Notifications (Optional)

Add to `.github/workflows/weekly-sync.yml`:

```yaml
- name: Notify Slack on changes
  if: steps.compare.outputs.changes_found == 'true'
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "✅ Transfer rates updated from Roame",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "Transfer rates synced successfully"
            }
          }
        ]
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

## ⏰ Change Schedule

Want to run on a different day or time?

Edit `.github/workflows/weekly-sync.yml`:

```yaml
schedule:
  - cron: '0 9 * * 1'  # Change the cron expression
```

Examples:
```yaml
# Every Monday 9 AM UTC (default)
- cron: '0 9 * * 1'

# Every Friday 10 AM UTC
- cron: '0 10 * * 5'

# Twice a week (Monday & Thursday at 9 AM UTC)
- cron: '0 9 * * 1,4'

# Daily at 9 AM UTC
- cron: '0 9 * * *'
```

Reference: https://crontab.guru

## 🚀 Manual Trigger

You don't have to wait for Monday. Manually trigger anytime:

1. Go to **Actions** tab
2. Select **"Weekly Roame Sync"**
3. Click **Run workflow**

## 📊 Monitoring

### View workflow runs:

1. Go to **Actions** tab
2. Click **"Weekly Roame Sync"**
3. See all runs and their results

### Common statuses:

- ✅ **Success (no changes)**: No new rates detected
- ✅ **Success (updated)**: Changes detected and committed
- ⚠️ **Roame file not found**: Manual download needed (issue created)
- ❌ **Failed**: Check logs for errors

## 🔍 Workflow Logs

To see what happened during a run:

1. Go to **Actions** → **Weekly Roame Sync**
2. Click a specific run
3. Click **sync-roame** job
4. Expand steps to see details

### Key sections to check:

- **Download Roame data**: Whether page is accessible
- **Check for manual Roame uploads**: Found the file?
- **Run comparison if Roame file exists**: What changed?
- **Commit changes if found**: Was anything updated?

## ⚙️ Customization

### Disable automatic issue creation

Remove or comment out the "Create issue if manual download needed" step in the workflow.

### Skip comparison if no changes in N days

Add logic to skip checks if file is recent:

```yaml
- name: Check file age
  run: |
    file_date=$(stat -f %Sm -t "%Y-%m-%d" roame-source-*.csv | head -1)
    days_old=$(( ($(date +%s) - $(date -d "$file_date" +%s)) / 86400 ))
    echo "File is $days_old days old"
```

### Store artifacts for audit trail

Add to workflow to keep all comparison outputs:

```yaml
- name: Upload comparison report
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: comparison-reports
    path: comparison_output.txt
    retention-days: 30
```

## 🔐 Security Notes

- Bot commits are marked as automated
- No credentials are stored or exposed
- Downloaded files are committed to git (audit trail)
- All changes go through git history (reversible)

## Troubleshooting

### "Roame file not found" every week

**Solution**: You need to download and commit the file weekly

```bash
# Download from https://roame.travel/transfer-partners-cheat-sheet
# Then:
git add roame-source-YYYY-MM-DD.csv
git commit -m "Add Roame data for weekly sync"
git push
```

### Workflow doesn't run on Monday

**Check**:
1. Repository has at least one commit (it does ✅)
2. Workflows are enabled in Settings → Actions
3. Branch `main` exists

**Note**: Scheduled workflows only run if repo has commits in past 60 days

### Changes not being committed

**Check**:
1. Write permissions enabled in Settings → Actions → General
2. Workflow has permission to push: Check workflow logs
3. Git config is set correctly in workflow

## Future Improvements

Planned enhancements:
- [ ] Direct Roame API integration (if they provide one)
- [ ] Auto-detect Roame CSV download link
- [ ] Slack notifications for changes
- [ ] Detailed changelog in commits
- [ ] Diff reports in GitHub comments

## Example: Weekly Routine

**Every Monday morning:**

1. Check GitHub for workflow status (automated)
2. If issue created: Download Roame file
3. Commit file: `git push`
4. Workflow auto-runs, auto-updates if needed
5. Done! ✅

**Time investment**: ~2 minutes once per week

## FAQ

**Q: Do I have to do this weekly?**  
A: Only if you want to stay current. Monthly or quarterly also works fine.

**Q: What if I don't download the file?**  
A: Workflow creates a friendly reminder issue. No data is lost.

**Q: Can this fully automate without me downloading?**  
A: Not currently (Roame doesn't provide an API or direct download URL). But this approach is the best balance of automation + safety.

**Q: What if Roame changes their page structure?**  
A: The workflow will still detect this and create an issue. You can fix it or contact Roame.

---

**Last Updated**: 2026-09-13  
**Status**: ✅ Ready to Use
