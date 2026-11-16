# Security Checklist — Code Examples & Commands

## Broken Access Control (OWASP A01)

- Trace how the authenticated identity, role, and tenant are established. A caller-supplied
  tenant header or resource ID is a selector, not proof of permission. Verify membership or
  delegated access against trusted state before the sensitive read or mutation.
- Follow object access through routes, services, repositories, and database policies. Check
  detail, list/search, export/download, mutation, and batch paths that exist in scope. Nested
  resources need the relevant parent/tenant relationship enforced; a scoped parent lookup
  does not prove a separately loaded child belongs to it.
- Check permission-changing operations such as invitations, role assignment, ownership
  transfers, and credential administration against the acting user's authority. Logging in
  proves identity; it does not by itself authorize administration or another user's records.
- Check tenant-sensitive cache keys, queued jobs, and storage access when those paths carry
  identity across a boundary. Determine whether trusted context survives that transition;
  do not demand a particular enforcement layer when an existing control already covers it.
- Do not flag intentionally public resources, shared access, or privileged service actions
  merely for lacking an owner predicate. Establish the intended access contract. If external
  row-level policies or gateway rules are decisive but unavailable, record a validation gap.

Example: a user may fetch their own private invoice. Trace whether selecting a different
invoice ID reaches another user's data despite all effective controls. A parameterized query
prevents SQL injection but does not establish authorization. Conversely, a verified database
policy that filters by the trusted session tenant may already enforce the boundary. Report
the actual path and consequence, not just the shape of the query.

## Injection (OWASP A03)

**SQL Injection:**
```javascript
// BAD: String concatenation
const query = `SELECT * FROM users WHERE id = ${userId}`;

// GOOD: Parameterized query
const query = 'SELECT * FROM users WHERE id = ?';
db.query(query, [userId]);
```

**Command Injection:**
```javascript
// BAD: Unsanitized input to shell
exec(`ls ${userInput}`);

// GOOD: Use array form or escape
execFile('ls', [sanitizedPath]);
```

**XSS (Cross-Site Scripting):**
```javascript
// BAD: Direct HTML insertion
element.innerHTML = userContent;

// GOOD: Use textContent or sanitize
element.textContent = userContent;
// Or use DOMPurify for HTML
element.innerHTML = DOMPurify.sanitize(userContent);
```

## Sensitive Data Exposure (OWASP A02)

**Hardcoded Secrets:**
```javascript
// BAD: Secrets in code
const apiKey = 'sk-1234567890abcdef';
const password = 'admin123';

// GOOD: Environment variables
const apiKey = process.env.API_KEY;
```

**Patterns to grep for:**
```
password\s*=\s*['"][^'"]+['"]
api[_-]?key\s*=\s*['"][^'"]+['"]
secret\s*=\s*['"][^'"]+['"]
token\s*=\s*['"][^'"]+['"]
Bearer\s+[A-Za-z0-9\-_]+
```

**False-positive filtering:** Before reporting a match:
- Skip lines containing `example`, `placeholder`, `test`, `TODO`, `CHANGEME`, or `xxx`
- Skip files in `test/`, `__tests__/`, `*_test.*`, `*.test.*`, `*.spec.*`
- Skip `.md` files (documentation examples)
- If the matched value is a well-known placeholder (e.g., `sk-...` with all zeros, `your-api-key-here`), skip it

**Logging Sensitive Data:**
```javascript
// BAD: Logging credentials
console.log('User login:', { email, password });

// GOOD: Redact sensitive fields
console.log('User login:', { email, password: '[REDACTED]' });
```

## Security Misconfiguration (OWASP A05)

**CORS Issues:**
```javascript
// BAD: Overly permissive
app.use(cors({ origin: '*' }));

// GOOD: Specific origins
app.use(cors({ origin: ['https://myapp.com'] }));
```

## Dependency Vulnerabilities

**Check commands by ecosystem:**
```bash
# Node.js
npm audit
npx audit-ci --critical

# Python
pip-audit
safety check

# Ruby
bundle audit

# Go
govulncheck ./...
```
