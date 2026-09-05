# Security Checklist — Code Examples & Commands

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
