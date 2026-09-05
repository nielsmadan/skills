# Clean Code Checklist — Code Examples

Annotated BAD/GOOD examples for each category. Language-agnostic pseudocode (JavaScript-like syntax for readability). Use these as reference when classifying findings during a review.

---

## 1. SOLID Principles

**What to look for:** classes/modules with multiple reasons to change, type-checking switches that grow with new variants, subclasses that break parent contracts, fat interfaces with unused methods, high-level code importing low-level implementations.

**Single Responsibility (SRP) — multiple concerns in one class:**
```javascript
// BAD: handles business logic, persistence, and formatting
class OrderService {
  calculateTotal(order) { ... }
  saveToDatabase(order) { ... }
  formatAsEmail(order) { ... }
}

// GOOD: one responsibility per class
class OrderCalculator { calculateTotal(order) { ... } }
class OrderRepository { save(order) { ... } }
class OrderEmailFormatter { format(order) { ... } }
```

**Open/Closed (OCP) — modifying existing code for every new variant:**
```javascript
// BAD: must edit function for each new type
function getDiscount(type) {
  if (type === "premium") return 0.2;
  if (type === "vip") return 0.3;
  // add new type here every time...
}

// GOOD: extend via new implementations
class PremiumDiscount { get() { return 0.2; } }
class VipDiscount { get() { return 0.3; } }
// new types = new class, no existing code changes
```

**Liskov Substitution (LSP) — subclass breaks parent contract:**
```javascript
// BAD: child violates parent behavior
class Bird { fly() { ... } }
class Penguin extends Bird {
  fly() { throw new Error("Can't fly"); } // breaks substitutability
}

// GOOD: model capabilities correctly
class Bird { move() { ... } }
class FlyingBird extends Bird { fly() { ... } }
class Penguin extends Bird { swim() { ... } }
```

**Interface Segregation (ISP) — forcing unused methods:**
```javascript
// BAD: implementors must stub unused methods
interface Worker {
  code();
  design();
  test();
  manageSprints();
}

// GOOD: split into focused interfaces
interface Coder { code(); }
interface Designer { design(); }
interface Tester { test(); }
```

**Dependency Inversion (DIP) — high-level depends on low-level:**
```javascript
// BAD: direct dependency on concrete implementation
class OrderService {
  constructor() {
    this.db = new PostgresDatabase(); // locked to Postgres
  }
}

// GOOD: depend on abstraction
class OrderService {
  constructor(repository) { // any repository works
    this.repository = repository;
  }
}
```

---

## 2. Foundational Principles

**What to look for:** copy-pasted logic across files, abstractions built for hypothetical futures, clever solutions where simple ones exist, late validation that lets bad data propagate.

**DRY — duplicated logic:**
```javascript
// BAD: same validation in two places
function createUser(data) {
  if (!data.email || !data.email.includes("@")) throw new Error("Invalid");
  // ...
}
function updateUser(data) {
  if (!data.email || !data.email.includes("@")) throw new Error("Invalid");
  // ...
}

// GOOD: single source of truth
function validateEmail(email) {
  if (!email || !email.includes("@")) throw new Error("Invalid");
}
function createUser(data) { validateEmail(data.email); ... }
function updateUser(data) { validateEmail(data.email); ... }
```

**YAGNI — speculative generality:**
```javascript
// BAD: building for hypothetical future needs
class DataProcessor {
  constructor(options = {}) {
    this.format = options.format || "json";     // only json is ever used
    this.compression = options.compression;      // never used
    this.encryption = options.encryption;        // never used
    this.retryPolicy = options.retryPolicy;      // never used
  }
}

// GOOD: only what's needed now
class DataProcessor {
  process(data) {
    return JSON.stringify(data);
  }
}
```

**KISS — unnecessary complexity:**
```javascript
// BAD: over-engineered for a simple check
function isEven(n) {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(((n & 1) === 0) ? true : false);
    }, 0);
  });
}

// GOOD: straightforward
function isEven(n) {
  return n % 2 === 0;
}
```

**Fail Fast — late validation:**
```javascript
// BAD: processes data before checking validity
function processPayment(order) {
  const total = calculateTotal(order);    // wasted work
  const tax = calculateTax(order);        // wasted work
  if (!order.paymentMethod) throw new Error("No payment method");
  // ...
}

// GOOD: validate first
function processPayment(order) {
  if (!order.paymentMethod) throw new Error("No payment method");
  const total = calculateTotal(order);
  const tax = calculateTax(order);
  // ...
}
```

---

## 3. Design Principles

**What to look for:** long method chains through objects, business logic mixed with infrastructure, deep inheritance trees, functions with hidden side effects, getters that mutate state.

**Law of Demeter — reaching through objects:**
```javascript
// BAD: train wreck
const street = order.getCustomer().getAddress().getStreet();

// GOOD: ask the nearest object
const street = order.getDeliveryStreet();
```

**Separation of Concerns — mixed responsibilities:**
```javascript
// BAD: UI handler contains business logic and persistence
function handleSubmit(form) {
  const price = form.quantity * form.unitPrice * (1 - form.discount);
  await db.orders.insert({ ...form, price });
  showToast("Order placed");
}

// GOOD: separate layers
function calculatePrice(quantity, unitPrice, discount) {
  return quantity * unitPrice * (1 - discount);
}
function handleSubmit(form) {
  const price = calculatePrice(form.quantity, form.unitPrice, form.discount);
  await orderRepository.create({ ...form, price });
  showToast("Order placed");
}
```

**Composition over Inheritance — deep hierarchy for code reuse:**
```javascript
// BAD: inheritance just for shared behavior
class Animal { eat() { ... } }
class Dog extends Animal { bark() { ... } }
class RobotDog extends Dog { recharge() { ... } } // RobotDog can eat?

// GOOD: compose behaviors
class RobotDog {
  constructor() {
    this.barker = new Barker();
    this.battery = new Battery();
  }
}
```

**Principle of Least Astonishment — surprising behavior:**
```javascript
// BAD: getter has side effect
get totalPrice() {
  this.lastAccessed = Date.now(); // surprise mutation
  return this.items.reduce((sum, i) => sum + i.price, 0);
}

// GOOD: getter is pure
get totalPrice() {
  return this.items.reduce((sum, i) => sum + i.price, 0);
}
```

**Tell Don't Ask — querying then acting externally:**
```javascript
// BAD: ask for state, act on it
if (account.getBalance() >= amount) {
  account.setBalance(account.getBalance() - amount);
}

// GOOD: tell the object what to do
account.withdraw(amount); // object manages its own state
```

**Command-Query Separation — method does both:**
```javascript
// BAD: mutates and returns
function getNextItem(queue) {
  const item = queue.shift(); // mutates queue
  return item;                // and returns data
}

// GOOD: separate commands from queries
function peek(queue) { return queue[0]; }        // query
function dequeue(queue) { return queue.shift(); } // command (name signals mutation)
```

**Encapsulation — exposed internals:**
```javascript
// BAD: internal state directly accessible
class ShoppingCart {
  items = [];       // public — anyone can mutate
}
cart.items.push(x); // bypasses any validation

// GOOD: controlled access
class ShoppingCart {
  #items = [];
  addItem(item) {
    if (this.#items.length >= 100) throw new Error("Cart full");
    this.#items.push(item);
  }
  getItems() { return [...this.#items]; } // defensive copy
}
```

**Cohesion & Coupling — low cohesion class:**
```javascript
// BAD: unrelated methods sharing a class
class Utils {
  formatDate(d) { ... }
  sendEmail(to, body) { ... }
  resizeImage(img, w, h) { ... }
}

// GOOD: cohesive groupings
class DateFormatter { format(d) { ... } }
class EmailSender { send(to, body) { ... } }
class ImageResizer { resize(img, w, h) { ... } }
```

---

## 4. Code Smells

**What to look for:** classes over ~300 lines, methods over ~20 lines, methods that use another class's data more than their own, data-only classes with no behavior, identical code blocks, long chains, unused code.

**God Class:**
```javascript
// BAD: one class does everything
class Application {
  authenticateUser() { ... }
  processPayment() { ... }
  sendNotification() { ... }
  generateReport() { ... }
  migrateDatabase() { ... }
  // 500+ lines...
}

// GOOD: split by responsibility
class AuthService { ... }
class PaymentProcessor { ... }
class NotificationService { ... }
```

**Long Method:**
```javascript
// BAD: one method with multiple phases
function processOrder(order) {
  // 15 lines of validation...
  // 20 lines of price calculation...
  // 10 lines of inventory check...
  // 15 lines of payment processing...
  // 10 lines of notification...
}

// GOOD: extract phases
function processOrder(order) {
  validate(order);
  const totals = calculateTotals(order);
  reserveInventory(order);
  chargePayment(order, totals);
  notifyCustomer(order);
}
```

**Feature Envy — method uses another object's data heavily:**
```javascript
// BAD: this method belongs on Customer
function getCustomerDisplayName(customer) {
  if (customer.title) return customer.title + " " + customer.lastName;
  return customer.firstName + " " + customer.lastName;
}

// GOOD: move to Customer
class Customer {
  getDisplayName() {
    if (this.title) return this.title + " " + this.lastName;
    return this.firstName + " " + this.lastName;
  }
}
```

**Data Class — no behavior, just fields:**
```javascript
// BAD: pure data container, logic elsewhere
class Rectangle { width; height; }
function area(rect) { return rect.width * rect.height; }
function perimeter(rect) { return 2 * (rect.width + rect.height); }

// GOOD: behavior lives with data
class Rectangle {
  constructor(width, height) { this.width = width; this.height = height; }
  area() { return this.width * this.height; }
  perimeter() { return 2 * (this.width + this.height); }
}
```

**Primitive Obsession:**
```javascript
// BAD: strings for everything
function createUser(name, email, role, currency, phoneCountryCode) { ... }
createUser("Jo", "bad-email", "superadmin", "FAKE", "000"); // no validation

// GOOD: value objects
function createUser(name, email: Email, role: Role, currency: Currency) { ... }
// Email, Role, Currency validate on construction
```

**Long Parameter List:**
```javascript
// BAD: too many params
function createEvent(title, date, location, organizer, category,
                     isPublic, maxAttendees, description) { ... }

// GOOD: parameter object
function createEvent(config: EventConfig) { ... }
// or use a builder pattern
```

**Shotgun Surgery — one change touches many files:**
```javascript
// BAD: adding a user field requires changes in 6 places
// user.js, userForm.js, userApi.js, userValidator.js, userSerializer.js, userTest.js
// all need manual updates for each new field

// GOOD: centralized schema drives everything
// schema.js defines fields once; form, API, validation derive from it
```

**Dead Code:**
```javascript
// BAD: unused function still in codebase
function legacyCalculation(data) { ... } // nothing calls this

// BAD: unreachable branch
function process(x) {
  return x * 2;
  console.log("done"); // never reached
}

// GOOD: delete dead code — version control has the history
```

**Data Clumps — same group of params travel together:**
```javascript
// BAD: same trio passed everywhere
function distanceBetween(x1, y1, z1, x2, y2, z2) { ... }
function translate(x, y, z, dx, dy, dz) { ... }

// GOOD: group into a type
class Point3D { constructor(x, y, z) { ... } }
function distanceBetween(a: Point3D, b: Point3D) { ... }
```

---

## 5. Readability & Structure

**What to look for:** deeply nested conditions, cryptic variable names, functions longer than a screen, "what" comments instead of "why" comments, imperative code where declarative is clearer.

**Guard Clauses / Early Returns:**
```javascript
// BAD: deep nesting
function process(user) {
  if (user) {
    if (user.isActive) {
      if (user.hasPermission) {
        return doWork(user);
      }
    }
  }
  return null;
}

// GOOD: guard clauses
function process(user) {
  if (!user) return null;
  if (!user.isActive) return null;
  if (!user.hasPermission) return null;
  return doWork(user);
}
```

**Meaningful Names:**
```javascript
// BAD: cryptic abbreviations
const d = new Date() - u.c;
if (d > 86400000) { ... }

// GOOD: self-documenting
const millisSinceCreation = Date.now() - user.createdAt;
const ONE_DAY_MS = 24 * 60 * 60 * 1000;
if (millisSinceCreation > ONE_DAY_MS) { ... }
```

**Small Focused Functions:**
```javascript
// BAD: section comments = function does too much
function processOrder(order) {
  // Validate order
  if (!order.items) throw new Error("No items");
  if (!order.customer) throw new Error("No customer");
  // Calculate totals
  let subtotal = 0;
  for (const item of order.items) {
    subtotal += item.price * item.quantity;
  }
  const tax = subtotal * 0.1;
  // Save
  db.orders.save({ ...order, subtotal, tax });
}

// GOOD: composed from focused functions
function processOrder(order) {
  validateOrder(order);
  const totals = calculateTotals(order);
  saveOrder(order, totals);
}
```

**Comments — "why" not "what":**
```javascript
// BAD: restates the code
// Loop through users and check if active
for (const user of users) {
  if (user.isActive) { ... }
}

// GOOD: explains reasoning
// Filter inactive users first — downstream payment processor
// rejects batches containing any inactive accounts
const active = users.filter(u => u.isActive);
```

**Declarative over Imperative (when clearer):**
```javascript
// Imperative (verbose)
const activeNames = [];
for (const user of users) {
  if (user.isActive) {
    activeNames.push(user.name);
  }
}

// Declarative (preferred when clear)
const activeNames = users
  .filter(u => u.isActive)
  .map(u => u.name);

// Note: if a for loop is clearer or faster, that's fine. Clarity over dogma.
```
