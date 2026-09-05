# Testing Principles — Code Examples

Code examples for each of the 8 testing principles. All examples use JavaScript/Jest syntax. Translate idioms to the detected framework using the terminology mapping in `framework-mapping.md`.

---

### 1. Test Behavior, Not Implementation

```javascript
// BAD: Breaks on any refactor
expect(component.state.internalFlag).toBe(true);
expect(service._privateMethod).toHaveBeenCalled();

// GOOD: Test observable behavior
expect(screen.getByText('Welcome')).toBeVisible();
expect(result.status).toBe('success');
```

---

### 2. Mock Only External Boundaries

```javascript
// BAD: Testing mocks, not real code
jest.mock('./database');
jest.mock('./auth');
jest.mock('./validator');
jest.mock('./logger');
// What's actually being tested?

// GOOD: Mock only external boundaries
jest.mock('./externalPaymentApi');
```

---

### 3. Meaningful Assertions

```javascript
// BAD: Test always passes
test('user login', async () => {
  await loginUser('test@example.com');
  // No expect() - what are we testing?
});

// GOOD: Verify outcomes
test('user login', async () => {
  const result = await loginUser('test@example.com');
  expect(result.token).toBeDefined();
  expect(result.user.email).toBe('test@example.com');
});
```

---

### 4. No Brittle Timing

```javascript
// BAD: Flaky - depends on timing
await doAsyncThing();
await new Promise(r => setTimeout(r, 100));
expect(result).toBe('done');

// GOOD: Wait for actual condition
await waitFor(() => expect(result).toBe('done'));
```

---

### 5. Independent Tests

```javascript
// BAD: Tests depend on execution order
let sharedState;
test('first', () => { sharedState = setup(); });
test('second', () => { expect(sharedState.value).toBe(1); }); // Fails if run alone

// GOOD: Each test sets up its own state
test('first', () => { const state = setup(); /* ... */ });
test('second', () => { const state = setup(); expect(state.value).toBe(1); });
```

---

### 6. Cover Edge Cases

No code example — principle is expressed as a checklist:

- Empty inputs
- Null/undefined
- Boundary values (0, -1, MAX_INT)
- Error conditions
- Concurrent access
- Unicode/special characters

---

### 7. Focused Tests

```javascript
// BAD: Tests too much, hard to debug failures
test('user flow', async () => {
  // 50 lines testing signup, login, profile, settings, logout
});

// GOOD: One concern per test
test('signup creates user', ...);
test('login sets session', ...);
```

---

### 8. Named Constants Over Magic Values

```javascript
// BAD: What is 42? Why 'abc123'?
expect(calculate(42)).toBe(84);
expect(validate('abc123')).toBe(true);

// GOOD: Named constants explain intent
const VALID_USER_ID = 'user_12345';
const DOUBLED_VALUE = INPUT * 2;
```
