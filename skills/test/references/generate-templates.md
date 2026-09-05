# Test Generation Templates

## What to Generate

> The templates below use Jest syntax for illustration. Adapt structure and syntax to the detected framework using the terminology mapping in `framework-mapping.md`. For example, in pytest use `def test_returns_expected_result():` instead of `it('returns expected result', ...)`.

**For a function:**
```javascript
describe('{functionName}', () => {
  it('returns expected result for valid input', () => {
    // Happy path
  });

  it('handles empty input', () => {
    // Edge case
  });

  it('throws on invalid input', () => {
    // Error handling
  });

  it('handles boundary value', () => {
    // Edge case: 0, MAX, etc.
  });
});
```

**For a component:**
```javascript
describe('{ComponentName}', () => {
  it('renders with required props', () => {
    // Happy path
  });

  it('responds to user interaction', () => {
    // User events
  });

  it('displays error state', () => {
    // Error handling
  });

  it('handles loading state', () => {
    // Async states
  });
});
```

**For a service/API:**
```javascript
describe('{ServiceName}', () => {
  it('returns data on success', () => {
    // Happy path
  });

  it('handles errors gracefully', () => {
    // Error handling
  });

  it('validates input', () => {
    // Input validation
  });
});
```

**For staged changes:**
1. Identify what changed (new function, modified behavior, etc.)
2. Find or create relevant test file
3. Generate tests for the changes
4. Ensure edge cases are covered

---

## Review Checklist

**Principles:**
- [ ] Tests verify behavior, not implementation
- [ ] Mocks limited to external boundaries
- [ ] All tests have meaningful assertions
- [ ] No brittle timing (setTimeout, sleep)
- [ ] Tests are independent (no shared state)
- [ ] Edge cases covered
- [ ] Tests are focused (one concern each)

**Flaky Patterns:**
- [ ] No unseeded `Math.random()`
- [ ] No unmocked `new Date()`
- [ ] No network calls to real services
- [ ] No file system dependencies without cleanup
- [ ] No environment variable assumptions

**Completeness (for code being reviewed):**
- [ ] All public functions/methods have tests
- [ ] All exported components have tests
- [ ] Error paths are tested, not just happy paths
- [ ] Edge cases identified in code have corresponding tests

**Pattern Conformance (for --staged/--unpushed/new tests):**
- [ ] File naming matches project convention
- [ ] Test organization matches existing tests (suite grouping and test naming conventions per framework — see `framework-mapping.md`)
- [ ] Setup/teardown patterns match existing tests (per-test and per-suite setup per framework)
- [ ] Mocking approach consistent with project (framework-specific mocking or dependency injection)
- [ ] Assertion style matches (expect vs assert, matchers used)
