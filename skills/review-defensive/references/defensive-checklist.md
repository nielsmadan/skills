# Defensive Review — Examples, Mechanisms, Sources

BAD/GOOD examples per category, the exhaustiveness mechanism in each language, and the sources behind the checklist. Quotes were checked against the linked pages in October 2026.

---

## 1. Closed-World Branching

**Phony default — the last case handled by elimination:**
```typescript
type PaymentKind = 'card' | 'sepa' | 'paypal';

// BAD: `else` means "must be paypal". Adding 'applepay' compiles and refunds via PayPal.
function refund(p: Payment) {
  if (p.kind === 'card') refundCard(p);
  else if (p.kind === 'sepa') refundSepa(p);
  else refundPaypal(p);
}

// GOOD: every case named; a new kind is a compile error at assertNever
function assertNever(x: never): never {
  throw new Error(`unhandled value: ${JSON.stringify(x)}`);
}
function refund(p: Payment) {
  switch (p.kind) {
    case 'card': return refundCard(p);
    case 'sepa': return refundSepa(p);
    case 'paypal': return refundPaypal(p);
    default: return assertNever(p.kind);
  }
}
```

```python
# GOOD (Python 3.11+, or typing_extensions >= 4.1)
from typing import assert_never

def refund(p: Payment) -> None:
    if p.kind is Kind.CARD:
        refund_card(p)
    elif p.kind is Kind.SEPA:
        refund_sepa(p)
    elif p.kind is Kind.PAYPAL:
        refund_paypal(p)
    else:
        assert_never(p.kind)
```

**Negated predicate:**
```python
# BAD: written when only ACTIVE and CANCELLED existed; PAUSED is now charged
if sub.status != Status.CANCELLED:
    charge(sub)

# GOOD: state the positive case
if sub.status is Status.ACTIVE:
    charge(sub)
```

**Lookup map with a fallback:**
```typescript
// BAD: a missing handler silently becomes the generic one
const handler = handlers[event.kind] ?? genericHandler;

// GOOD: the map must cover every key, or it does not compile
const handlers: Record<EventKind, Handler> = { created: onCreated, deleted: onDeleted };
```

**Wildcard arm that hides new variants (Rust):**
```rust
// BAD: a new Shape variant falls into `_` silently
match shape { Shape::Circle(r) => area_circle(r), _ => area_square(shape) }

// GOOD: no wildcard; adding a variant fails to compile
match shape { Shape::Circle(r) => area_circle(r), Shape::Square(s) => s * s }
```

## 2. Unknown Values From Outside

```typescript
// BAD: an unknown status throws inside the decoder, failing the whole page
const status = StatusSchema.parse(raw.status); // z.enum([...])

// GOOD: decode to known-or-unknown; each consumer handles unknown on purpose
type Status = { kind: 'known'; value: KnownStatus } | { kind: 'unknown'; raw: string };

switch (s.kind) {
  case 'known': return render(s.value);
  case 'unknown':
    log.warn('unrecognized status', { raw: s.raw });
    return renderUnsupported();
}
```

```swift
// GOOD: @unknown default warns at compile time if a *known* case is missing,
// and still handles values from a newer SDK at runtime
switch status {
case .active: ...
case .cancelled: ...
@unknown default: logUnknown(status); showUnsupported()
}
```

## 3. Silent Failure and Masking Defaults

```javascript
// BAD: a missing price becomes free
const total = items.reduce((sum, i) => sum + (i.price ?? 0), 0);

// GOOD: absence is a contract break — fail where it happened
const total = items.reduce((sum, i) => {
  if (i.price == null) throw new Error(`item ${i.id} has no price`);
  return sum + i.price;
}, 0);
```

```python
# BAD
try:
    sync_account(acct)
except Exception:
    pass

# GOOD: catch what you can handle; let the rest propagate
try:
    sync_account(acct)
except RateLimited as e:
    schedule_retry(acct, after=e.retry_after)
```

## 4. Invariants and Assertions

```python
# BAD: assert as input validation — removed under `python -O`
def withdraw(acct, amount):
    assert amount > 0
    ...

# GOOD: input check is a real error; assert guards an internal invariant
def withdraw(acct, amount):
    if amount <= 0:
        raise ValueError("amount must be positive")
    acct.balance -= amount
    assert acct.balance >= 0, "overdraft should have been rejected upstream"
```

## 5. Bounds and Resources

```python
# BAD: no timeout — a hung upstream holds this worker forever
resp = requests.get(url)

# GOOD
resp = requests.get(url, timeout=(3.05, 10))  # connect, read
```

Retries: cap the attempts, back off exponentially, add jitter, and keep one retry layer rather than stacking them.

---

## Exhaustiveness mechanism by language

| Language | Compile-time exhaustiveness | What defeats it | Unknown runtime values |
|---|---|---|---|
| TypeScript | `never` check in `default` (handbook "Exhaustiveness checking"); typescript-eslint `switch-exhaustiveness-check` | A `default` that does work. With `considerDefaultExhaustiveForUnions`, any `default` silences the rule | Decode to a known-or-unknown union |
| Python | `typing.assert_never` (3.11+, `typing_extensions` 4.1+); mypy `exhaustive-match`, pyright `reportMatchNotExhaustive` | `else:` / `case _:` doing work | Explicit unknown member or wrapper |
| Rust | `match` is exhaustive by default | `_ =>` arm; clippy `wildcard_enum_match_arm`, `match_wildcard_for_single_variants` catch it | `#[non_exhaustive]` forces downstream crates to keep a wildcard arm |
| Swift | `switch` must be exhaustive | `default` | `@unknown default` matches anything but warns if a known case is unmatched (SE-0192) |
| Kotlin | `when` on sealed/enum without `else`; non-exhaustive `when` *statements* on enum/sealed/Boolean warn since 1.6 | `else ->` | — |
| Java 21 | Pattern `switch` over sealed types needs no `default` (JEP 441) | A manual `default` | Compiler inserts a synthetic throwing `default` |
| C/C++ | `-Wswitch` (in `-Wall`) | Any `default:` suppresses `-Wswitch`; `-Wswitch-enum` warns even with a `default` | — |
| Go | None built in | — | `exhaustive` linter; `default-signifies-exhaustive` is off by default, so `default` does not count |
| Protobuf | — | — | Open enums keep unknown numeric values; Java's `getName` returns `UNRECOGNIZED` |

---

## Sources

**Exhaustiveness and catch-alls**
- McConnell, *Code Complete* 2nd ed., case statements (draft chapters: https://jmvidal.cse.sc.edu/library/mcconnell04a.pdf): "You might sometimes have only one case remaining and decide to code that case as the default clause. Though sometimes tempting, that's dumb. … you lose the ability to detect errors with the default clause." Also: "Such case statements break down under modification." and "Use the default clause to detect errors."
- JEP 441, https://openjdk.org/jeps/441: "Manually writing a `default` clause in this situation is not only irritating but actually pernicious, since the compiler can do a better job of checking exhaustiveness without one."
- GCC warning options, https://gcc.gnu.org/onlinedocs/gcc/Warning-Options.html: `-Wswitch` — "(The presence of a `default` label prevents this warning.)"; `-Wswitch-enum` — "gives a warning about an omitted enumeration code even if there is a `default` label."
- typescript-eslint `switch-exhaustiveness-check`, https://typescript-eslint.io/rules/switch-exhaustiveness-check/
- TypeScript handbook, Narrowing → Exhaustiveness checking, https://www.typescriptlang.org/docs/handbook/2/narrowing.html
- Python typing guide, https://typing.python.org/en/latest/guides/unreachable.html: "if you add another member to the enum … but don't update the `match` statement, the type checker will give an error".
- Clippy lints, https://rust-lang.github.io/rust-clippy/master/index.html: `wildcard_enum_match_arm` — "New enum variants added by library updates can be missed."
- Rust reference, `non_exhaustive`, https://doc.rust-lang.org/reference/attributes/type_system.html
- Swift SE-0192, https://github.com/swiftlang/swift-evolution/blob/main/proposals/0192-non-exhaustive-enums.md: "`@unknown default` matches any value … However, the compiler will produce a *warning* if all known elements of the enum have not already been matched."
- Kotlin 1.6 what's new, https://kotlinlang.org/docs/whatsnew16.html
- Go `exhaustive`, https://pkg.go.dev/github.com/nishanths/exhaustive/passes/exhaustive: "Including a default case does not make a switch statement exhaustive."
- CWE-478, https://cwe.mitre.org/data/definitions/478.html: "A good practice is to reserve the default case for error handling." — consistent with the above: the default reports, it does not do a known case's work.
- CWE-396, https://cwe.mitre.org/data/definitions/396.html: broad catches are dangerous "if the program grows and begins to throw new types of exceptions. The new exception types will not receive any attention."

**External data and evolving APIs**
- GitHub REST API breaking changes, https://docs.github.com/en/rest/about-the-rest-api/breaking-changes: additive (non-breaking) changes include "Adding enum values".
- Google AIP-180, https://google.aip.dev/180: "be aware that it is possible that user code does not handle new values gracefully."
- Protobuf enum behavior, https://protobuf.dev/programming-guides/enum/
- RFC 9413 (critique of Postel's law), https://www.rfc-editor.org/rfc/rfc9413.html: "Choosing to generate fatal errors for unspecified conditions instead of attempting error recovery can ensure that faults receive attention."
- Fowler, Tolerant Reader, https://martinfowler.com/bliki/TolerantReader.html
- Hyrum's Law, https://www.hyrumslaw.com/
- King, "Parse, don't validate", https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/ (defines "shotgun parsing")
- Minsky, "Effective ML Revisited", https://blog.janestreet.com/effective-ml-revisited/ ("Make illegal states unrepresentable")

**Fail fast, assertions, over-defense**
- Shore, "Fail Fast", https://martinfowler.com/ieeeSoftware/failFast.pdf: "The program continues working right after an error but fails in strange ways later on."
- Holzmann, "The Power of Ten", https://spinroot.com/gerard/pdf/P10.pdf — rule 2 (fixed loop bounds), rule 5 (assertions), rule 7 (check return values).
- *The Pragmatic Programmer* tips ("Crash Early", "Use Assertions to Prevent the Impossible"), https://pragprog.com/tips/
- McConnell, *Code Complete* (same PDF): "Too much defensive programming creates problems of its own." Barricades: "Once the data has been accepted by the class's public methods, the class's private methods can assume the data is safe."
- Armstrong thesis §4.4, https://erlang.org/download/armstrong_thesis_2003.pdf: "Let it crash." / "Do not program defensively."
- CWE-252 (unchecked return value), https://cwe.mitre.org/data/definitions/252.html
- Google Python style guide on catch-all `except`, https://google.github.io/styleguide/pyguide.html

**Bounds and resources**
- AWS Builders' Library, "Timeouts, retries, and backoff with jitter", https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/: "set a timeout on any remote call … This includes both a connection timeout and a request timeout."
- Google SRE book, "Addressing Cascading Failures", https://sre.google/sre-book/addressing-cascading-failures/: "Limit retries per request." and the server-wide retry budget.
