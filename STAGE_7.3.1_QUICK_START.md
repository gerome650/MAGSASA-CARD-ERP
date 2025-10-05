# Stage 7.3.1 Quick Start Guide
## Weekly Notion Sync - Setup & Testing

**⏱️ 5-Minute Setup** | **🎯 Production Ready**

---

## 🚀 Quick Setup (First Time)

### Step 1: Create Notion Integration (2 min)

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Name: "MAGSASA CI Automation"
4. Copy the **API Key** (starts with `secret_`)

### Step 2: Create/Share Databases (2 min)

Create or identify these databases in Notion:
- **CI Reports** - Weekly CI intelligence
- **Roadmap** - Project milestones
- **AI Studio Milestones** - Strategic goals

For each database:
1. Click "Share" (top right)
2. Invite your integration
3. Grant "Edit" permissions
4. Copy **Database ID** from URL

### Step 3: Configure Secrets (1 min)

#### For GitHub Actions:
Go to `Settings → Secrets → Actions → New secret`

Add these secrets:
```
NOTION_API_KEY=secret_...
MAGSASA_CI_DB_ID=...
MAGSASA_ROADMAP_DB_ID=...
AI_STUDIO_MILESTONES_DB_ID=...
```

#### For Local Development:
```bash
cp env.template .env
# Edit .env and add your keys
```

---

## ✅ Testing (Before Going Live)

### Test 1: Connection Test
```bash
python scripts/test_notion_connection.py
```
**Expected**: ✅ All tests passed!

### Test 2: Schema Validation
```bash
python scripts/validate_notion_schema.py
```
**Expected**: ✅ All database schemas validated successfully!

### Test 3: Dry-Run Sync
```bash
python scripts/notion_weekly_sync.py --all --dry-run
```
**Expected**: ✅ All 4 streams show "would sync"

### Test 4: Single Record Test
```bash
# Test CI sync only (creates 1 record)
python scripts/notion_weekly_sync.py --ci
```
**Expected**: ✅ 1 record created in CI Reports database

✅ **If all tests pass → Ready for production!**

---

## 🎮 Usage Commands

### Common Commands

```bash
# Dry-run (safe, no changes)
python scripts/notion_weekly_sync.py --all --dry-run

# Sync everything (live)
python scripts/notion_weekly_sync.py --all

# Sync specific streams
python scripts/notion_weekly_sync.py --ci
python scripts/notion_weekly_sync.py --roadmap
python scripts/notion_weekly_sync.py --milestones
python scripts/notion_weekly_sync.py --kpis

# With JSON logging (for CI)
python scripts/notion_weekly_sync.py --all --log-json

# Individual stream tests
python scripts/sync_ci_weekly.py --dry-run
python scripts/sync_roadmap_weekly.py --dry-run
python scripts/sync_milestones_weekly.py --dry-run
python scripts/sync_kpis_weekly.py --dry-run
```

### GitHub Actions

**Manual Run:**
1. Go to `Actions` → `Weekly Notion Sync`
2. Click "Run workflow"
3. Select options (dry-run recommended first)
4. Click "Run workflow"

**Automatic:**
- Runs every Monday at 09:00 UTC
- No action needed

---

## 🐛 Troubleshooting

### ❌ "NOTION_API_KEY is not set"
**Fix:** 
- Local: Check `.env` file exists
- GitHub: Verify secret in repository settings

### ❌ "Database access failed"
**Fix:**
1. Share database with integration in Notion
2. Verify database ID is correct
3. Check integration has "Edit" permissions

### ❌ "Schema validation failed"
**Fix:**
1. Run: `python scripts/validate_notion_schema.py`
2. Add missing properties in Notion
3. Follow property types shown in error

### ❌ "Rate limit exceeded"
**Fix:**
- Wait 1 minute, try again
- Reduce sync frequency
- Contact Notion for higher limits

---

## 📊 What Gets Synced

| Stream | Frequency | Records | Database |
|--------|-----------|---------|----------|
| CI Reports | Weekly | 1 per week | MAGSASA_CI_DB_ID |
| Roadmap | Weekly | Updates all | MAGSASA_ROADMAP_DB_ID |
| Milestones | Weekly | ~5 milestones | AI_STUDIO_MILESTONES_DB_ID |
| KPIs | Weekly | 1 summary | MAGSASA_CI_DB_ID |

---

## 🎯 Success Checklist

- [ ] Notion integration created
- [ ] Databases created/identified
- [ ] Databases shared with integration
- [ ] GitHub secrets configured
- [ ] Connection test passed
- [ ] Schema validation passed
- [ ] Dry-run test passed
- [ ] Single record test passed
- [ ] Workflow enabled
- [ ] First manual run completed
- [ ] Waiting for first scheduled run

---

## 📚 Full Documentation

For detailed information:
- **Usage Guide**: [docs/NOTION_WEEKLY_SYNC.md](docs/NOTION_WEEKLY_SYNC.md)
- **Completion Summary**: [STAGE_7.3.1_COMPLETION_SUMMARY.md](STAGE_7.3.1_COMPLETION_SUMMARY.md)
- **Notion Client**: [utils/notion_client.py](utils/notion_client.py)

---

## 🆘 Need Help?

1. Check [docs/NOTION_WEEKLY_SYNC.md](docs/NOTION_WEEKLY_SYNC.md) troubleshooting section
2. Run diagnostics: `python scripts/test_notion_connection.py`
3. Check workflow logs in GitHub Actions
4. Review sync logs: `ls -la reports/notion-weekly-sync-*.json`

---

**Last Updated**: 2025-10-04  
**Stage**: 7.3.1 - Weekly Notion Sync  
**Status**: ✅ Production Ready


