# Security Policy

## Supported Versions

| Version | Supported |
| --- | --- |
| 2.1.x | ✅ Active |
| < 2.0 | ❌ End of life |

## Reporting a Vulnerability

If you discover a security vulnerability in NeuraSearch, please report it responsibly.

### How to Report

1. **Do NOT** open a public GitHub issue for security vulnerabilities.
2. Email your report to: **security@neurasearch.dev** (or open a private GitHub Security Advisory).
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment** within 48 hours.
- **Assessment** within 7 business days.
- **Fix timeline** communicated after assessment.
- **Credit** in the release notes (unless you prefer anonymity).

## Security Architecture

NeuraSearch implements the following security measures:

### Authentication
- JWT tokens with HS256 algorithm and configurable expiration
- Password hashing via bcrypt (passlib)
- Middleware-level authentication on all API endpoints

### Data Isolation
- Workspace-level logical isolation across all data stores
- Parameterized SQL queries throughout (no string interpolation)
- Path traversal protection on file uploads

### Computation Sandbox
- User code execution runs in isolated subprocesses
- Empty environment variables (`env={}`) to block network access
- 3-second execution timeout
- Restricted imports: only `math`, `datetime`, `json` allowed
- Blocked modules: `os`, `sys`, `subprocess`, `shutil`, `socket`, `urllib`, `http`, `ftplib`

### Secrets Management
- All sensitive values loaded from `.env` file (git-ignored)
- No secrets committed to version control
- Pydantic BaseSettings for type-safe configuration
