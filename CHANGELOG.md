# Changelog

All notable changes to MailRadar will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-31

### Added
- **Core Architecture & Monorepo Foundation**:
  - FastAPI modular backend architecture with Pydantic v2 validation.
  - SQLAlchemy 2.0 dual-compatible PostgreSQL and SQLite database engine with UUID primary keys.
  - Next.js 15 modern dark-first SaaS web dashboard with Tailwind CSS, Lucide icons, and Framer Motion.
  - Full-featured Linux Typer CLI with rich terminal formatting and exit code standards.
- **Authentication & Multi-Tenant User Management**:
  - Secure bcrypt password hashing and JWT access token handling.
  - Role-based permissions (`ADMIN`, `OPERATOR`, `VIEWER`).
  - Immutable audit logging for administrative actions.
- **Discovery Engine**:
  - GitHub REST API adapter for repositories, maintainers, languages, topics, and metrics.
  - Website and documentation adapter with SSRF protection, RFC 1918 private network blocking, crawl depth limiting, and robots.txt compliance.
  - Modular adapter registry supporting custom source parsers.
- **Professional Contact Intelligence**:
  - Strict professional email regex extraction with contextual windowing.
  - Complete contact provenance records linking source URL, category, extraction timestamp, and evidence snippet.
  - Relevance scoring engine based on maintainer role signals.
- **Verification Engine**:
  - Multi-stage RFC syntax validation, domain existence, and DNS MX record lookup.
  - Offline/Sandbox fallback mode for hermetic testing.
- **Suppression Management**:
  - Permanent global and organization-scoped suppression list.
  - Mandatory suppression and opt-out checks prior to any message dispatch.
- **Campaign Outreach Engine & Human Approval Queue**:
  - Complete campaign lifecycle: `DRAFT` -> `RECIPIENT_REVIEW` -> `APPROVED` -> `SCHEDULED` -> `SENDING` -> `COMPLETED`.
  - Mandatory human approval gate for every individual recipient.
  - Sandbox delivery provider and TLS SMTP delivery provider.
  - Idempotent delivery protection and transactional outbox.
- **Testing & DevOps**:
  - Comprehensive Pytest test suite covering unit, security (SSRF, duplicate delivery, suppression bypass), and integration flows.
  - Docker Compose configuration and production Dockerfiles.
  - GitHub Actions CI pipeline.
