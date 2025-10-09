🧭 **System Anchor:** Please review the [SYSTEM_PROMPT.md](../SYSTEM_PROMPT.md) before merging.
This document defines the mission, governance flow, and observer guardrails for this repo.

---

# 🔄 Pull Request — MAGSASA-CARD ERP

<!-- 
This PR template enforces governance standards from `/docs/cursor-prompt.md`.
Complete ALL sections before requesting review.
-->

## 📌 Pull Request Summary

### What does this PR do?
<!-- Provide a clear, concise description of the changes -->


### Related Issue/Ticket
<!-- Link to issue, Jira ticket, or Notion page -->
- Issue: #
- Ticket: 

### Type of Change
<!-- Mark with [x] -->
- [ ] 🐛 Bug fix
- [ ] ✨ New feature
- [ ] 🔧 Refactor
- [ ] 📚 Documentation update
- [ ] 🧪 Test improvements
- [ ] 🚀 Performance optimization
- [ ] 🔒 Security enhancement

---

## 🧪 QA Consistency Checklist (Observer + Governance)

Please verify the following **before merging**. These align with automated checks run by the QA Consistency Checker:

* [ ] Observer thresholds match guardrails (`observer_guardrails.yaml`)
* [ ] Render metrics (uptime, latency, drift) are within required limits
* [ ] Required secrets (`RENDER_API_KEY`, `RENDER_SERVICE_ID`, `SLACK_GOVERNANCE_WEBHOOK`) are present or documented
* [ ] Alert Loop integration remains intact (Render → Governance → Slack → Observer)
* [ ] No drift detected between governance specs and workflow config
* [ ] All related specs (`mcp-architecture.md`, `render_integration.md`, `slack_integration.md`) are updated if necessary

📝 *Note: If any of these checks fail, the automated QA Consistency Checker will flag this PR.*

---

## 📑 1. Spec-First Compliance

> **Governance Rule:** *"All new features, services, or adapters must reference a spec file in `/specs/`."*

- [ ] This PR is linked to an approved specification document
- [ ] Spec file location: `/specs/____________________.md`
- [ ] All new endpoints, services, or data flows are traceable to the spec
- [ ] If no spec exists, I have created one and included it in this PR

**Reviewer Note:** PRs without a linked spec are automatically non-compliant.

---

## 🧩 2. Architecture & MCP Compliance

> **Governance Rule:** *"Follow the MCP → Adapter → Pod structure strictly."*

### Architecture Alignment
- [ ] Code follows the `MCP → Adapter → Pod` pattern
- [ ] Services are modular, decoupled, and containerized
- [ ] No architectural drift or deviation from existing patterns
- [ ] No duplicate code or functionality

### MCP Tool Integration (if applicable)
- [ ] MCP manifest includes YAML + schema for new tools
- [ ] Tool adapters declare scopes, rate limits, and methods
- [ ] External tools are callable through MCP adapters (no direct calls from pods)
- [ ] Input/output schemas are validated and documented

### API Contracts
- [ ] Endpoints follow naming conventions: `/chat`, `/score`, `/recommend`, `/plan`, `/prescribe`
- [ ] Request/response schemas use Pydantic models
- [ ] OpenAPI annotations are included (`/docs` and `/openapi.json` work)
- [ ] API contracts match the spec

---

## 📊 3. Data & Database Integrity

> **Governance Rule:** *"All database operations must include validation and rollback logic."*

### Schema Validation
- [ ] Database schema matches the models in `src/models/`
- [ ] Field names align with current schema (e.g., `full_name`, `mobile_number`, `land_size_ha`)
- [ ] No references to deprecated fields (e.g., `name`, `phone`, `farm_size`)

### Database Operations
- [ ] Database operations include validation logic
- [ ] Rollback logic is implemented for transactions
- [ ] Foreign key constraints are defined and enforced
- [ ] ACID compliance is maintained (Atomicity, Consistency, Isolation, Durability)

### Data Precision
- [ ] Financial fields use 2-decimal precision
- [ ] Datetime fields use ISO format
- [ ] Geographic coordinates use proper precision
- [ ] Edge cases (nulls, precision loss, constraint violations) are handled

### Integration Testing
- [ ] New database operations have integration-level tests
- [ ] Tests use real database connections (not just mocks)
- [ ] Tests include transaction rollback for isolation

---

## 🧠 4. Prescription Engine Requirements

> **Governance Rule:** *"All critical operations must log `traceId`, `ruleVersion`, and `modelHash`."*

**Skip this section if your PR doesn't involve prescriptions, scoring, or recommendations.**

### Auditability
- [ ] All prescriptions/recommendations include `traceId`
- [ ] All prescriptions/recommendations include `ruleVersion`
- [ ] All prescriptions/recommendations include `modelHash`
- [ ] Timestamps are included for all operations

### Prescription Metadata
- [ ] Prescriptions include: `dosage`, `timing`, `risk`, `roi`
- [ ] Recommendations include confidence scores
- [ ] Explanations include data-backed reasoning with citations
- [ ] Constraint solvers handle edge cases (low budget, high rainfall, unavailable SKUs)

### Fallback Logic
- [ ] Fallback routing is implemented for model failures
- [ ] RAG hydration is performed before inference (if applicable)
- [ ] Missing data scenarios are handled gracefully

---

## 🧪 5. Testing Standards

> **Governance Rule:** *"Tests must be comprehensive, current, and organized."*

### Test Organization
- [ ] All new tests are placed under `/tests/`
- [ ] No duplicate test files exist (check root vs. `/tests/`)
- [ ] Test files follow naming convention: `test_*.py`

### Test Quality
- [ ] Test fixtures match the current database schema
- [ ] Tests include both unit and integration levels
- [ ] Tests use proper pytest markers (`@pytest.mark.database`, etc.)
- [ ] Test coverage is >90% for new features

### Pytest Configuration
- [ ] `pytest.ini` or `pyproject.toml` markers are updated if needed
- [ ] Custom pytest configuration is in `pyproject.toml` (not embedded in test files)

---

## 🔐 6. Security & Secrets Management

> **Governance Rule:** *"No hardcoded secrets or environment variables in code."*

### Credential Security
- [ ] No hardcoded API keys, tokens, or passwords
- [ ] Environment variables are used via `.env` or secret management
- [ ] External integrations use the credential broker
- [ ] Secrets are not logged or printed

### Input Validation
- [ ] All public endpoints validate input
- [ ] SQL injection risks are mitigated (ORM usage, parameterized queries)
- [ ] XSS and CSRF protections are in place (if applicable)
- [ ] File upload endpoints validate file types and sizes

### Permissions & Access Control
- [ ] Least-privilege principles are applied
- [ ] Role-based access control (RBAC) is enforced
- [ ] Session management follows security best practices

---

## 📚 7. Documentation & README

> **Governance Rule:** *"Documentation must be updated to reflect new changes."*

### Documentation Updates
- [ ] `README.md` or `/docs/` have been updated
- [ ] Inline docstrings are complete and accurate
- [ ] API endpoints are documented (docstrings + OpenAPI)

### Visual Documentation (if applicable)
- [ ] Architecture diagrams updated (if structure changed)
- [ ] Data flow diagrams updated (if data paths changed)
- [ ] Sequence diagrams included for complex interactions

### Usage Examples
- [ ] Code examples are provided for new features
- [ ] Usage instructions are clear and tested

---

## 📁 8. Deployment & Lifecycle

> **Governance Rule:** *"Deployment pipelines and lifecycle hooks must remain stable."*

### Deployment Impact
- [ ] End-to-end deployment pipeline is unaffected
- [ ] CI/CD workflows pass successfully
- [ ] No breaking changes to deployment scripts

### Rollback & Recovery
- [ ] Rollback scripts or instructions are updated (if needed)
- [ ] Database migrations include down migrations
- [ ] Rollback has been tested

### Lifecycle Hooks
- [ ] Initialization scripts are updated (if needed)
- [ ] Teardown/cleanup scripts are tested
- [ ] Health checks are passing

---

## 🧭 9. Final Governance Sign-Off

> **Stop Test:** "If this code deployed into production today, would it still follow the ERP architecture and MCP standards six months from now?"

### Developer Sign-Off
- [ ] I have verified that this PR complies with **all** governance principles defined in `/docs/cursor-prompt.md`
- [ ] I have reviewed audit fields and traceability requirements
- [ ] I have checked for MCP or Prescription Engine deviations
- [ ] I have tested this code locally and verified it works
- [ ] I understand that violating governance standards may block this PR from merging

### Reviewer Checklist (for AI/Human Reviewers)
- [ ] Spec-first compliance verified
- [ ] Architecture alignment confirmed
- [ ] Database integrity validated
- [ ] Security review passed
- [ ] Test coverage is adequate
- [ ] Documentation is complete
- [ ] No architectural drift detected

---

## 📊 Pre-Merge Checklist

Before requesting final approval:

- [ ] All CI/CD pipelines are green
- [ ] No linter errors or warnings
- [ ] Test coverage meets threshold (>90%)
- [ ] No merge conflicts
- [ ] Branch is up to date with `main`/`develop`

---

## 💬 Additional Notes

<!-- 
Add any additional context, screenshots, performance metrics, or notes for reviewers.
If this PR involves complex logic, consider adding a walkthrough.
-->

---

## 🔗 Related Links

- Governance Manual: [`/docs/cursor-prompt.md`](/docs/cursor-prompt.md)
- Spec Directory: [`/specs/`](/specs/)
- Testing Guide: [`/tests/README.md`](/tests/README.md)
- Architecture Docs: [`/docs/`](/docs/)

---

**🧑‍⚖️ Reviewer:** Follow `/docs/cursor-prompt.md` when reviewing this PR.  
**👷 Developer:** Ensure all checkboxes are marked before requesting review.
