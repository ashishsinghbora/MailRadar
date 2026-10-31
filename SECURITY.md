# Security Policy

Security is a primary design pillar of MailRadar. We take vulnerabilities seriously and appreciate responsible disclosure.

---

## 1. Supported Versions

| Version | Supported          |
| :------ | :----------------- |
| 1.0.x   | :white_check_mark: |
| < 1.0.0 | :x:                |

---

## 2. Reporting a Vulnerability

If you discover a security vulnerability within MailRadar, please do **not** open a public issue. Instead, submit a confidential report to our security team:

- **Email**: `security@mailradar.dev` (or via GitHub Security Advisories)
- **Response Target**: Within 48 hours with an initial assessment and timeline.

Please include:
- Description of vulnerability and impact.
- Clear reproduction steps or proof-of-concept.
- Any suggested mitigations.

---

## 3. Core Security Defenses Implemented in MailRadar

### 3.1. SSRF Protection (Server-Side Request Forgery)
MailRadar employs strict URL validation before fetching any remote project website or documentation:
- **Private Address Deny-List**: Blocks IPv4 (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16), Loopback (127.0.0.0/8), Link-Local (169.254.0.0/16), and IPv6 equivalents (::1, fc00::/7, fe80::/10).
- **Cloud Metadata Blocking**: Blocks access to `169.254.169.254` (AWS, GCP, Azure, DigitalOcean instance metadata).
- **Safe Scheme Enforcement**: Only `http` and `https` protocols are allowed (`file://`, `gopher://`, `dict://` are strictly rejected).
- **Safe Redirects**: Multi-hop redirects are re-evaluated to prevent open-redirect SSRF pivoting.

### 3.2. Data Protection & Tenant Isolation
- **Credential Encryption**: Connected provider API keys and tokens are encrypted at rest using Fernet symmetric encryption.
- **Password Security**: Passwords are saved with salted bcrypt hashing.
- **Tenant Isolation**: All database queries for organization-scoped entities enforce organization filtering.
- **Access Control**: Role-based access control (`ADMIN`, `OPERATOR`, `VIEWER`) protects all mutating endpoints.

### 3.3. Outreach Abuse Protection
- **No Indiscriminate Scraping**: MailRadar enforces crawl depth limits, robot.txt compliance, and domain bounds.
- **Mandatory Human Approval**: No automated bot-sending. Every single recipient must be explicitly reviewed and approved by a human operator before email delivery is permitted.
- **Suppression Inviolability**: The suppression list check is hardcoded into the sending transaction pipeline and cannot be bypassed.
