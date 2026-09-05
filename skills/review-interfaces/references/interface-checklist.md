# Interface Checklist — Code Examples

Annotated BAD/GOOD examples for each category in the Interface Checklist. Use these as reference when classifying findings during a review.

---

## Pit of Success

**What to look for:** multiple ways to achieve the same result, consecutive same-type params, ambiguous defaults, easy to misuse without error.

**Overlapping Props:**
```tsx
// BAD: Two ways to set button text
<Button label="Save" />
<Button>Save</Button>
<Button label="Save">Cancel</Button>  // Which wins?

// GOOD: One way
<Button>Save</Button>
```

**Consecutive Same-Type Params:**
```typescript
// BAD: Easy to transpose
function copyFile(source: string, destination: string) { ... }
copyFile("/tmp/b.txt", "/tmp/a.txt");  // Swapped — no error

// GOOD: Distinct types or named params
function copyFile(opts: { source: string; destination: string }) { ... }
copyFile({ source: "/tmp/a.txt", destination: "/tmp/b.txt" });
```

**Ambiguous Default:**
```python
# BAD: Does retry=True mean "retry on failure" or "this is a retry"?
def fetch(url, retry=True): ...

# GOOD: Clear intent
def fetch(url, max_retries=3): ...
```

---

## Naming & Readability

**What to look for:** names that don't describe behavior, inconsistent vocabulary, asymmetric pairs, generic names.

**Inconsistent Vocabulary:**
```typescript
// BAD: Mixed terms for the same concept
class UserService {
  removeUser(id: string) { ... }
  deleteAccount(id: string) { ... }
  destroySession(id: string) { ... }
}

// GOOD: Consistent
class UserService {
  deleteUser(id: string) { ... }
  deleteAccount(id: string) { ... }
  deleteSession(id: string) { ... }
}
```

**Generic Names:**
```typescript
// BAD: What does "handle" do?
function handleData(data: any) { ... }

// GOOD: Specific
function validateOrder(order: Order): ValidationResult { ... }
```

**Asymmetric Pairs:**
```typescript
// BAD: open exists but no close
class Connection {
  open() { ... }
  terminate() { ... }  // Should be close()
}

// GOOD: Symmetric
class Connection {
  open() { ... }
  close() { ... }
}
```

---

## Signature Design

**What to look for:** too many params, boolean flags, weak types, inconsistent ordering, returning null instead of empty collections.

**Too Many Params:**
```typescript
// BAD: 6 positional params
function createUser(name: string, email: string, role: string,
  department: string, active: boolean, sendWelcome: boolean) { ... }

// GOOD: Options object
interface CreateUserOptions {
  name: string;
  email: string;
  role: Role;
  department?: string;
  sendWelcomeEmail?: boolean;
}
function createUser(options: CreateUserOptions) { ... }
```

**Boolean Flag:**
```typescript
// BAD: What does `true` mean at the call site?
fetchUsers(true);

// GOOD: Named option
fetchUsers({ includeInactive: true });

// GOOD: Separate function (if the behavior is substantially different)
fetchAllUsers();
fetchActiveUsers();
```

**Weak Types:**
```typescript
// BAD: Any string accepted
function setStatus(status: string) { ... }
setStatus("actve");  // Typo — no error

// GOOD: Constrained type
type Status = "active" | "inactive" | "pending";
function setStatus(status: Status) { ... }
```

**Returning Null vs Empty:**
```typescript
// BAD: Callers must null-check
function getItems(): Item[] | null { ... }
const count = getItems()?.length ?? 0;  // Every caller

// GOOD: Empty collection
function getItems(): Item[] { ... }
const count = getItems().length;  // Clean
```

---

## Surface Area & Encapsulation

**What to look for:** public members that should be private, exposed internals, missing explicit exports, leaked dependency types, exposed mutable state.

**Leaking Internals:**
```typescript
// BAD: Implementation detail in public interface
class UserCache {
  public cache: Map<string, User> = new Map();  // Callers depend on Map
  public getUser(id: string) { return this.cache.get(id); }
}

// GOOD: Hide the implementation
class UserCache {
  private cache = new Map<string, User>();
  public getUser(id: string): User | undefined {
    return this.cache.get(id);
  }
}
```

**Leaking Dependency Types:**
```typescript
// BAD: Exposes internal dependency in public interface
import { AxiosResponse } from "axios";
export function fetchUser(id: string): Promise<AxiosResponse<User>> { ... }

// GOOD: Wrap the dependency
export function fetchUser(id: string): Promise<User> { ... }
```

**Missing Explicit Exports:**
```typescript
// BAD: Everything is importable (barrel exports all)
export * from "./internals";
export * from "./helpers";

// GOOD: Explicit public surface
export { UserService } from "./UserService";
export type { User, CreateUserOptions } from "./types";
```

---

## Flexibility & YAGNI

**What to look for:** unused parameters, over-abstraction, under-constrained types, premature generalization.

**Over-Configured:**
```tsx
// BAD: 12 props, most never used
<DataTable
  data={rows}
  sortable={true}
  filterable={true}
  groupBy={null}
  pivotable={false}
  exportFormats={["csv"]}
  virtualScroll={true}
  rowHeight={40}
  headerRenderer={null}
  cellRenderer={null}
  onRowClick={null}
  theme="default"
/>

// GOOD: Start minimal, add props when callers need them
<DataTable data={rows} onRowClick={handleClick} />
```

**Under-Constrained Types:**
```typescript
// BAD: Allows invalid states
interface Task {
  status: string;
  completedAt: Date | null;
  // status can be "active" while completedAt is set — invalid
}

// GOOD: Invalid states unrepresentable
type Task =
  | { status: "active"; completedAt: null }
  | { status: "completed"; completedAt: Date };
```

**Premature Abstraction:**
```typescript
// BAD: Abstract factory for one implementation
interface NotificationSender { send(msg: Message): void; }
class EmailNotificationSender implements NotificationSender { ... }
class NotificationSenderFactory {
  create(type: string): NotificationSender { ... }
}

// GOOD: Just a function (add abstraction when a second sender appears)
function sendEmailNotification(msg: Message): void { ... }
```

---

## Composition & Extensibility

**What to look for:** deep inheritance, god objects, single responsibility violations, Law of Demeter violations, mixed logic and presentation.

**God Component:**
```tsx
// BAD: Does everything
function UserDashboard() {
  // Fetches user data
  // Renders profile form
  // Handles avatar upload
  // Manages notification preferences
  // Shows billing info
  return <div>...</div>;
}

// GOOD: Composed from focused components
function UserDashboard() {
  return (
    <DashboardLayout>
      <UserProfile />
      <NotificationPreferences />
      <BillingOverview />
    </DashboardLayout>
  );
}
```

**Law of Demeter Violation:**
```typescript
// BAD: Reaching through chain
function getShippingCity(order: Order): string {
  return order.getCustomer().getAddress().getCity();
}

// GOOD: Ask the object directly
function getShippingCity(order: Order): string {
  return order.getShippingCity();
}
```

**Deep Inheritance:**
```typescript
// BAD: Fragile hierarchy
class Animal { ... }
class Mammal extends Animal { ... }
class DomesticAnimal extends Mammal { ... }
class Dog extends DomesticAnimal { ... }

// GOOD: Composition
interface Animal { name: string; move(): void; }
interface Domestic { owner: string; }
type Pet = Animal & Domestic;
```
