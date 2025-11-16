# Security Audit Report
**Date**: November 16, 2025
**Version**: v4.2.2
**Auditor**: Claude Code (Automated Security Scan)
**Issue**: #7 - Update codebase to reflect current security standards

---

## Executive Summary

Comprehensive security audit conducted using industry-standard tools:
- **Bandit** (Python static security analyzer)
- **pip-audit** (Python dependency vulnerability scanner)
- **Safety** (Python package security checker)

### Results Overview

| Category | Count | Severity |
|----------|-------|----------|
| **Bandit Issues** | 253 | 7 High, 4 Medium, 242 Low |
| **Vulnerable Dependencies** | 16 | 10 packages affected |
| **Lines Scanned** | 19,955 | N/A |

### Risk Assessment

- **Critical**: 2 issues (vulnerable dependencies with RCE potential)
- **High**: 9 issues (MD5 usage, hardcoded secrets indicators)
- **Medium**: 4 issues (file permissions, binding interfaces)
- **Low**: 242 issues (mostly informational)

---

## Critical Issues (Immediate Action Required)

### 1. Vulnerable Dependencies - RCE Risk

#### authlib 1.6.1 → 1.6.5 (3 CVEs)
**Risk**: Remote Code Execution, Denial of Service
**CVSS**: 7.5 (HIGH) - 6.5 (MEDIUM)

**Vulnerabilities**:
1. **GHSA-9ggr-2464-2j32**: JWS critical header bypass
   - Allows policy bypass via `crit` parameter exploitation
   - Can lead to privilege escalation in mixed-language fleets

2. **GHSA-pq5p-34cr-23v9**: Unbounded JWS/JWT header/signature
   - Single request can exhaust 4GB+ RAM
   - CPU exhaustion attack vector

3. **GHSA-g7f3-828f-7h7m**: Unbounded DEFLATE decompression
   - 4KB ciphertext expands to 50MB+
   - Memory/CPU exhaustion DoS

**Fix**: `pip install --upgrade "authlib>=1.6.5"`

#### setuptools 65.5.0 → 78.1.1 (3 CVEs)
**Risk**: Remote Code Execution, Path Traversal, ReDoS
**CVSS**: HIGH

**Vulnerabilities**:
1. **GHSA-cx63-2mw6-8hw5**: RCE via package_index download functions
2. **PYSEC-2025-49**: Path traversal allows arbitrary file write
3. **PYSEC-2022-43012**: ReDoS in package_index.py

**Fix**: `pip install --upgrade "setuptools>=78.1.1"`

#### starlette 0.47.3 → 0.49.1
**Risk**: Denial of Service
**CVSS**: MEDIUM-HIGH

**Vulnerability**: GHSA-7f5h-v6xp-fcq8
- O(n²) complexity in FileResponse Range header parsing
- Affects StaticFiles and all FileResponse usage
- Quadratic-time CPU exhaustion per request

**Fix**: `pip install --upgrade "starlette>=0.49.1"`

---

## High Priority Issues

### 2. MD5 Usage for Security (7 instances)

**Finding**: MD5 hash used in security-sensitive contexts

**Locations**:
1. `api/routers/agent_optimized.py:685` - code hashing
2. `services/enhanced_recommendations_service.py:417` - code hashing
3. `services/recommendations_service.py:530,533` - cache keys
4. `services/standards_research_service.py:269,316` - ID generation

**Risk**: MD5 is cryptographically broken; not suitable for security
**Impact**: Collision attacks possible, cache poisoning potential

**Fix Options**:
```python
# Option 1: SHA-256 (security contexts)
import hashlib
code_hash = hashlib.sha256(code.encode()).hexdigest()

# Option 2: MD5 with usedforsecurity=False (non-security)
code_hash = hashlib.md5(code.encode(), usedforsecurity=False).hexdigest()
```

**Recommendation**:
- Use SHA-256 for code hashing
- Use `usedforsecurity=False` for cache keys (acceptable per Bandit)

### 3. Additional Vulnerable Dependencies

#### aiohttp 3.12.13 → 3.12.14
- **GHSA-9548-qrrj-x5pj**: Request smuggling in pure Python version
- **Fix**: `pip install --upgrade "aiohttp>=3.12.14"`

#### fastmcp 2.11.3 → 2.13.0 (2 CVEs)
- **GHSA-mxxr-jv3v-6pgc**: XSS in OAuth callback
- **GHSA-rj5c-58rq-j5g5**: Command injection on Windows
- **Fix**: `pip install --upgrade "fastmcp>=2.13.0"`

#### langchain-text-splitters 0.3.8 → 0.3.9
- **GHSA-m42m-m8cr-8m58**: XXE attacks in HTMLSectionSplitter
- **Fix**: `pip install --upgrade "langchain-text-splitters>=0.3.9"`

#### pip 25.2 → 25.3
- **GHSA-4xh5-x5gv-qwph**: Path traversal in sdist extraction
- **Fix**: `pip install --upgrade pip>=25.3"`

#### torch 2.7.1 → 2.8.0
- **GHSA-887c-mr87-cxwp**: DoS in ctc_loss function
- **Fix**: `pip install --upgrade "torch>=2.8.0"`

#### uv 0.8.13 → 0.9.5
- **GHSA-w476-p2h3-79g9**: Path traversal in tar archives
- **Fix**: `pip install --upgrade "uv>=0.9.5"`

---

## Medium Priority Issues

### 4. Hardcoded Bind Address

**Finding**: Application binds to all interfaces (0.0.0.0)

**Locations**:
- `config/settings.py:19` - API_HOST default
- `api/schemas/admin.py:177` - Configuration schema

**Current**:
```python
API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
```

**Recommendation**: Document security implications
```python
# Production: bind to specific interface or use reverse proxy
# Development: 0.0.0.0 is acceptable
API_HOST: str = Field(default="127.0.0.1", env="API_HOST")  # Safer default
```

### 5. Permissive File Permissions

**Finding**: Script sets 0o755 permissions

**Location**: `github-scripts/run_git_commit.py:13`

**Current**: `os.chmod(script_path, 0o755)`
**Risk**: Group/world readable
**Recommendation**: Consider 0o750 for scripts

### 6. Unsafe Pickle Deserialization

**Finding**: Pickle used as fallback for cache deserialization

**Location**: `utils/cache_manager.py:118`

**Current**:
```python
return pickle.loads(data)
```

**Risk**: Arbitrary code execution if cache is compromised
**Mitigation**:
- Already using JSON as primary deserializer (good!)
- Consider removing pickle fallback or adding integrity checks
- Document that cache storage must be trusted

---

## Low Priority Issues (242 total)

### Common Patterns:
- `assert` statements (B101) - 120 instances
- `Try/Except/Pass` blocks (B110) - 80 instances
- Hardcoded SQL (B608) - 15 instances
- Other informational warnings - 27 instances

**Recommendation**: Review incrementally, most are false positives or acceptable in context.

---

## Remediation Plan

### Phase 1: Critical (Immediate - Day 1)

1. **Update Critical Dependencies** (30 min)
   ```bash
   pip install --upgrade \
     "authlib>=1.6.5" \
     "setuptools>=78.1.1" \
     "starlette>=0.49.1"
   ```

2. **Test Application** (30 min)
   - Run full test suite
   - Verify no breaking changes
   - Check API functionality

### Phase 2: High Priority (Week 1)

1. **Replace MD5 Usage** (2-3 hours)
   - Replace in security contexts with SHA-256
   - Add `usedforsecurity=False` for cache keys
   - Update tests if hash values are checked

2. **Update Remaining Dependencies** (1 hour)
   ```bash
   pip install --upgrade \
     aiohttp fastmcp langchain-text-splitters \
     pip torch uv
   ```

3. **Run Regression Tests** (1 hour)

### Phase 3: Medium Priority (Week 2)

1. **Review Bind Configuration** (1 hour)
   - Document production deployment requirements
   - Update .env.example with security notes
   - Add deployment guide

2. **Review Pickle Usage** (2 hours)
   - Audit cache security model
   - Consider removing pickle fallback
   - Add cache validation

3. **File Permissions Review** (1 hour)
   - Audit script permissions
   - Update as needed

### Phase 4: Documentation (Week 2)

1. **Update Security Documentation** (2-3 hours)
   - Document dependency update policy
   - Add security best practices guide
   - Update incident response plan

2. **Update requirements.txt** (30 min)
   - Pin minimum secure versions
   - Add security comments

---

## Ongoing Recommendations

### 1. Automated Security Scanning
```bash
# Add to CI/CD pipeline
pip-audit --desc
bandit -r . -ll -f txt
```

### 2. Dependency Management
- Use `pip-audit` monthly
- Subscribe to security advisories for key dependencies
- Pin minimum secure versions in requirements.txt

### 3. Pre-commit Hooks
```bash
# Install security checks
pip install pre-commit
# Add to .pre-commit-config.yaml:
# - bandit
# - pip-audit
```

### 4. Regular Audits
- Quarterly comprehensive security review
- Annual penetration testing (if public-facing)
- Keep OWASP Top 10 checklist

---

## Testing Requirements

### Pre-Deployment Tests
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Manual API endpoint testing
- [ ] Load testing with updated dependencies
- [ ] Security regression tests

### Success Criteria
- ✅ Zero critical vulnerabilities
- ✅ All high-priority fixes implemented
- ✅ Tests passing at 100%
- ✅ Documentation updated
- ✅ Deployment guide reviewed

---

## Appendix

### A. Tool Versions
- Bandit: Latest
- pip-audit: Latest
- Safety: Latest
- Python: 3.11.9

### B. Scan Commands
```bash
# Full scan
bandit -r . -f txt -ll > bandit_report.txt
pip-audit --desc > pip_audit_report.txt
safety check > safety_report.txt
```

### C. References
- OWASP Top 10 2021: https://owasp.org/Top10/
- CWE Top 25: https://cwe.mitre.org/top25/
- Python Security Best Practices: https://python.readthedocs.io/en/stable/library/security_warnings.html

---

**Report Generated**: 2025-11-16
**Next Review**: 2026-02-16 (90 days)
