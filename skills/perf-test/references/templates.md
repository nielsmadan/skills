# Performance Test Templates

Language-specific benchmark templates, load testing configs, and E2E scenario examples.

## Code Profiling by Language

### JavaScript/TypeScript

```javascript
// perf-tests/{target}.bench.js
const Benchmark = require('benchmark');
const suite = new Benchmark.Suite;

suite
  .add('{functionName}', function() {
    // code to benchmark
  })
  .on('complete', function() {
    console.log(this[0].toString());
    console.log('ops/sec:', this[0].hz);
  })
  .run();
```

### Python

```python
# perf-tests/{target}_bench.py
import timeit
import statistics

def benchmark():
    times = timeit.repeat(
        '{function_call}',
        setup='{setup_code}',
        number=1000,
        repeat=5
    )
    print(f"Mean: {statistics.mean(times):.4f}s")
    print(f"Stdev: {statistics.stdev(times):.4f}s")
```

### Go

```go
// {target}_test.go
func Benchmark{Function}(b *testing.B) {
    for i := 0; i < b.N; i++ {
        // code to benchmark
    }
}
```

## Load Testing

### Using hey (universal)

```bash
hey -n 1000 -c 50 -m GET http://localhost:3000/api/endpoint
```

### Using autocannon (Node.js)

```javascript
const autocannon = require('autocannon');
autocannon({
  url: 'http://localhost:3000/api/endpoint',
  connections: 50,
  duration: 10
}, console.log);
```

## E2E Scenario Testing

For testing real-world workflows involving multiple operations and state changes.

### 1. Setup Phase

```javascript
// Create known database state
async function setupTestState() {
  await db.reset();
  await db.seed({
    users: [{ id: 'user_1', balance: 1000 }],
    products: [{ id: 'prod_1', stock: 100, price: 25 }],
    carts: []
  });
}
```

### 2. Scenario Script

```javascript
// e2e-perf/checkout-flow.js
const { performance } = require('perf_hooks');

async function runScenario() {
  const metrics = { steps: [], total: 0 };
  const start = performance.now();

  // Step 1: Add items to cart
  let stepStart = performance.now();
  await fetch('/api/cart/add', {
    method: 'POST',
    body: JSON.stringify({ productId: 'prod_1', quantity: 2 })
  });
  metrics.steps.push({ name: 'add_to_cart', ms: performance.now() - stepStart });

  // Step 2: Apply discount code
  stepStart = performance.now();
  await fetch('/api/cart/discount', {
    method: 'POST',
    body: JSON.stringify({ code: 'SAVE10' })
  });
  metrics.steps.push({ name: 'apply_discount', ms: performance.now() - stepStart });

  // Step 3: Checkout
  stepStart = performance.now();
  await fetch('/api/checkout', { method: 'POST' });
  metrics.steps.push({ name: 'checkout', ms: performance.now() - stepStart });

  metrics.total = performance.now() - start;
  return metrics;
}

// Run multiple iterations
async function benchmark(iterations = 100) {
  const results = [];
  for (let i = 0; i < iterations; i++) {
    await setupTestState(); // Reset state each run
    results.push(await runScenario());
  }
  return analyzeResults(results);
}
```

### 3. Cleanup

```javascript
async function cleanup() {
  await db.reset();
  // Or restore to known good state
}
```

### Key Considerations

- Isolate test database (don't use production)
- Reset state between iterations for consistency
- Measure individual steps AND total time
- Account for cold starts vs warm runs
- Consider concurrent users for realistic load
