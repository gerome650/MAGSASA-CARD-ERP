# Stage 7.3.1 - Notion Access Fix Summary

**Date:** October 4, 2025  
**Status:** 🔴 API Key Invalid - Action Required

## 🎯 Issue Identified

The Notion Access Audit has successfully identified the root cause of the 401 Unauthorized error:

```
❌ API token is invalid
```

## 📊 Audit Results

### Environment Variables Status
- ✅ All required environment variables are set in `.env`
- ✅ Database IDs are configured
- ⚠️  Optional variables (GITHUB_TOKEN, GITHUB_REPOSITORY) not set

### API Connectivity Status
- ❌ **NOTION_API_KEY is invalid or expired**
- The current key: `secret_ntn_123255786...Pbye` is not recognized by Notion

## 🔧 Required Actions

### Step 1: Verify Your Notion Integration

1. Go to: **https://www.notion.so/my-integrations**
2. Locate your integration (should be named "AI Studio Master Automation")
3. Check the integration status:
   - Is it active?
   - Has it been revoked?
   - When was it last used?

### Step 2: Get a Valid API Key

**Option A: If integration exists and is active**
1. Click on your integration
2. Go to "Secrets" section
3. Click "Show" to reveal the API key
4. Copy the complete key (starts with `secret_ntn_` or `secret_`)

**Option B: If integration doesn't exist or is inactive**
1. Create a new Internal Integration:
   - Click "+ New integration"
   - Name it: "AI Studio Master Automation"
   - Select your workspace
   - Leave capabilities as default (Read content, Update content, Insert content)
2. Click "Submit"
3. Copy the generated API key

### Step 3: Update Your .env File

1. Open `.env` in your project root
2. Update the NOTION_API_KEY line:
   ```bash
   NOTION_API_KEY=secret_ntn_YOUR_NEW_KEY_HERE
   ```
3. Save the file

### Step 4: Share Databases with Integration

Once you have a valid API key, you need to share each database with your integration:

**For each database:**
1. Open the database in Notion:
   - CI Intelligence Reports
   - MAGSASA-CARD ERP Roadmap
   - AI Studio Strategic Milestones

2. Click the "..." menu (top right)
3. Click "Add connections"
4. Search for "AI Studio Master Automation"
5. Click to connect

**Visual Guide:**
```
Database Page → ... → Add connections → AI Studio Master Automation → Connect
```

### Step 5: Re-run the Audit

After updating the API key and sharing databases:

```bash
python3 scripts/audit_notion_access.py --json
```

Expected output should show:
```
✅ Successfully connected to Notion API
✅ All required databases accessible
```

### Step 6: Run Sanity Check

Once the audit passes:

```bash
python3 scripts/notion_cli.py sanity-check
```

Or use the auto-fix flag to run this automatically:

```bash
python3 scripts/audit_notion_access.py --auto-fix
```

## 📋 Verification Checklist

- [ ] Verified integration exists at notion.so/my-integrations
- [ ] Got a valid API key from the integration
- [ ] Updated NOTION_API_KEY in .env file
- [ ] Shared all 3 databases with the integration
- [ ] Re-ran audit successfully
- [ ] Ran full sanity check
- [ ] Tested sync with --dry-run

## 🚀 Quick Fix Command

If you have the correct API key, run this one-liner to test:

```bash
# Test with temporary key (doesn't modify .env)
NOTION_API_KEY="your_key_here" python3 scripts/audit_notion_access.py
```

## 📊 Audit Tool Features

The new audit script provides:

✅ **Environment Verification**
- Validates all required variables
- Masks sensitive values in output
- Clear error messages for missing variables

✅ **API Connectivity Testing**
- Tests authentication with Notion API
- Detects 401, 403, 404, and other errors
- Provides specific remediation for each error type

✅ **Resource Discovery**
- Lists all accessible databases
- Lists all accessible pages
- Shows workspace information

✅ **Required Database Validation**
- Verifies access to each required database
- Shows database properties and last edited time
- Identifies specific access issues

✅ **Remediation Guidance**
- Step-by-step fixes for each error
- Links to Notion settings
- Clear action items

✅ **JSON Export**
- `--json` flag exports detailed audit results
- Saved to `reports/notion-access-audit.json`
- Useful for CI/CD and automation

✅ **Auto-Fix**
- `--auto-fix` flag runs sanity check if audit passes
- Streamlines the validation workflow

## 🔍 Diagnostic Commands

### Basic Audit
```bash
python3 scripts/audit_notion_access.py
```

### Audit with JSON Export
```bash
python3 scripts/audit_notion_access.py --json
```

### Audit with Auto Sanity Check
```bash
python3 scripts/audit_notion_access.py --auto-fix
```

### Manual Sanity Check
```bash
python3 scripts/notion_cli.py sanity-check
```

### Dry-Run Sync Test
```bash
python3 scripts/notion_cli.py sync --all --dry-run
```

## 📈 Success Criteria

The audit will pass when:

1. ✅ Valid NOTION_API_KEY is set
2. ✅ All 3 required database IDs are set
3. ✅ API connectivity test succeeds (no 401/403 errors)
4. ✅ All 3 required databases are accessible
5. ✅ Database schemas are valid

## 🆘 Common Issues

### Issue: "API token is invalid"
**Solution:** Get a new API key from notion.so/my-integrations and update .env

### Issue: "404 Not Found" for database
**Solution:** Share the database with your integration using "Add connections"

### Issue: "403 Forbidden"
**Solution:** Grant integration proper permissions in workspace settings

### Issue: Database ID is wrong
**Solution:** Get correct database ID from Notion (open database → Copy link → Extract ID)

## 📞 Support

If issues persist after following these steps:

1. Export audit results: `python3 scripts/audit_notion_access.py --json`
2. Check `reports/notion-access-audit.json` for detailed error information
3. Verify integration type is "Internal Integration" not "Public Integration"
4. Ensure you're in the correct Notion workspace

## 🎉 Next Steps After Success

Once the audit passes:

1. **Test Sync Operations**
   ```bash
   python3 scripts/notion_cli.py sync --all --dry-run
   ```

2. **Run Live Sync**
   ```bash
   python3 scripts/notion_cli.py sync --all
   ```

3. **Enable Automation**
   - GitHub Actions workflows are ready
   - Will run automatically on schedule
   - Check `.github/workflows/notion-*.yml`

4. **Monitor Results**
   - Check `reports/` directory for sync logs
   - Review Notion databases for synced data
   - Verify weekly automation runs

---

**Audit Tool Location:** `scripts/audit_notion_access.py`  
**Sanity Check Tool:** `scripts/notion_cli.py`  
**Environment File:** `.env` (copied from `env.template`)

