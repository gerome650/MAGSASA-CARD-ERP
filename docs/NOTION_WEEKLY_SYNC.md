# Stage 7.3.1: Weekly Notion Sync

Automated weekly synchronization of project intelligence to Notion databases.

## 📋 Overview

The Weekly Notion Sync system automatically syncs project data to Notion every Monday at 09:00 UTC:

1. **CI Intelligence Reports** → CI Reports Database
2. **Roadmap Milestones** → Roadmap Database  
3. **AI Studio Strategic Milestones** → Milestones Database
4. **Project KPIs & Metrics** → Dashboard Properties

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  GitHub Actions Workflow                     │
│              (notion-weekly-sync.yml)                        │
│  Triggers: Every Monday 09:00 UTC + Manual Dispatch         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           Master Orchestrator (notion_weekly_sync.py)        │
│  • Coordinates all sync streams                             │
│  • Aggregates results                                       │
│  • Writes summary to Control Center                         │
└────────┬───────────┬────────────┬──────────────┬────────────┘
         │           │            │              │
         ▼           ▼            ▼              ▼
    ┌────────┐ ┌─────────┐ ┌──────────┐ ┌─────────────┐
    │   CI   │ │Roadmap  │ │Milestones│ │    KPIs     │
    │  Sync  │ │  Sync   │ │   Sync   │ │    Sync     │
    └────────┘ └─────────┘ └──────────┘ └─────────────┘
         │           │            │              │
         ▼           ▼            ▼              ▼
    ┌────────────────────────────────────────────────────┐
    │              Notion Databases                       │
    │  • MAGSASA CI Reports DB                           │
    │  • MAGSASA Roadmap DB                              │
    │  • AI Studio Milestones DB                         │
    └────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

1. **Notion API Key**: Create an integration at [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. **Database Access**: Share target databases with your Notion integration
3. **GitHub Secrets**: Configure secrets in repository settings

### Setup GitHub Secrets

Go to: `Settings → Secrets and variables → Actions → New repository secret`

Add the following secrets:

| Secret Name | Description | Required |
|-------------|-------------|----------|
| `NOTION_API_KEY` | Notion integration API key | ✅ Yes |
| `MAGSASA_CI_DB_ID` | CI Reports database ID | ✅ Yes |
| `MAGSASA_ROADMAP_DB_ID` | Roadmap database ID | ✅ Yes |
| `AI_STUDIO_MILESTONES_DB_ID` | Milestones database ID | ✅ Yes |
| `CONTROL_CENTER_PAGE_ID` | Control Center page ID | ⚪ Optional |
| `GITHUB_TOKEN` | GitHub PAT for issue creation | ⚪ Optional |

### Finding Database IDs

1. Open your database in Notion
2. Click "Share" → Copy link
3. Extract the ID from the URL:
   ```
   https://notion.so/workspace/DATABASE_ID?v=...
                            ^^^^^^^^^^^^^^^^
   ```

### Local Setup

1. Copy environment template:
   ```bash
   cp env.template .env
   ```

2. Fill in your credentials in `.env`:
   ```bash
   NOTION_API_KEY=secret_...
   MAGSASA_CI_DB_ID=...
   MAGSASA_ROADMAP_DB_ID=...
   AI_STUDIO_MILESTONES_DB_ID=...
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## 📖 Usage

### Automated Weekly Sync (GitHub Actions)

The workflow runs automatically every Monday at 09:00 UTC.

**View runs**: Go to `Actions` → `Weekly Notion Sync (Stage 7.3.1)`

### Manual Execution

#### Via GitHub UI

1. Go to `Actions` → `Weekly Notion Sync (Stage 7.3.1)`
2. Click "Run workflow"
3. Select options:
   - **Dry run**: `true` (test without writes) or `false` (live sync)
   - **Sync target**: `all`, `ci`, `roadmap`, `milestones`, or `kpis`
4. Click "Run workflow"

#### Via Local Command Line

**Sync everything (dry-run):**
```bash
python scripts/notion_weekly_sync.py --all --dry-run
```

**Sync everything (live):**
```bash
python scripts/notion_weekly_sync.py --all
```

**Sync specific streams:**
```bash
# CI reports only
python scripts/notion_weekly_sync.py --ci

# Roadmap and milestones
python scripts/notion_weekly_sync.py --roadmap --milestones

# KPIs only
python scripts/notion_weekly_sync.py --kpis
```

**With JSON logging (for CI/CD):**
```bash
python scripts/notion_weekly_sync.py --all --log-json
```

### Individual Sync Scripts

Each stream can be synced independently:

```bash
# CI Intelligence
python scripts/sync_ci_weekly.py --dry-run

# Roadmap
python scripts/sync_roadmap_weekly.py --dry-run

# Milestones
python scripts/sync_milestones_weekly.py --dry-run

# KPIs
python scripts/sync_kpis_weekly.py --dry-run
```

## 🔍 Schema Validation

Validate database schemas before syncing:

```bash
python scripts/validate_notion_schema.py
```

**What it checks:**
- Required properties exist
- Property types match expectations
- Database accessibility

**Sample output:**
```
🔍 Validating Notion Database Schemas
======================================================================

🔍 Validating CI Reports Database...
  ✅ 'Name' (title)
  ✅ 'Week Of' (date)
  ✅ 'Workflows Pass Rate' (number)
  ...
  ✅ All required properties present and correct

🔍 Validating Roadmap Database...
  ✅ All required properties present and correct

🔍 Validating AI Studio Milestones Database...
  ✅ All required properties present and correct

======================================================================
✅ All database schemas validated successfully!
```

## 📊 Database Schemas

### CI Reports Database

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| Name | Title | ✅ | Report name (e.g., "CI Report - Week of 2025-10-04") |
| Week Of | Date | ✅ | Monday of the reporting week |
| Workflows Pass Rate | Number | ✅ | CI workflow pass rate (%) |
| Auto-Fix Success Rate | Number | ✅ | Auto-fix success rate (%) |
| Avg MTTR (minutes) | Number | ✅ | Average Mean Time To Repair |
| Total Runs | Number | ⚪ | Total workflow runs |
| Failed Runs | Number | ⚪ | Failed workflow runs |
| Top Failures | Rich Text | ✅ | List of top failure patterns |
| Recommendations | Rich Text | ✅ | Actionable recommendations |
| Status | Select | ✅ | "Active" or "Archived" |
| Type | Select | ✅ | "CI Report" or "KPI Summary" |

### Roadmap Database

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| Name | Title | ✅ | Milestone name |
| Status | Select | ✅ | Not Started, Planning, In Progress, Testing, Completed, Blocked |
| Target Date | Date | ✅ | Planned completion date |
| Progress | Number | ✅ | Completion percentage (0-100) |
| Next Action | Rich Text | ✅ | Next action item |
| Risk Level | Select | ✅ | Low, Medium, High |
| Drift (days) | Number | ⚪ | Days behind schedule |

### AI Studio Milestones Database

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| Stage Name | Title | ✅ | Milestone stage name |
| Target Date | Date | ✅ | Planned completion date |
| Status | Select | ✅ | Not Started, Planning, In Progress, Testing, Completed |
| Description | Rich Text | ⚪ | Milestone description |
| Progress | Number | ⚪ | Completion percentage |

## 🔧 Configuration

### Adjusting Sync Schedule

Edit `.github/workflows/notion-weekly-sync.yml`:

```yaml
on:
  schedule:
    - cron: "0 9 * * 1"  # Monday 09:00 UTC
```

**Common schedules:**
- `0 9 * * 1` - Monday 09:00 UTC
- `0 0 * * 1` - Monday 00:00 UTC
- `0 12 * * 1,3,5` - Mon/Wed/Fri 12:00 UTC
- `0 18 * * *` - Every day 18:00 UTC

Use [crontab.guru](https://crontab.guru) to create custom schedules.

### Dry-Run Mode

Dry-run mode simulates the sync without making any changes to Notion:

```bash
# Local
python scripts/notion_weekly_sync.py --all --dry-run

# GitHub Actions: Set dry_run input to "true"
```

**Use dry-run for:**
- Testing configuration changes
- Validating credentials
- Previewing sync behavior
- Debugging issues

## 🐛 Troubleshooting

### Schema Validation Failures

**Problem**: Schema validation fails with missing properties

**Solution**:
1. Run validation to see what's missing:
   ```bash
   python scripts/validate_notion_schema.py
   ```

2. Add missing properties in Notion:
   - Go to database
   - Click "..." → "Customize"
   - Add properties matching the schema

3. Re-validate:
   ```bash
   python scripts/validate_notion_schema.py
   ```

### API Key Errors

**Problem**: `❌ NOTION_API_KEY is not set`

**Solutions**:
- **Local**: Ensure `.env` file exists with valid `NOTION_API_KEY`
- **GitHub**: Verify secret is set in repository settings
- **Key format**: Should start with `secret_`

**Problem**: `❌ Notion API error: unauthorized`

**Solutions**:
- Regenerate API key in Notion
- Update secret in GitHub and `.env`
- Verify integration has database access

### Database Access Errors

**Problem**: `❌ Database access failed`

**Solutions**:
1. Share database with integration:
   - Open database in Notion
   - Click "Share"
   - Invite your integration
   - Grant "Edit" permissions

2. Verify database ID:
   - Copy link from Notion
   - Extract ID from URL
   - Update env var/secret

3. Test connection:
   ```bash
   python scripts/test_notion_connection.py
   ```

### Sync Failures

**Problem**: Workflow fails with timeout

**Solutions**:
- Check Notion API status: [status.notion.so](https://status.notion.so)
- Reduce sync frequency if hitting rate limits
- Contact Notion support for rate limit increases

**Problem**: Some records not syncing

**Solutions**:
- Check logs in workflow artifacts
- Verify data format matches schema
- Test individual sync scripts:
  ```bash
  python scripts/sync_ci_weekly.py --dry-run
  ```

### Issue Creation

**Problem**: Issues not created on failure

**Solution**: Ensure `GITHUB_TOKEN` secret is set with `repo` scope

### Log Access

**Accessing logs:**
1. Go to `Actions` → Select failed workflow run
2. Click on job name
3. Expand failed step to view logs
4. Download artifacts for JSON logs

**Local logs:**
```bash
ls -la reports/notion-weekly-sync-*.json
```

## 🔄 Recovery Procedures

### Manual Sync After Failure

1. Check workflow logs for error
2. Fix underlying issue (schema, credentials, etc.)
3. Re-run workflow:
   - Go to Actions → Failed run
   - Click "Re-run jobs" → "Re-run failed jobs"

### Backfill Missing Weeks

If multiple weeks were missed:

```bash
# Sync current week
python scripts/notion_weekly_sync.py --all

# For historical data, manually adjust dates in sync scripts
# or create custom backfill script
```

### Reset Sync State

To clear all synced data and start fresh:

1. **Backup**: Export databases from Notion
2. **Clear**: Delete all synced pages (keep schema)
3. **Re-sync**: Run sync to repopulate:
   ```bash
   python scripts/notion_weekly_sync.py --all
   ```

## 📈 Monitoring

### Success Metrics

- ✅ All 4 streams sync successfully
- ✅ Schema validation passes
- ✅ No API rate limit errors
- ✅ Logs uploaded to artifacts

### Key Indicators

Monitor these in Notion:
- **CI Pass Rate**: Should trend >85%
- **Auto-Fix Success**: Should trend >75%
- **At-Risk Items**: Should trend downward
- **Completion %**: Should trend toward 100%

### Alert Triggers

Issues are auto-created when:
- Scheduled sync fails
- Schema validation fails
- API errors occur

Check: `Issues` tab → Filter by `notion-sync` label

## 🔐 Security Best Practices

1. **API Key Rotation**
   - Rotate Notion API keys quarterly
   - Update secrets immediately after rotation
   - Test sync after rotation

2. **Least Privilege**
   - Integration only needs access to specific databases
   - Don't share entire workspace

3. **Secret Management**
   - Never commit `.env` files
   - Use GitHub encrypted secrets
   - Audit secret access regularly

4. **Access Logs**
   - Review Notion integration activity
   - Monitor API usage in Notion settings

## 📚 Additional Resources

### Related Documentation
- [Notion API Documentation](https://developers.notion.com)
- [GitHub Actions Documentation](https://docs.github.com/actions)
- [Notion Client Utility](../utils/notion_client.py)

### Internal Links
- [AI Studio Notion Setup](../AI_STUDIO_NOTION_SETUP_COMPLETE.md)
- [Notion Integration README](../NOTION_INTEGRATION_README.md)
- [Stage 7.3.2 Completion](../STAGE_7.3.2_COMPLETION_SUMMARY.md)

### Support

**Issues?** Create a GitHub issue with:
- Error messages
- Workflow run link
- Relevant log excerpts
- Environment details

**Questions?** Check existing issues or documentation first.

---

## 📝 Changelog

### v1.0.0 (2025-10-04)
- ✅ Initial implementation
- ✅ CI, Roadmap, Milestones, KPIs sync
- ✅ Schema validation
- ✅ Dry-run support
- ✅ Automated issue creation
- ✅ Comprehensive documentation

---

**Last Updated**: 2025-10-04  
**Maintainer**: AI Studio Team  
**Stage**: 7.3.1 - Weekly Notion Sync


