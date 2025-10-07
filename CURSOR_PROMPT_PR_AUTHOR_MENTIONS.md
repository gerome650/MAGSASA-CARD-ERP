# 🎯 Cursor Prompt: Dynamic PR Author Mentions for Failed CI Checks

## 📋 Feature Request

Enhance the existing PR Auto-Commenter system (`scripts/release_dashboard/pr_commenter.py`) to **automatically mention/tag the PR author** (`@username`) when CI checks fail. This creates immediate accountability and notification for the person responsible for fixing the issues.

---

## 🎯 Core Requirements

### 1. **Automatic Author Detection**
- Detect the PR author's GitHub username from the PR context
- Support both PR events and workflow run events
- Handle edge cases: bots, co-authors, automated PRs

### 2. **Smart Mention Strategy**
Implement tiered mention logic based on failure severity:

| Failure Severity | Mention Strategy | Example |
|------------------|------------------|---------|
| **Critical** (≥5 failed workflows) | Tag in header + top of comment | `@username ⚠️ Critical: 5+ workflows failing` |
| **High** (3-4 failed workflows) | Tag in header only | `@username - Multiple checks failing` |
| **Medium** (1-2 failed workflows) | Tag in failure section | `cc: @username - Please review failing checks` |
| **Low** (warnings only) | No direct tag, just FYI section | `ℹ️ Some checks have warnings` |

### 3. **Idempotent Updates**
- Preserve existing comment marker system: `<!-- RELEASE_DASHBOARD_COMMENT_MARKER: DO_NOT_DELETE -->`
- Update existing comments instead of creating duplicates
- Avoid spamming authors with redundant mentions

### 4. **Rate Limiting & Politeness**
- Only re-mention author if:
  - New failures detected since last comment
  - More than 1 hour has passed since last mention
  - Failure count has increased
- Add configurable cooldown period to avoid notification fatigue

---

## 🏗️ Implementation Tasks

### **Task 1: Extract PR Author Information**

Modify `scripts/release_dashboard/pr_commenter.py` to add:

```python
def get_pr_author(self) -> Optional[str]:
    """
    Retrieve the PR author's GitHub username.
    
    Returns:
        str: GitHub username (without @) or None if not found
    """
    try:
        # Method 1: From GitHub event payload
        if os.getenv("GITHUB_EVENT_PATH"):
            with open(os.getenv("GITHUB_EVENT_PATH"), "r") as f:
                event_data = json.load(f)
                if "pull_request" in event_data:
                    return event_data["pull_request"]["user"]["login"]
        
        # Method 2: From GitHub API
        if self.owner and self.repo and self.pr_number:
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            url = f"https://api.github.com/repos/{self.owner}/{self.repo}/pulls/{self.pr_number}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                pr_data = response.json()
                return pr_data["user"]["login"]
        
        return None
        
    except Exception as e:
        logger.warning(f"Failed to retrieve PR author: {e}")
        return None
```

### **Task 2: Implement Mention Logic**

Add a new method to generate mention-aware comments:

```python
def generate_mention_section(
    self, 
    author: str, 
    failing_count: int,
    is_update: bool = False,
    last_mention_time: Optional[datetime] = None
) -> str:
    """
    Generate appropriate mention section based on failure severity.
    
    Args:
        author: GitHub username
        failing_count: Number of failing workflows
        is_update: Whether this is updating an existing comment
        last_mention_time: Timestamp of last mention (for cooldown)
    
    Returns:
        Formatted mention string
    """
    # Check cooldown (default: 1 hour)
    MENTION_COOLDOWN_SECONDS = 3600
    should_mention = True
    
    if is_update and last_mention_time:
        elapsed = (datetime.now() - last_mention_time).total_seconds()
        should_mention = elapsed >= MENTION_COOLDOWN_SECONDS
    
    if not should_mention:
        return ""  # Skip mention during cooldown
    
    # Severity-based mentions
    if failing_count >= 5:
        return f"## ⚠️ @{author} — CRITICAL: {failing_count} Workflows Failing\n\n"
    elif failing_count >= 3:
        return f"### 🚨 @{author} — Multiple Checks Failing ({failing_count})\n\n"
    elif failing_count >= 1:
        return f"_cc: @{author} — Please review the failing checks below._\n\n"
    else:
        return ""  # No failures, no mention needed
```

### **Task 3: Track Mention History**

Create a mention tracking system to avoid spam:

```python
class MentionTracker:
    """Track when authors were last mentioned to implement cooldown."""
    
    def __init__(self, cache_file: str = ".pr_mention_cache.json"):
        self.cache_file = cache_file
        self.cache = self._load_cache()
    
    def _load_cache(self) -> dict:
        """Load mention history from cache file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Persist mention history."""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def should_mention(self, pr_key: str, current_failures: int) -> bool:
        """
        Determine if author should be mentioned based on history.
        
        Args:
            pr_key: Unique PR identifier (e.g., "owner/repo#123")
            current_failures: Current number of failing workflows
        
        Returns:
            True if mention is warranted, False otherwise
        """
        if pr_key not in self.cache:
            return current_failures > 0  # First time, mention if failures exist
        
        last_data = self.cache[pr_key]
        last_mention_time = datetime.fromisoformat(last_data["timestamp"])
        last_failure_count = last_data["failure_count"]
        
        # Cooldown check (1 hour)
        elapsed = (datetime.now() - last_mention_time).total_seconds()
        if elapsed < 3600:
            return False  # Still in cooldown
        
        # Mention if failures increased
        return current_failures > last_failure_count
    
    def record_mention(self, pr_key: str, failure_count: int):
        """Record that we mentioned the author."""
        self.cache[pr_key] = {
            "timestamp": datetime.now().isoformat(),
            "failure_count": failure_count
        }
        self._save_cache()
```

### **Task 4: Update Comment Generation**

Modify `generate_comment_body()` to include mentions:

```python
def generate_comment_body(
    self, 
    score_data: dict, 
    failing_workflows: list, 
    dashboard_branch: str,
    pr_author: Optional[str] = None
) -> str:
    """Generate PR comment with author mentions for failures."""
    
    failing_count = len([w for w in failing_workflows if w.get('count', 0) > 0])
    
    # Generate mention section if author available
    mention_section = ""
    if pr_author and failing_count > 0:
        pr_key = f"{self.owner}/{self.repo}#{self.pr_number}"
        tracker = MentionTracker()
        
        if tracker.should_mention(pr_key, failing_count):
            mention_section = self.generate_mention_section(
                author=pr_author,
                failing_count=failing_count,
                is_update=True
            )
            tracker.record_mention(pr_key, failing_count)
    
    # Build comment body
    body = f"""{mention_section}🧭 **Release Readiness: {score_data['total_score']:.1f}% {score_data['status_emoji']}**

**Status:** {score_data['status_text']}

📊 **Top Failing Workflows:**
{self.format_failing_workflows(failing_workflows, max_count=3)}

📄 **Dashboard:** [{self.owner}/{self.repo}/{dashboard_branch}](https://github.com/{self.owner}/{self.repo}/blob/{dashboard_branch}/v0.7.0-release-checklist.md)

🛡️ **Readiness Badge:**
![Readiness Badge]({self.generate_badge_url(score_data['total_score'])})

**Last updated:** {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}

{self.COMMENT_MARKER}
"""
    
    return body
```

### **Task 5: Add Configuration Options**

Create a configuration file `configs/pr_mentions_config.yml`:

```yaml
# PR Author Mention Configuration

mention:
  enabled: true
  
  # Cooldown period before re-mentioning (seconds)
  cooldown_seconds: 3600
  
  # Minimum failures to trigger mention
  min_failures_for_mention: 1
  
  # Severity thresholds
  severity:
    critical: 5    # >= 5 failing workflows
    high: 3        # >= 3 failing workflows
    medium: 1      # >= 1 failing workflow
  
  # Users to never mention (bots, automated accounts)
  exclude_users:
    - "dependabot[bot]"
    - "github-actions[bot]"
    - "renovate[bot]"
  
  # Custom message templates
  templates:
    critical: "⚠️ @{author} — CRITICAL: {count} workflows failing! Immediate attention required."
    high: "🚨 @{author} — Multiple checks failing ({count}). Please review ASAP."
    medium: "cc: @{author} — {count} check(s) need your attention."
```

### **Task 6: Update GitHub Workflow**

Ensure the workflow has proper permissions in `.github/workflows/ci-pro-dashboard.yml`:

```yaml
permissions:
  contents: write
  actions: read
  pull-requests: write  # Required for mentioning
  issues: write         # PRs are issues in GitHub API
```

---

## 🧪 Testing Checklist

### Unit Tests (`tests/test_pr_mentions.py`)

```python
import pytest
from scripts.release_dashboard.pr_commenter import PRCommenter, MentionTracker

def test_get_pr_author_from_event():
    """Test author extraction from GitHub event payload."""
    # Test implementation

def test_mention_severity_levels():
    """Test correct mention format for different failure counts."""
    commenter = PRCommenter(token="test", owner="org", repo="repo", pr_number=1)
    
    # Critical: 5+ failures
    mention = commenter.generate_mention_section("alice", 5)
    assert "@alice" in mention
    assert "CRITICAL" in mention
    
    # High: 3-4 failures
    mention = commenter.generate_mention_section("bob", 3)
    assert "@bob" in mention
    assert "Multiple" in mention
    
    # Medium: 1-2 failures
    mention = commenter.generate_mention_section("charlie", 1)
    assert "@charlie" in mention

def test_mention_cooldown():
    """Test cooldown prevents spam."""
    tracker = MentionTracker(cache_file=".test_cache.json")
    pr_key = "org/repo#123"
    
    # First mention should work
    assert tracker.should_mention(pr_key, 3) == True
    tracker.record_mention(pr_key, 3)
    
    # Immediate second mention should be blocked
    assert tracker.should_mention(pr_key, 3) == False

def test_exclude_bot_authors():
    """Test bots are not mentioned."""
    bot_users = ["dependabot[bot]", "github-actions[bot]"]
    # Test implementation
```

### Integration Tests

1. **Test on Real PR:**
   ```bash
   # Create test PR
   git checkout -b test-pr-mentions
   git commit --allow-empty -m "test: PR author mentions"
   git push origin test-pr-mentions
   
   # Trigger CI failure
   # Check PR comment includes @yourusername
   ```

2. **Test Cooldown:**
   - Trigger multiple CI runs within 1 hour
   - Verify author is only mentioned once
   
3. **Test Severity Levels:**
   - Create PRs with 1, 3, and 5+ failures
   - Verify appropriate mention format

---

## 📊 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Author Notification Rate** | 100% for failures | Track mentions vs failures |
| **False Mention Rate** | < 1% | Monitor incorrect mentions |
| **Cooldown Effectiveness** | No spam complaints | User feedback |
| **MTTR (Mean Time to Resolution)** | -30% reduction | Compare before/after |
| **Author Response Time** | < 30 minutes | Track from mention to action |

---

## 🚀 Rollout Plan

### Phase 1: Soft Launch (1 week)
- Enable for test repository only
- Monitor for issues
- Gather team feedback

### Phase 2: Beta (1 week)
- Enable for 50% of repositories
- A/B test mention effectiveness
- Refine templates based on feedback

### Phase 3: Full Production
- Enable for all repositories
- Document best practices
- Create opt-out mechanism for specific PRs

---

## 🔧 Maintenance & Monitoring

### Logs to Track
```python
logger.info(f"Mentioned @{author} for PR #{pr_number} ({failing_count} failures)")
logger.info(f"Skipped mention for @{author} (cooldown active)")
logger.warning(f"Failed to retrieve PR author for PR #{pr_number}")
```

### Metrics Dashboard
Add to existing dashboard:
- Total mentions sent
- Mentions per severity level
- Average response time after mention
- Cooldown activations

### Alerts
- **High Priority:** Mention failure rate > 5%
- **Medium Priority:** Response time > 1 hour
- **Low Priority:** Cooldown hit > 10 times/day (tune threshold)

---

## 🎨 Example Output

### Before Enhancement
```markdown
🧭 **Release Readiness: 75.0% 🔴**

📊 **Top Failing Workflows:**
• ❌ **tests-api.yml** — 3 recent failures
• ❌ **build.yml** — 2 recent failures
```

### After Enhancement (3 failures)
```markdown
### 🚨 @alice — Multiple Checks Failing (3)

🧭 **Release Readiness: 75.0% 🔴**

📊 **Top Failing Workflows:**
• ❌ **tests-api.yml** — 3 recent failures ([logs](https://...))
• ❌ **build.yml** — 2 recent failures ([logs](https://...))

💡 **Quick Actions:**
- Review the logs above
- Check recent commits
- Run tests locally: `make test`
```

---

## 🔮 Future Enhancements

### Phase 2 Features
- [ ] **Multi-author detection** - Mention co-authors from `Co-authored-by` trailer
- [ ] **Smart suggestions** - Include likely fix commands based on failure type
- [ ] **Escalation path** - Mention team lead if PR blocked > 24h
- [ ] **Praise system** - Mention author with 🎉 when all checks pass
- [ ] **Integration with Slack** - Cross-post urgent mentions to Slack

### Phase 3 Features
- [ ] **ML-powered insights** - Predict common mistakes and suggest preventive actions
- [ ] **Automated fix attempts** - Create suggested fix commits for common failures
- [ ] **Team analytics** - Track response patterns and identify training needs

---

## 📚 Related Files

Files to modify/create:
- `scripts/release_dashboard/pr_commenter.py` (main changes)
- `configs/pr_mentions_config.yml` (new configuration)
- `tests/test_pr_mentions.py` (new tests)
- `.github/workflows/ci-pro-dashboard.yml` (permission updates)
- `PR_AUTO_COMMENTER_IMPLEMENTATION_COMPLETE.md` (documentation update)

---

## ✅ Definition of Done

- [ ] PR author correctly detected from GitHub context
- [ ] Mentions appear in PR comments when checks fail
- [ ] Cooldown system prevents notification spam
- [ ] Bot authors are excluded from mentions
- [ ] Configuration file allows customization
- [ ] Unit tests cover all mention scenarios
- [ ] Integration test validates end-to-end flow
- [ ] Documentation updated with examples
- [ ] Team trained on new feature
- [ ] Metrics dashboard showing mention effectiveness
- [ ] No regression in existing PR comment functionality

---

## 🎯 Implementation Instructions for Cursor

To implement this feature, paste this prompt into Cursor and say:

> "Implement dynamic PR author mentions as specified in CURSOR_PROMPT_PR_AUTHOR_MENTIONS.md. Start by modifying `scripts/release_dashboard/pr_commenter.py` to add author detection and mention logic. Follow the phased approach: first implement basic mentions, then add cooldown tracking, then add severity levels. Make sure to preserve all existing functionality and add comprehensive tests."

**Key Points to Emphasize:**
1. Don't break existing PR comment functionality
2. Test cooldown logic thoroughly to avoid spam
3. Make configuration easy to tune per team preferences
4. Include rollback plan if issues arise
5. Monitor metrics closely during rollout

---

**Status:** Ready for Implementation 🚀  
**Estimated Effort:** 8-12 hours  
**Priority:** High (enhances accountability & MTTR)  
**Dependencies:** Existing PR Auto-Commenter system


