# Judgment Checklist (full catalogue)

Load when reviewing files. Every item here assumes `typescript-eslint` already owns
the mechanical layer — nothing below is a lint finding.

## 1. Type modeling & design

The core value. A linter checks that types are *consistent*; only a human checks that they're *right*.

- **Invalid states are representable.** Flag a type where contradictory or impossible combinations can be constructed — e.g. `{ isLoading: boolean; data?: T; error?: E }` allows loading-with-data-and-error simultaneously. Recommend a discriminated union so illegal states won't type-check. *(Effective TS Item 29 — "make invalid states unrepresentable.")*
- **Bag-of-optionals instead of a union of interfaces.** `interface Shape { kind; radius?; sideLength? }` should be `type Shape = Circle | Square`, each with only its own required fields. *(Effective TS Item 34.)*
- **Outputs wider than callers need.** A function whose return type includes `| null`, `| undefined`, or `| string` that no caller actually wants forces defensive handling everywhere. Be liberal in inputs, strict in outputs. *(Effective TS Item 30.)*
- **`null`/`undefined` scattered through the interior** instead of pushed to the perimeter. Flag types that bake nullability into shared aliases or sprinkle nullable fields deep in the model; normalize at the boundary so interior code deals in non-null values. *(Effective TS Items 32/33.)*
- **Optional overload.** Many `?` fields "just in case" multiply the states callers must handle. Flag types that are mostly-optional when the real object usually has everything. *(Effective TS Item 37.)*
- **In-band sentinels.** `-1`/`0`/`""` overloaded to mean "not found"/"none" instead of a distinct type or `null`. *(Effective TS Item 36.)*
- **Hand-copied shapes that will drift.** A type that manually restates a subset of another type's fields should derive from it via `Pick`/`Omit`/`Partial`/`Required`/`Record`/`ReturnType<typeof fn>` so it stays in sync when the source changes. Judgment call: derive when there's a real source-of-truth relationship; don't force utility-type gymnastics where an independent type is genuinely clearer. *(Effective TS Item 15.)*
- **Interchangeable primitives that shouldn't be.** Several `string` IDs (`userId`, `postId`) or unit-bearing `number`s that can be swapped at a call site with no error — consider a branded/nominal type *only if* mix-ups are a real risk here. Note the cost (ergonomics); don't recommend brands reflexively. *(Effective TS Item 64.)*

## 2. Inference vs. annotation

Default to inference; annotate only when it **serves a purpose**. The judgment is *which* is which — the trivial cases (`const n: number = 5`) are ESLint's `no-inferrable-types`, so don't report those.

- **Prefer inference where the initializer already yields the right type.** Flag annotations that merely restate an inferred type *and* cost you nothing to drop — but only when removing them changes nothing (don't flag an annotation that's narrowing or widening on purpose).
- **Do annotate hand-authored complex objects** (config objects, fixtures, lookup tables, large literals). An annotation there surfaces a mistake **at the definition site** immediately, instead of as a confusing error at some distant use site — this is a *good* annotation, flag its **absence** on nontrivial literals, not its presence.
- **Prefer `satisfies` over a colon annotation for literals when you want validation *and* narrow inferred types.** `const routes = {...} satisfies Record<string, Handler>` type-checks the literal while keeping the exact keys for autocomplete; `const routes: Record<string, Handler> = {...}` widens them away. Flag `: WideType = { literal }` where narrow keys/values are later needed. *(Total TypeScript / Pocock; Effective TS Item 9.)*
- **`as` is not an annotation.** Flag `const x = { ... } as SomeType` used to *label* a literal: `as` silences errors rather than checking, so a missing/renamed field passes silently and breaks at runtime. Recommend a colon annotation or `satisfies`. *(This is the judgment cousin of the linted redundant-cast rule — here the cast is being misused as documentation.)*
- **Return-type annotations on public API boundaries, not internals.** Recommend an explicit return type on exported/public functions (locks the contract, catches accidental widening). Do **not** flag missing return types on internal/local functions where inference is fine and annotations are noise. *(Conditional — weigh the function's visibility. Pocock: "don't use return types, unless…"; Effective TS Items 30/67.)*
- **Export types that appear in a public API's signatures.** Flag an exported function whose params/return reference an un-exported type — consumers can't name it. *(Effective TS Item 67.)*

## 3. Casts & escape hatches — the judgment residue

ESLint flags casts that are *provably redundant* and *provably unsafe*. What's left for a human:

- **A cast that compiles but hides a wrong upstream type.** `return rows as OrderDTO[]` where `rows` is `Record<string, unknown>[]`: the cast is load-bearing (lint won't call it unnecessary) but it exists only because the DB layer is mistyped. The fix is upstream — type the query result — not the cast. This is the highest-value cast finding and it's pure judgment.
- **A cast/`any` standing in for validation at a trust boundary.** `JSON.parse(s) as Config`, `res.data as User`, `event.target as HTMLInputElement` assert a shape that was never checked. For parsed/network/DOM data, recommend a runtime guard or schema (the assertion is a claim, not a proof). Judgment: legitimate at genuinely-safe boundaries, a bug waiting to happen for external data.
- **`any`/suppression that masks a modeling gap.** Where `any` (or a `@ts-expect-error` that lint permits because it has a comment) is hiding a type that *could* be modeled, say what the right type is. The point isn't "there's an `any`" (lint's job) — it's "here's the model that removes the need for it."

State your reasoning for each finding. "Cast hides that `getUser` is mistyped as `any`" is a finding; "there's a cast here" is not (and is probably already lint-flagged).

## Severity

- **Critical**: a type-modeling flaw that lets illegal state reach runtime and cause a crash/corruption (invalid-states-representable in a load-bearing model; a boundary cast on unvalidated external data that will throw on malformed input).
- **High**: a modeling problem that will cause bugs or force error-prone handling as the code evolves (outputs too wide, cast hiding a wrong upstream type, hand-copied type that will silently drift).
- **Medium**: annotation/inference misuse (`as`-as-label, missing definition-site annotation on a complex literal, missing public-API return type), sentinel values, over-optional types.
- **Suggestion**: nominal-type opportunities, DRY-via-utility-type refactors where the current code is merely repetitive, not buggy.
