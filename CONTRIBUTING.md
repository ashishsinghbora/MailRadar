# Contributing to MailRadar

Thank you for your interest in contributing to MailRadar! We welcome community contributions that align with our high standards of software quality, security, and ethical developer outreach.

---

## Code of Conduct

All contributors and maintainers are expected to follow our community guidelines: be respectful, collaborative, and constructive.

---

## Development Workflow

1. **Fork & Branch**:
   Create a feature branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Environment Setup**:
   Follow instructions in [DEVELOPMENT.md](file:///home/ashu/Projects/MailRadar/DEVELOPMENT.md).

3. **Testing**:
   Every new feature or bugfix must be accompanied by comprehensive tests:
   ```bash
   pytest
   ```

4. **Commit Standards**:
   Use Conventional Commits:
   - `feat:` New features
   - `fix:` Bug fixes
   - `docs:` Documentation updates
   - `test:` Test additions or refactoring
   - `refactor:` Code improvements without behavioral changes

5. **Pull Requests**:
   Submit PRs against `main`. Ensure all CI checks pass.
