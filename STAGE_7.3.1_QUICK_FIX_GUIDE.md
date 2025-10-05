# 🚀 Stage 7.3.1 - Quick Fix Guide for 401 Unauthorized

**Last Updated:** October 4, 2025  
**Status:** 🔴 Requires API Key Update

---

## 🎯 Problem Summary

The Notion Sanity Check is failing with **401 Unauthorized** because the current API key is invalid or expired.

```
❌ 401 Unauthorized: API token is invalid.
```

## ⚡ Quick Fix (3 Steps)

### Option A: Interactive Setup (Recommended)

```bash
# Step 1: Run the setup wizard
python3 scripts/setup_notion_api_key.py

# Step 2: Follow the prompts to enter your new API key
# Step 3: The wizard will validate and save the key automatically
```

The wizard will:
- ✅ Guide you through getting a new API key
- ✅ Validate the key before saving
- ✅ Update your `.env` file
- ✅ Optionally run the access audit

---

### Option B: Manual Setup

#### 1. Get Your API Key

Visit: **https://www.notion.so/my-integrations**

**Create or locate "AI Studio Master Automation":**
- If it exists: Click on it → Show secret → Copy key
- If not: Create new → Name it → Copy key

#### 2. Update .env File

Edit the `.env` file in your project root:

```bash
NOTION_API_KEY=secret_ntn_YOUR_NEW_KEY_HERE
```

#### 3. Share Databases

For **each** of these databases in Notion:
- CI Intelligence Reports
- MAGSASA-CARD ERP Roadmap  
- AI Studio Strategic Milestones

Do this:
1. Open database in Notion
2. Click `...` (top right)
3. Click "Add connections"
4. Select "AI Studio Master Automation"
5. Click "Connect"

#### 4. Verify

```bash
# Run the access audit
python3 scripts/audit_notion_access.py --json
```

---

## 🔍 Diagnostic Tools

### 1. Access Audit (Start Here)

**Purpose:** Diagnose API key and database access issues

```bash
# Basic audit
python3 scripts/audit_notion_access.py

# With JSON export
python3 scripts/audit_notion_access.py --json

# Auto-run sanity check if successful
python3 scripts/audit_notion_access.py --auto-fix
```

**What it checks:**
- ✅ Environment variables (required and optional)
- ✅ API key validity and authentication
- ✅ List of all accessible databases
- ✅ Access to 3 required databases
- ✅ Database properties and metadata

**Expected Output (Success):**

```
================================================================================
📊 DATABASE ACCESS SUMMARY
================================================================================

Database Name                       ID Prefix       Access     Workspace
--------------------------------------------------------------------------------
CI Intelligence Reports             2822dea9679a    ✅ Yes     AI Studio Workspace
MAGSASA-CARD ERP Roadmap            2822dea9679a    ✅ Yes     AI Studio Workspace
AI Studio Strategic Milestones      27d2dea9679a    ✅ Yes     AI Studio Workspace

================================================================================
✅ AUDIT PASSED
================================================================================
```

---

### 2. API Key Setup Wizard

**Purpose:** Interactive tool to configure your API key

```bash
python3 scripts/setup_notion_api_key.py
```

**Features:**
- 📝 Step-by-step instructions for getting your API key
- 🔍 Validates key format and connectivity
- 💾 Saves to .env file automatically
- ✅ Tests access to Notion API
- 🚀 Optional auto-run of access audit

---

### 3. Sanity Check

**Purpose:** Comprehensive validation of entire integration

```bash
# Full sanity check
python3 scripts/notion_cli.py sanity-check

# With dry-run sync simulation
python3 scripts/notion_cli.py sanity-check --dry-run

# Schema validation only
python3 scripts/notion_cli.py validate
```

**What it checks:**
- ✅ Environment variables
- ✅ API connectivity
- ✅ Database access
- ✅ Schema validation
- ✅ Dry-run sync simulation (optional)

---

## 📊 Access Audit Output Explained

### Status Indicators

| Icon | Meaning |
|------|---------|
| ✅ | Success - Working correctly |
| ❌ | Error - Requires action |
| ⚠️  | Warning - Optional issue |

### Common Error Messages

#### "API token is invalid"
```
❌ 401 Unauthorized: API token is invalid.
```
**Fix:** Get a new API key from notion.so/my-integrations

#### "Database not found"
```
❌ 404 Not Found - Database doesn't exist or integration not connected
```
**Fix:** Share the database with your integration using "Add connections"

#### "Integration has no access"
```
❌ 403 Forbidden: Integration has no access permissions
```
**Fix:** Check workspace permissions and share databases with integration

---

## 🔧 Remediation Checklist

Use this checklist to systematically fix the issue:

### Phase 1: API Key
- [ ] Visit https://www.notion.so/my-integrations
- [ ] Verify "AI Studio Master Automation" integration exists
- [ ] Get the API key (Show → Copy)
- [ ] Update NOTION_API_KEY in .env file
- [ ] Run: `python3 scripts/audit_notion_access.py`
- [ ] Verify: No 401 errors in output

### Phase 2: Database Access
- [ ] Open "CI Intelligence Reports" in Notion
- [ ] Add connection to "AI Studio Master Automation"
- [ ] Open "MAGSASA-CARD ERP Roadmap" in Notion
- [ ] Add connection to "AI Studio Master Automation"
- [ ] Open "AI Studio Strategic Milestones" in Notion
- [ ] Add connection to "AI Studio Master Automation"
- [ ] Run: `python3 scripts/audit_notion_access.py`
- [ ] Verify: All 3 databases show ✅ Yes in Access column

### Phase 3: Validation
- [ ] Run: `python3 scripts/notion_cli.py sanity-check`
- [ ] Verify: All checks pass
- [ ] Run: `python3 scripts/notion_cli.py sync --all --dry-run`
- [ ] Verify: Dry-run completes without errors

### Phase 4: Live Test
- [ ] Run: `python3 scripts/notion_cli.py sync --all`
- [ ] Check Notion databases for synced data
- [ ] Verify: Data appears correctly in Notion

---

## 🎯 Success Criteria

You'll know it's working when:

1. **Access Audit Passes:**
   ```
   ✅ AUDIT PASSED
   All required databases are accessible!
   ```

2. **Sanity Check Passes:**
   ```
   ✅ Overall Status: PASS
   🎉 All sanity checks passed! Notion integration is ready.
   ```

3. **Databases are Synced:**
   - CI reports appear in Notion
   - Roadmap milestones are updated
   - Strategic milestones are synced

---

## 📁 File Locations

| File | Purpose |
|------|---------|
| `.env` | Environment variables (API key, database IDs) |
| `env.template` | Template for .env file |
| `scripts/audit_notion_access.py` | Access diagnostic tool |
| `scripts/setup_notion_api_key.py` | Interactive API key setup |
| `scripts/notion_cli.py` | Unified CLI for all Notion operations |
| `scripts/sanity_check_notion.py` | Comprehensive sanity check |
| `reports/notion-access-audit.json` | Latest audit results (JSON) |
| `reports/sanity-check-*.json` | Sanity check results |

---

## 🆘 Troubleshooting

### Issue: "python-dotenv not installed"

```bash
pip install python-dotenv
```

### Issue: ".env file not found"

```bash
cp env.template .env
# Then edit .env with your API key
```

### Issue: "Database ID has query params"

Database IDs can include query parameters like `?v=...`  
This is fine - the scripts will handle it automatically.

Example:
```
MAGSASA_CI_DB_ID=2822dea9679a80f8bf45edf92dc2e199?v=2822dea9679a80e6a0de000cd1b90d7a
```

### Issue: Can't find database ID

1. Open the database in Notion
2. Click "Share" → "Copy link"
3. Extract the ID from the URL:
   ```
   https://notion.so/2822dea9679a80f8bf45edf92dc2e199?v=...
                      ^^^^^^^^^ This is your database ID ^^^^^^^^^
   ```

### Issue: Integration not showing in "Add connections"

- Make sure the integration is in the **same workspace** as the database
- Try refreshing the Notion page
- Check integration hasn't been deleted at notion.so/my-integrations

---

## 📞 Getting Help

### Export Diagnostic Information

```bash
# Export full audit results
python3 scripts/audit_notion_access.py --json

# Results saved to:
# reports/notion-access-audit.json
```

### Check Logs

```bash
# View recent sanity checks
ls -lt reports/sanity-check-*.json | head -5

# View specific sanity check
cat reports/sanity-check-20251004_170330.json | python3 -m json.tool
```

---

## 🚀 After Fix - Next Steps

Once the audit passes and sanity check succeeds:

### 1. Test Sync Operations

```bash
# Dry-run (no writes to Notion)
python3 scripts/notion_cli.py sync --all --dry-run

# Live sync
python3 scripts/notion_cli.py sync --all
```

### 2. Verify Data in Notion

- Open each database in Notion
- Check that CI reports are synced
- Verify roadmap milestones
- Confirm strategic milestones

### 3. Enable Automation

The GitHub Actions workflows are ready:
- `.github/workflows/notion-weekly-sync.yml` - Weekly sync
- `.github/workflows/notion-roadmap-sync.yml` - Roadmap sync

They will run automatically on schedule.

### 4. Monitor Results

```bash
# Check sync logs
ls -lt reports/

# View CI intelligence reports
cat reports/CI_WEEKLY_INTELLIGENCE.md
```

---

## 📚 Related Documentation

- `STAGE_7.3.1_ACCESS_FIX_SUMMARY.md` - Detailed fix summary
- `STAGE_7.3.1_COMPLETION_SUMMARY.md` - Stage completion report
- `STAGE_7.3.1_QUICK_START.md` - Quick start guide
- `NOTION_INTEGRATION_README.md` - Full integration documentation

---

## ✅ Quick Commands Reference

```bash
# 1. Setup API key (interactive)
python3 scripts/setup_notion_api_key.py

# 2. Run access audit
python3 scripts/audit_notion_access.py --json

# 3. Run sanity check
python3 scripts/notion_cli.py sanity-check

# 4. Test sync (dry-run)
python3 scripts/notion_cli.py sync --all --dry-run

# 5. Live sync
python3 scripts/notion_cli.py sync --all
```

---

**Remember:** The root cause is an invalid API key. Once you update it and share the databases with your integration, everything should work! 🎉

