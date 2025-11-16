# Security Best Practices Guide
**Version**: 1.0.0
**Last Updated**: November 16, 2025
**Applies To**: Code Standards Auditor v4.2.2+

---

## Overview

This document outlines security best practices for developing, deploying, and maintaining the Code Standards Auditor application.

---

## 1. Dependency Management

### 1.1 Regular Updates
**Requirement**: Update dependencies monthly or when critical CVEs are announced.

```bash
# Monthly security check
pip-audit --desc
python3 -m bandit -r . -ll

# Update critical packages immediately
pip install --upgrade package-name
```

### 1.2 Version Pinning
**Current Practice**: Use minimum version constraints in `requirements.txt`

```txt
# Good - allows security patches
authlib>=1.6.5

# Avoid - prevents security updates
authlib==1.6.5
```

### 1.3 Vulnerability Monitoring
**Tools**:
- pip-audit (dependency vulnerabilities)
- bandit (code security issues)
- GitHub Dependabot alerts

**Schedule**: Weekly automated scans, immediate response to critical alerts

---

## 2. API Security

### 2.1 Authentication & Authorization

**API Keys** (Current Implementation):
- Store in environment variables only
- Never commit to version control
- Rotate quarterly or after suspected exposure
- Use separate keys for dev/staging/production

**Example .env**:
```bash
# NEVER commit this file
GEMINI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
```

### 2.2 Rate Limiting

**Current Settings** (`api/middleware/rate_limit.py`):
- Default: 60 requests/minute per IP
- Configurable via environment variable

**Production Recommendations**:
```bash
# Adjust based on usage patterns
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_BURST=20
```

### 2.3 Input Validation

**Required**: All user inputs must be validated

**Examples**:
```python
# Use Pydantic models for validation
from pydantic import BaseModel, validator

class CodeAnalysisRequest(BaseModel):
    code: str
    language: str

    @validator('language')
    def validate_language(cls, v):
        allowed = ['python', 'java', 'javascript']
        if v not in allowed:
            raise ValueError(f'Language must be one of {allowed}')
        return v
```

### 2.4 Output Sanitization

**Prevent Information Leakage**:
```python
# Good - generic error message
raise HTTPException(
    status_code=500,
    detail="Internal server error"
)

# Bad - exposes internal details
raise HTTPException(
    status_code=500,
    detail=f"Database connection failed: {str(e)}"
)
```

---

## 3. Cryptographic Practices

### 3.1 Hashing (Resolved in v4.2.2)

**✅ Current Implementation**:
```python
# Non-security use cases (cache keys, IDs)
code_hash = hashlib.md5(code.encode(), usedforsecurity=False).hexdigest()

# Security-sensitive use cases
code_hash = hashlib.sha256(code.encode()).hexdigest()
```

**Rule**: Always use `usedforsecurity=False` for MD5 to suppress Bandit warnings when MD5 is used for non-security purposes.

### 3.2 Secrets Management

**Never**:
- Hardcode secrets in code
- Commit secrets to git
- Log secrets
- Pass secrets in URLs

**Always**:
- Use environment variables
- Use .env files (git-ignored)
- Implement secrets rotation
- Encrypt secrets at rest (production)

---

## 4. Network Security

### 4.1 HTTPS/TLS

**Production Requirements**:
- TLS 1.2 or higher only
- Valid SSL certificates
- HSTS headers enabled
- Strong cipher suites

**Implementation** (via reverse proxy):
```nginx
# nginx example
server {
    listen 443 ssl http2;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:...';

    add_header Strict-Transport-Security "max-age=31536000" always;
}
```

### 4.2 CORS Configuration

**Current**: Configured in `api/main.py`

**Production Settings**:
```python
# Restrict to specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 4.3 Binding Interfaces

**Development** (`.env`):
```bash
API_HOST=127.0.0.1  # Localhost only
API_PORT=8000
```

**Production** (behind reverse proxy):
```bash
API_HOST=127.0.0.1  # Let nginx/apache handle external access
API_PORT=8000
```

**Direct Internet Access** (use with firewall):
```bash
API_HOST=0.0.0.0  # All interfaces - REQUIRES FIREWALL
API_PORT=8000
```

---

## 5. Database Security

### 5.1 Neo4j Security

**Connection Security**:
```python
# Use environment variables
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=strong-password-here
NEO4J_DATABASE=code-standards
```

**Best Practices**:
- Use strong passwords (16+ characters)
- Change default credentials
- Use separate credentials per environment
- Enable encryption for bolt:// connections
- Limit database user permissions

### 5.2 Query Security

**✅ Current**: Using Cypher parameterized queries

**Example**:
```python
# Good - parameterized
query = "MATCH (n:Standard {id: $id}) RETURN n"
result = session.run(query, id=user_input)

# Bad - string concatenation (SQL injection risk)
query = f"MATCH (n:Standard {{id: '{user_input}'}}) RETURN n"
```

### 5.3 Redis Security

**Configuration**:
```bash
# Bind to localhost
bind 127.0.0.1

# Require authentication
requirepass your-strong-password

# Disable dangerous commands
rename-command FLUSHALL ""
rename-command CONFIG ""
```

---

## 6. Code Security

### 6.1 Static Analysis

**Pre-commit Hooks** (`.pre-commit-config.yaml`):
```yaml
repos:
  - repo: local
    hooks:
      - id: bandit
        name: bandit
        entry: bandit
        args: ['-r', '.', '-ll']
        language: system
        pass_filenames: false
```

### 6.2 Dangerous Operations

**Pickle Usage** (utils/cache_manager.py):
- ⚠️ Only use with trusted data
- Consider removing pickle fallback
- Add integrity checks if keeping

**File Operations**:
```python
# Validate paths to prevent traversal
from pathlib import Path

def safe_read(user_path: str, base_dir: Path) -> str:
    full_path = (base_dir / user_path).resolve()
    if not str(full_path).startswith(str(base_dir)):
        raise ValueError("Path traversal attempt")
    return full_path.read_text()
```

### 6.3 Command Injection Prevention

**Never**:
```python
# BAD - command injection risk
os.system(f"process {user_input}")
```

**Always**:
```python
# GOOD - use subprocess with list
subprocess.run(["process", user_input], check=True)
```

---

## 7. Deployment Security

### 7.1 Environment Separation

**Environments**:
- Development: Local, permissive settings
- Staging: Production-like, test data
- Production: Strict settings, real data

**Configuration**:
```bash
# .env.production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
ENABLE_SWAGGER=false
```

### 7.2 Docker Security

**Dockerfile Best Practices**:
```dockerfile
# Use specific version tags
FROM python:3.11.9-slim

# Run as non-root user
RUN useradd -m appuser
USER appuser

# Minimal permissions
COPY --chown=appuser:appuser . /app

# No secrets in image
# Use environment variables or secrets management
```

### 7.3 Secrets in CI/CD

**GitHub Actions**:
```yaml
- name: Run tests
  env:
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  run: pytest
```

---

## 8. Logging & Monitoring

### 8.1 Secure Logging

**Never Log**:
- API keys
- Passwords
- Personal data (PII)
- Session tokens

**Example**:
```python
# Good - masked
logger.info(f"API call with key: {api_key[:8]}***")

# Bad - exposed
logger.info(f"API call with key: {api_key}")
```

### 8.2 Security Monitoring

**Monitor For**:
- Failed authentication attempts
- Rate limit violations
- Unusual access patterns
- Error rate spikes
- Slow query warnings

**Tools**:
- Prometheus metrics
- Grafana dashboards
- Alert rules

---

## 9. Incident Response

### 9.1 Security Incident Process

1. **Detection**: Automated alerts or manual discovery
2. **Containment**: Isolate affected systems
3. **Investigation**: Determine scope and impact
4. **Remediation**: Fix vulnerability, rotate secrets
5. **Communication**: Notify stakeholders
6. **Documentation**: Document incident and response
7. **Prevention**: Update procedures to prevent recurrence

### 9.2 Breach Response

**If API Key Compromised**:
1. Immediately revoke the key
2. Generate new key
3. Update `.env` file
4. Restart application
5. Review logs for unauthorized usage
6. Document incident in `SECURITY_INCIDENT_YYYY-MM-DD.md`

**If Database Compromised**:
1. Disconnect from network
2. Change all database credentials
3. Review audit logs
4. Restore from backup if needed
5. Conduct security audit

---

## 10. Compliance & Auditing

### 10.1 Security Audit Schedule

**Daily**: Automated dependency checks (CI/CD)
**Weekly**: Bandit security scans
**Monthly**: Manual code review
**Quarterly**: Penetration testing (if public-facing)
**Annually**: Comprehensive security audit

### 10.2 Audit Checklist

- [ ] All dependencies up to date
- [ ] No known CVEs in dependencies
- [ ] Bandit scan passing
- [ ] No hardcoded secrets
- [ ] All tests passing
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Logging properly configured
- [ ] Access controls reviewed
- [ ] Backup strategy validated

---

## 11. Developer Guidelines

### 11.1 Secure Coding Checklist

Before committing code:
- [ ] No secrets in code
- [ ] Input validation implemented
- [ ] Output sanitization implemented
- [ ] Error messages don't leak info
- [ ] Dependencies are secure versions
- [ ] Bandit scan passes
- [ ] Tests include security cases

### 11.2 Code Review Security Focus

Reviewers should verify:
- Authentication/authorization correct
- Input validation thorough
- SQL/NoSQL injection prevented
- XSS vulnerabilities addressed
- Sensitive data properly handled
- Error handling doesn't expose internals

---

## 12. Resources

### Documentation
- [OWASP Top 10](https://owasp.org/Top10/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [Python Security](https://python.readthedocs.io/en/stable/library/security_warnings.html)

### Tools
- [Bandit](https://bandit.readthedocs.io/) - Python security linter
- [pip-audit](https://pypi.org/project/pip-audit/) - Dependency checker
- [Safety](https://pyup.io/safety/) - Vulnerability scanner

### Internal
- `SECURITY_AUDIT_REPORT_20251116.md` - Latest audit report
- `API_KEY_SECURITY.md` - API key management
- `.env.example` - Configuration template

---

## Appendix: Security Contacts

**Project Maintainer**: ronkoch2-code
**Repository**: https://github.com/ronkoch2-code/code-standards-auditor
**Issue Reporting**: GitHub Issues (mark as security if sensitive)

**For Critical Security Issues**:
Create private security advisory on GitHub or email maintainer directly.

---

**Document Version**: 1.0.0
**Next Review**: February 16, 2026 (90 days)
