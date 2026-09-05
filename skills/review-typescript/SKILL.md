---
name: review-typescript
description: TypeScript-specific code review focused on JUDGMENT-level type design a linter can't decide — type modeling (make invalid states unrepresentable), inference-vs-annotation calls, and casts/`any` that hide a real modeling problem. Deliberately does NOT duplicate typescript-eslint. Auto-invoked by `code-review` on TypeScript projects. Triggers "review typescript", "typescript review", "type design review".
argument-hint: '[--staged | --unpushed | --changed | --all | --multi]'
effort: high
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Review TypeScript

TypeScript review that covers what a **type-aware linter cannot decide for you** — how types are *modeled*, when to *annotate vs infer*, and whether a cast or `any` is papering over a design problem. These are judgment calls; the mechanical rules are ESLint's job.

## Relationship to typescript-eslint (read first)

**This skill assumes `typescript-eslint` handles the mechanical layer.** Do NOT re-flag anything a lint rule catches — that's noise and it duplicates CI. Specifically, do **not** report:

- Redundant/unnecessary assertions (`no-unnecessary-type-assertion`), explicit `any` (`no-explicit-any`), unsafe `any` flow (`no-unsafe-*`), non-null `!` (`no-non-null-assertion`)
- `@ts-ignore`/`@ts-expect-error` without a reason (`ban-ts-comment`)
- Floating/misused promises, `await`-thenable, throw/reject non-Error (`no-floating-promises`, `no-misused-promises`, `only-throw-error`)
- Dangerous built-ins `Function`/`{}`/wrapper objects (`no-unsafe-function-type`, `no-empty-object-type`, `no-wrapper-object-types`)
- Truthiness/nullish traps, `??` vs `||`, template-expression coercion (`strict-boolean-expressions`, `prefer-nullish-coalescing`, `restrict-template-expressions`)
- `import type`, `prefer-as-const`, trivially-inferrable annotations (`consistent-type-imports`, `prefer-as-const`, `no-inferrable-types`)
- Always-true/false conditions, single-use generics, exhaustive switches (`no-unnecessary-condition`, `no-unnecessary-type-parameters`, `switch-exhaustiveness-check`)

**One-time tooling recommendation (not a per-diff finding):** if the project's ESLint config is missing or isn't on `typescript-eslint` `strict-type-checked`, say so **once** at the top of the review and recommend enabling it — plus tsconfig `strict` and `noUncheckedIndexedAccess`. That single recommendation solves the whole mechanical class (including the classic "unnecessary cast slipped through" via `no-unnecessary-type-assertion`) far better than a reviewer eyeballing diffs. Then move on to the judgment work below.

Run on `.ts` / `.tsx` / `.mts` / `.cts`. Complements `review-cleancode` (SOLID/DRY/smells) — don't repeat it.

## Usage

```
/review-typescript                  # Review context-related code
/review-typescript --staged         # Review staged changes
/review-typescript --unpushed       # Review files changed across all unpushed commits
/review-typescript --changed        # Review unstaged changes
/review-typescript --all            # Full codebase audit (parallel agents)
/review-typescript --multi          # Also get external advisor opinions
```

## Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Context-related code | Files from the current conversation context. If no context, ask the user to specify files or use `--staged`/`--changed`/`--all`. |
| `--staged` | Staged changes | `git diff --cached --name-only` |
| `--unpushed` | Files changed across unpushed commits | `git diff --name-only $(git rev-list HEAD --not --remotes \| tail -1)^..HEAD` |
| `--changed` | Unstaged changes | `git diff --name-only` |
| `--all` | Full codebase | Glob `*.ts`/`*.tsx`/`*.mts`/`*.cts`, parallel agents |
| `--multi` | Add external opinions | Combines with any scope above; invokes `second-opinion --quick` |

`--unpushed` derives its range from `git rev-list HEAD --not --remotes` (oldest unpushed commit's parent → HEAD). If nothing is unpushed, or there is no remote/upstream (or the range walks back to the root commit) so it can't be determined reliably, stop and ask the user to pick another scope. Restrict the resolved file list to TypeScript extensions before reviewing.

## Workflow

1. **Determine scope** (see table) and filter to TypeScript files only.
2. **Read CLAUDE.md** in the repo root for project conventions.
3. **Check the lint baseline once.** Look for `eslint.config.*`/`.eslintrc*` and whether it extends `typescript-eslint` `strict-type-checked` (or `recommended-type-checked`). If absent, emit the one-time tooling recommendation above and note that mechanical findings are out of scope for this review.
4. **Review each file** against the three judgment categories (load `references/checklist.md`).
5. **Parallelize** if scope has >5 files: one sub-agent per category, merge and dedupe.
6. **External opinions** (if `--multi`): invoke `second-opinion --quick` with this prompt:

   ```
   Read-only TypeScript review. Assume typescript-eslint already handles mechanical rules — do NOT repeat lint-level findings. Focus on TYPE DESIGN judgment: are invalid states representable that shouldn't be? Are types modeled with unions of interfaces or a bag of optional fields? Are functions returning wider types than callers need? Is inference used where it could be, and are annotations added only where they serve a purpose (definition-site checking of complex literals, public-API contracts)? Do any casts/`any` compile but hide a wrong upstream type? 300 words or less.
   ```

   Wait for all external results before proceeding.
7. **Classify severity** and **report**, grouped by severity.

## Checklist (judgment only)

**Load `references/checklist.md`** before reviewing files — it carries the full bullet
catalogue for all three categories plus the severity definitions. The categories:

1. **Type modeling & design** — the core value. Invalid states representable, bag-of-optionals
   where a union belongs, outputs wider than callers need, nullability in the interior instead
   of at the perimeter, in-band sentinels, hand-copied shapes that will drift.
2. **Inference vs. annotation** — default to inference; annotate where it *serves a purpose*
   (definition-site checking of complex literals, public-API contracts). `satisfies` vs colon
   annotation vs `as`.
3. **Casts & escape hatches** — the residue after lint: a cast that compiles but hides a wrong
   upstream type, a cast standing in for validation at a trust boundary, `any` masking a
   modeling gap.

State your reasoning for each finding. "Cast hides that `getUser` is mistyped as `any`" is a
finding; "there's a cast here" is not (and is probably already lint-flagged).

## Output Format

```markdown
## TypeScript Review: {scope}

### Lint baseline
{One line: does the project run typescript-eslint strict-type-checked? If not, the one-time recommendation. Omit if it does.}

### Critical (illegal state can reach runtime)
- {file}:{line} — {category}: {description}
  **Why it's not a lint finding:** {what judgment this needed}
  **Impact:** {what breaks}
  **Fix:** {model change / boundary validation — with code}

### High (modeling problems that will cause bugs)
- {file}:{line} — {category}: {description}
  **Fix:** {solution}

### Medium (annotation/inference & type-design)
- {file}:{line} — {category}: {description} — {suggested change}

### Suggestions
- {opportunities}
```

If `--multi` was used, append one subsection per advisor that responded (titled with the advisor's name as reported by `second-opinion`), then a **Cross-Model Agreement** subsection.

## Examples

**Invalid state representable:**
> /review-typescript --staged

Finds a `FetchState` type `{ loading: boolean; data?: T; error?: string }` — nothing prevents `loading: true` with both `data` and `error` set. Reports High with a discriminated-union rewrite. Not a lint finding: the type is internally consistent; only a human knows the states are illegal.

**Cast hiding a mistyped source:**
> /review-typescript --changed

Finds `const total = order.items as LineItem[]` where `order.items` is typed `any` (from an untyped API client). Reports High — fix the client's return type; the cast is a symptom. `no-unnecessary-type-assertion` stays silent because the cast is load-bearing.

**Good annotation missing:**
> /review-typescript

A 40-line hand-written `const config = {...}` has no type, so a typo in a nested key only errors at a distant consumer. Reports Medium — add `satisfies AppConfig` for definition-site checking while keeping the narrow inferred shape.

## Troubleshooting

### Findings overlap with ESLint
**Solution:** They shouldn't. If a finding maps to a named typescript-eslint rule, drop it and (if the project doesn't run that rule) fold it into the one-time lint-baseline recommendation instead. This skill only reports what a type-aware linter can't judge.

### Can't tell if a boundary cast is safe
**Solution:** Trace where the value comes from. In-process, already-typed data → the cast may be fine (or redundant, i.e. lint's problem). External/parsed/DOM data → recommend a runtime guard; the type system can't vouch for data it never saw.

## Notes

- Model first, annotate second, cast last. Most cast findings dissolve once the underlying type is modeled correctly.
- Respect project conventions in CLAUDE.md (a codebase may deliberately allow `null`, prefer `interface`/`type`, etc.).
- Don't be dogmatic: brands, utility-type derivation, and satisfies all have ergonomic costs — recommend them where they prevent real bugs, not everywhere they're possible.
- Sources: *Effective TypeScript*, 2nd ed. (Vanderkam, 2024); Total TypeScript (Pocock); the TypeScript Handbook. typescript-eslint owns the mechanical rules referenced above.
