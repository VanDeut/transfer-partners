# Automated Rate Syncing with GitHub Actions

This guide explains how to keep transfer rates up-to-date with Roame data.

**Recommended Approach**: Download Roame data manually and use comparison scripts (safer, more reliable)  
**Alternative**: Automated scraping with GitHub Actions (requires monitoring)

## 🎯 Recommended: Manual Download + Comparison

**This is the safest and most straightforward approach:**

### Workflow
1. **Download fresh data** from Roame's website (use their download button)
2. **Save to repo** as `roame-source-YYYY-MM-DD.csv`
3. **Run comparison** script to detect changes
4. **Apply updates** using `update_transfer.py`
5. **Commit** changes with full audit trail

### Steps

```bash
# 1. Download from https://roame.travel/transfer-partners-cheat-sheet
# Save as: roame-source-2026-09-20.csv

# 2. Compare with current data
python3 scripts/compare_roame.py roame-source-2026-09-20.csv

# 3. Script suggests update commands - run them:
python3 update_transfer.py "Chase" "United" 0.8

# 4. Validate
./validate.sh

# 5. Commit
git add transfer-partners.json roame-source-2026-09-20.csv
git commit -m "Sync with Roame data as of 2026-09-20"
```

### Advantages
✅ **No scraping** = no legal concerns  
✅ **Auditable** = you see exactly what Roame provided  
✅ **Reliable** = doesn't break if Roame changes their site  
✅ **Simple** = easy to troubleshoot  
✅ **Version controlled** = git history of all changes  

### Best Practice
- **Weekly**: Quick check of Roame for major changes
- **Monthly**: Full download and comparison
- **Set calendar reminder**: So you don't forget updates

---

## Alternative: Automated GitHub Actions Scraping

If you prefer automated daily updates, the GitHub Actions workflow automatically:
- Runs daily at 9 AM UTC
- Fetches the latest data from Roame Transfer Partners
- Compares with your current JSON
- Auto-commits any detected changes
- Creates issues if errors occur

## Setup Instructions

### 1. Push to GitHub

First, you need to push this repository to GitHub:

```bash
git remote add origin https://github.com/YOUR_ORG/transfer-partners.git
git push -u origin main
```

### 2. Enable GitHub Actions

1. Go to your GitHub repository
2. Click **Settings** → **Actions** → **General**
3. Enable "Allow all actions and reusable workflows"

### 3. Verify the Workflow File

The workflow file is already created at:
```
.github/workflows/sync-rates.yml
```

It's configured to run:
- ✅ **Automatically**: Daily at 9 AM UTC
- ✅ **Manually**: Via "Run workflow" button on Actions tab

### 4. Check Workflow Permissions (Important!)

For auto-commits, the workflow needs write access:

1. Go to **Settings** → **Actions** → **General**
2. Under "Workflow permissions":
   - ✅ Select "Read and write permissions"
   - ✅ Check "Allow GitHub Actions to create and approve pull requests"

## How It Works

### Daily Schedule

```yaml
schedule:
  - cron: '0 9 * * *'  # 9 AM UTC every day
```

To change the schedule time:
- Edit `.github/workflows/sync-rates.yml`
- Modify the `cron` value
- Reference: https://crontab.guru

### Workflow Steps

1. **Checkout**: Clone your repository
2. **Python Setup**: Install Python 3.11
3. **Dependencies**: Install required packages (requests, beautifulsoup4)
4. **Fetch & Sync**: Run the sync script
5. **Validate**: Check JSON validity
6. **Configure Git**: Set up bot credentials
7. **Commit**: Auto-commit if changes found
8. **Push**: Push to main branch
9. **Error Handling**: Create issue if workflow fails

## Manual Trigger

To run the sync manually:

1. Go to **Actions** tab in GitHub
2. Select **"Sync Transfer Rates from Roame"**
3. Click **Run workflow** → **Run workflow**

## Customization

### Change Sync Schedule

Edit `.github/workflows/sync-rates.yml`:

```yaml
schedule:
  - cron: '0 6 * * *'  # 6 AM UTC instead of 9 AM
```

### Change Commit Messages

Edit `.github/workflows/sync-rates.yml`:

```yaml
git commit -m "Custom message here"
```

### Change Error Handling

The workflow currently creates an issue on failure. To disable:

```yaml
# Comment out the "Create issue if errors" step in the workflow
```

### Add Slack Notifications

Add to `.github/workflows/sync-rates.yml` after the commit step:

```yaml
- name: Notify Slack
  if: steps.sync.outputs.changes_found == 'true'
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "Transfer rates updated from Roame",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "✅ Transfer rates synced\n${{ steps.sync.outputs.changes_summary }}"
            }
          }
        ]
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

## Important Notes ⚠️

### Web Scraping Limitations

The current sync script uses web scraping, which has limitations:

1. **Fragile**: If Roame changes their page structure, scraping may break
2. **Rate Limiting**: Roame may block frequent requests
3. **Complex Data**: Transfer rates table is complex (JavaScript-rendered content)

### Recommendations for Production

For reliable automation, consider these improvements:

#### Option 1: Roame API (Best)
If Roame provides an API, use that instead of scraping:
```python
response = requests.get('https://api.roame.travel/v1/transfer-rates')
rates = response.json()
```

#### Option 2: Browser Automation (Robust)
Use Selenium or Playwright for JavaScript-heavy pages:
```bash
pip install selenium
# or
pip install playwright
playwright install chromium
```

#### Option 3: Scheduled Notifications (Practical)
Instead of auto-updating, send daily digest:
1. Scrape Roame
2. Send digest email with changes
3. Manual verification before auto-commit

## Monitoring & Debugging

### View Workflow Runs

1. Go to **Actions** tab
2. Click **"Sync Transfer Rates from Roame"**
3. View all runs and their logs

### Common Issues

**Issue**: Workflow doesn't appear in Actions tab
- **Solution**: Make sure `.github/workflows/sync-rates.yml` is committed to `main` branch

**Issue**: "Permission denied" when pushing
- **Solution**: Go to Settings → Actions → General → Enable "Read and write permissions"

**Issue**: Script errors but workflow doesn't fail
- **Solution**: Errors are logged but workflow continues. Check logs in Actions tab.

**Issue**: Too many/too few commits
- **Solution**: Adjust the change detection logic in `scripts/sync_roame_rates.py`

### View Detailed Logs

1. Click a workflow run
2. Click **sync-rates** job
3. Expand **Fetch and sync rates** step
4. See detailed output

## Approval & Review Process (Alternative)

Instead of auto-committing, create pull requests for manual review:

Edit `.github/workflows/sync-rates.yml`:

```yaml
- name: Create Pull Request
  if: steps.sync.outputs.changes_found == 'true'
  uses: peter-evans/create-pull-request@v5
  with:
    commit-message: "Auto-update transfer rates from Roame"
    title: "📊 Transfer rates updated"
    body: |
      Automated sync from Roame Transfer Partners
      
      ${{ steps.sync.outputs.changes_summary }}
    branch: auto/roame-sync
    delete-branch: true
```

This creates a PR instead of auto-committing, allowing manual review before merge.

## Future Improvements

Planned enhancements:

- [ ] **Roame API Integration**: Use official API if available
- [ ] **Slack Notifications**: Notify team of changes
- [ ] **PR Review Mode**: Create PRs instead of auto-commits
- [ ] **Change Summary Comments**: Auto-comment on related issues
- [ ] **Comparison Report**: Generate detailed change reports
- [ ] **Email Digests**: Send daily digest to team
- [ ] **Webhook Support**: Integrate with other services

## Troubleshooting

### Workflow Disabled?

GitHub may auto-disable workflows if no commits for 60 days. To re-enable:
1. Go to Actions tab
2. Click "I understand my workflows..."
3. Click "Enable workflow"

### Rate Limiting from Roame?

Add delay between requests:
```python
time.sleep(5)  # Add 5 second delay
```

Edit `scripts/sync_roame_rates.py` to add delays.

### Large Commits in History?

If workflow commits are cluttering history, use:
```bash
git log --author="Transfer Partners Bot"  # View bot commits
```

To clean up (advanced):
```bash
git filter-branch --author-name "Transfer Partners Bot" --author-email "action@github.com" ...
```

## Support & Questions

For issues with the automation:

1. **Check workflow logs**: Actions tab → workflow run → logs
2. **Review error messages**: Look for specific error messages
3. **Test manually**: Run `python3 scripts/sync_roame_rates.py` locally
4. **Check Roame availability**: Verify https://roame.travel is accessible

---

**Last Updated**: 2026-09-13  
**Status**: ✅ Ready for Production
