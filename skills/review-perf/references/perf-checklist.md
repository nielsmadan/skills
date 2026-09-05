# Performance Checklist — Code Examples

Annotated BAD/GOOD examples for each category in the Performance Checklist. Use these as reference when classifying findings during a review.

---

## Algorithmic Complexity

**What to look for:** nested loops over the same collection, repeated expensive calculations inside loops, array scans that could exit early.

**O(n²) or Worse:**
```javascript
// BAD: O(n²) nested loops
for (const item of items) {
  for (const other of items) {
    if (item.id === other.parentId) { ... }
  }
}

// GOOD: O(n) with lookup map
const parentMap = new Map(items.map(i => [i.id, i]));
for (const item of items) {
  const parent = parentMap.get(item.parentId);
}
```

**Repeated Calculations:**
```javascript
// BAD: Recalculating in loop
items.forEach(item => {
  const config = expensiveConfigLookup(); // Called n times
  process(item, config);
});

// GOOD: Calculate once
const config = expensiveConfigLookup();
items.forEach(item => process(item, config));
```

**Missing Early Exit:**
```javascript
// BAD: Always iterates entire array
function findUser(users, id) {
  let result = null;
  users.forEach(u => { if (u.id === id) result = u; });
  return result;
}

// GOOD: Exit when found
function findUser(users, id) {
  return users.find(u => u.id === id);
}
```

---

## Database/Query Patterns

**What to look for:** queries inside loops (N+1), loading all rows without a LIMIT, fetching all columns when only a few are needed, columns used in WHERE/ORDER BY/JOIN without indexes.

**N+1 Queries:**
```javascript
// BAD: Query per item
const users = await db.users.findAll();
for (const user of users) {
  user.posts = await db.posts.findAll({ where: { userId: user.id } });
}

// GOOD: Single query with include
const users = await db.users.findAll({
  include: [{ model: db.posts }]
});
```

**Missing Pagination:**
```javascript
// BAD: Load all records
const allUsers = await db.users.findAll();

// GOOD: Paginate
const users = await db.users.findAll({
  limit: 50,
  offset: page * 50
});
```

**SELECT * When Few Columns Needed:**
```sql
-- BAD: Fetching everything
SELECT * FROM users WHERE active = true;

-- GOOD: Only needed columns
SELECT id, name, email FROM users WHERE active = true;
```

---

## Memory Management

**What to look for:** connections or file handles opened without a finally/close, caches with no size or TTL bound, event listeners added without a corresponding removal.

**Unclosed Resources:**
```javascript
// BAD: Connection never closed
const conn = await db.connect();
const data = await conn.query('...');
// conn stays open

// GOOD: Always close
const conn = await db.connect();
try {
  return await conn.query('...');
} finally {
  conn.close();
}
```

**Growing Caches:**
```javascript
// BAD: Cache grows forever
const cache = {};
function getValue(key) {
  if (!cache[key]) cache[key] = expensiveLookup(key);
  return cache[key];
}

// GOOD: LRU or TTL cache
const cache = new LRUCache({ max: 1000 });
```

**Event Listener Leaks:**
```javascript
// BAD: Never removed
useEffect(() => {
  window.addEventListener('resize', handler);
}, []);

// GOOD: Cleanup
useEffect(() => {
  window.addEventListener('resize', handler);
  return () => window.removeEventListener('resize', handler);
}, []);
```

---

## UI/Render Performance

**What to look for:** inline object/function literals passed as props causing reference churn, long lists rendered without virtualization, heavy synchronous computation on the main thread.

**Unnecessary Re-renders (React):**
```javascript
// BAD: New object every render
<Child style={{ color: 'red' }} />
<Child onClick={() => handleClick(id)} />

// GOOD: Memoize
const style = useMemo(() => ({ color: 'red' }), []);
const handleClickMemo = useCallback(() => handleClick(id), [id]);
```

**Missing Virtualization:**
```javascript
// BAD: Render 10,000 items
{items.map(item => <Row key={item.id} {...item} />)}

// GOOD: Use virtualization
<VirtualizedList
  data={items}
  renderItem={({ item }) => <Row {...item} />}
/>
```

**Blocking Main Thread:**
```javascript
// BAD: Heavy sync computation
function processData(data) {
  return data.map(item => expensiveTransform(item)); // Blocks UI
}

// GOOD: Use web worker or chunk
async function processData(data) {
  return await worker.process(data);
}
```

---

## Network/IO

**What to look for:** sequential awaits for independent requests, the same request fired multiple times without deduplication or caching.

**Sequential Requests:**
```javascript
// BAD: Wait for each
const user = await fetchUser(id);
const posts = await fetchPosts(id);
const comments = await fetchComments(id);

// GOOD: Parallel
const [user, posts, comments] = await Promise.all([
  fetchUser(id),
  fetchPosts(id),
  fetchComments(id)
]);
```

**Missing Request Deduplication:**
```javascript
// BAD: Same request multiple times
componentA.fetchUser(123);
componentB.fetchUser(123); // Duplicate request

// GOOD: Cache or dedupe
const { data } = useSWR(`/users/${id}`, fetcher);
```
