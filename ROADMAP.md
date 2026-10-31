# MailRadar — Product Roadmap

This document outlines planned improvements, architectural evolution, and feature milestones for MailRadar.

---

## Phase 1: Core Foundation & Single-Tenant Release (Completed in v1.0.0)
- [x] FastAPI REST API with Pydantic v2 schemas and JWT auth.
- [x] SQLAlchemy 2.0 relational schema with UUID primary keys and Alembic migrations.
- [x] GitHub REST API discovery adapter with quota and rate limit handling.
- [x] Official website and documentation crawler with strict SSRF defense.
- [x] Professional contact extraction with evidence snippet preservation.
- [x] DNS MX verification pipeline.
- [x] Permanent suppression list and opt-out processing.
- [x] Outreach campaign manager with mandatory human approval queue.
- [x] Sandbox mock provider and SMTP email provider.
- [x] Next.js dark-first web dashboard with full responsive layout.
- [x] Typer-based Linux CLI with rich formatting.
- [x] Docker Compose deployment configuration.
- [x] Comprehensive automated test suite.

---

## Phase 2: Team Collaboration & Multi-User Governance (v1.1.0)
- [ ] Team invites and organization member management.
- [ ] Granular role permissions (Custom roles, Approval-only managers).
- [ ] Campaign change review requests and inline comments.
- [ ] Shared contact tag taxonomy across organization workspaces.

---

## Phase 3: Advanced Intelligence & Ecosystem Adapters (v1.2.0)
- [ ] GitLab and Codeberg discovery adapters.
- [ ] PyPI, npm, and Crates.io package metadata discovery adapters.
- [ ] Advanced AI-assisted personalization suggestions (strictly human-approved).
- [ ] Automated reply sentiment classification (Interested, Busy, Not Relevant, Unsubscribe).

---

## Phase 4: Enterprise Scale & Compliance (v1.3.0)
- [ ] SAML 2.0 / Okta / Azure AD Single Sign-On (SSO).
- [ ] Multi-region delivery routing and bounce webhook ingestion.
- [ ] Automated contact data retention expiration rules (GDPR right-to-be-forgotten schedules).
- [ ] High-throughput distributed Celery worker orchestration with Kubernetes Helm charts.
