# Security Checklist

## Injection
- SQL injection: string concatenation in queries instead of parameterized/prepared statements
- XSS: unescaped user input rendered in HTML/DOM
- Command injection: user input passed to shell commands (`exec`, `system`, `child_process`)
- Path traversal: user input in file paths without sanitization (`../` attacks)
- Template injection: user input in template engines without escaping
- LDAP/XML/Header injection via unsanitized input

## Authentication & Authorization
- Missing authentication on protected endpoints
- Broken access control (IDOR: direct object references without ownership check)
- Privilege escalation paths (role checks bypassed or missing)
- Session fixation or improper session invalidation
- JWT: missing signature verification, weak algorithms (none/HS256 when RS256 expected)
- Missing CSRF protection on state-changing operations

## Secrets & Sensitive Data
- Hardcoded credentials, API keys, tokens in source code
- Secrets in logs, error messages, or API responses
- Sensitive data in URL query parameters (logged by proxies/servers)
- Missing encryption for sensitive data at rest
- PII exposure in debug output or stack traces
- `.env` files or credential files committed to repository

## Input Validation
- Missing server-side validation (client-side only)
- Insufficient validation of file uploads (type, size, content)
- Missing rate limiting on sensitive endpoints
- Regex ReDoS vulnerability (catastrophic backtracking)
- Deserialization of untrusted data

## Cryptography
- Weak hashing algorithms (MD5, SHA1 for passwords)
- Missing salt in password hashing
- Predictable random values for security-sensitive operations (`Math.random()` instead of crypto)
- Hardcoded encryption keys or IVs
- Deprecated or broken cipher suites

## HTTP Security
- Missing security headers (CORS misconfiguration, CSP, HSTS)
- Open redirects via unvalidated redirect URLs
- Sensitive data transmitted over HTTP (not HTTPS)
- Missing `HttpOnly`/`Secure`/`SameSite` flags on session cookies
- CORS wildcard (`*`) with credentials

## Dependency Security
- Known vulnerable dependencies (check if version is outdated and has CVEs)
- Typosquatting risk in new dependency additions
- Overly permissive dependency version ranges
