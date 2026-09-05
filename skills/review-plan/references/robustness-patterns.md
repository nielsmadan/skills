# Robustness Anti-Pattern Examples

Code examples of common fragile patterns and their robust alternatives. Used by the robustness review agent.

## Timing Hacks (Never Do This)

```javascript
// BAD: Timeout to "fix" race condition
await saveData();
await new Promise(r => setTimeout(r, 100)); // Hope it's done!
const data = await loadData();

// GOOD: Proper synchronization
await saveData();
await waitForSync(); // Explicit sync point
const data = await loadData();
```

```javascript
// BAD: Polling for state change
let ready = false;
while (!ready) {
  await sleep(100);
  ready = checkIfReady();
}

// GOOD: Event-based
await new Promise(resolve => {
  emitter.once('ready', resolve);
});
```

## Silent Failures

```python
# BAD: Swallowing errors
try:
    result = risky_operation()
except:
    pass  # Hope it worked!

# GOOD: Handle or propagate
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise OperationFailedError(e) from e
```

## State Assumptions

```typescript
// BAD: Assuming state is current
const user = cache.get(userId);
user.balance += amount;  // Stale!

// GOOD: Optimistic locking or transactions
const user = await db.transaction(async (tx) => {
  const u = await tx.users.findUnique({ where: { id: userId } });
  return tx.users.update({
    where: { id: userId, version: u.version },
    data: { balance: u.balance + amount, version: { increment: 1 } }
  });
});
```
