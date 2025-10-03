# ADR: Repo-First Documentation Protocol
**Context.** Notion integration is pending; artifacts/policies must be auditable and versioned.
**Decision.** The repo (configs/, docs/, ops/runbooks/) is the source of truth; CI gates enforce doc coupling.
**Consequences.** Faster iteration; consistent reviews; later optional one-way Notion sync.
