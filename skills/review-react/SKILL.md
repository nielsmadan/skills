---
name: review-react
description: React-specific code review for both react-dom and React Native, focused on JUDGMENT-level component design a linter can't decide — state modeling and placement, effects that shouldn't be effects, component boundaries and identity, render cost calibrated to whether React Compiler is on, and platform pitfalls (hydration and Server Component boundaries on the web; lists, JS-thread work and native subscriptions on React Native). Deliberately does NOT duplicate eslint-plugin-react-hooks, and first checks which of its rules actually run — the compiler-backed rules from v6 on cover much of what reviewers used to flag by hand. Auto-invoked by `code-review` on React projects. Triggers "review react", "react review", "review components", "review hooks", "review effects", "react native review".
argument-hint: '[--staged | --unpushed | --changed | --all | --multi]'
effort: high
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Review React

React review that covers what the hooks linter and React Compiler **cannot decide for you** —
where state lives and what shape it has, whether an effect should exist at all, where component
and boundary lines fall, and which render costs are real. Mechanical hook rules are lint's job.

## Relationship to the lint layer (read first)

Establish the baseline before deciding anything is out of scope. Three facts change what this
review is responsible for:

| Fact | How to tell | What it changes |
|---|---|---|
| **Hooks lint rules that run** | `eslint-plugin-react-hooks` version and config in `eslint.config.*` / `.eslintrc*`; read the `lint` script too, since CLI flags can override the config | v6+ ships compiler-backed rules (`set-state-in-effect`, `set-state-in-render`, `refs`, `purity`, `immutability`, `static-components`, `preserve-manual-memoization`, `globals`, `use-memo`, …) alongside `rules-of-hooks` and `exhaustive-deps`. Count only the rules the config enables. Another linter (oxlint, Biome) needs its enabled React rules checked individually |
| **React Compiler on** | `babel-plugin-react-compiler` in `package.json`, and where the build enables it: `babel.config.js`, the Vite React plugin's `babel.plugins`, `reactCompiler` in `next.config.*`, `experiments.reactCompiler` in Expo's `app.json` / `app.config.*` | Decides whether manual memoization is noise or necessary (checklist §4) |
| **React version and renderer** | `react`, `react-dom` / `react-native`, and the framework (Next.js, Remix/React Router, Expo) in `package.json` | Which APIs are available to recommend (`useActionState`, `useOptimistic`, `useEffectEvent`), and which platform section of the checklist applies |

If a rule runs, its findings are out of scope. If it does not — an old plugin version, rules
cherry-picked, or no hooks linting at all — the same issue is a review finding, and the
configuration gap goes in §P rather than being reported per occurrence.

Run on `.jsx` / `.tsx` / `.js` / `.ts` files that render components or define hooks. Complements
`review-typescript` (type design) and `review-cleancode` (smells) — don't repeat them.

## Usage

```
review-react                  # Review context-related code
review-react --staged         # Review staged changes
review-react --unpushed       # Review files changed across all unpushed commits
review-react --changed        # Review unstaged changes
review-react --all            # Full codebase audit (parallel agents) + §P
review-react --multi          # Also get external advisor opinions
```

## Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Context-related code | Files from the current conversation context. If no context, ask the user to specify files or use `--staged`/`--changed`/`--all`. |
| `--staged` | Staged changes | `git diff --cached --name-only` |
| `--unpushed` | Files changed across unpushed commits | `git diff --name-only $(git rev-list HEAD --not --remotes \| tail -1)^..HEAD` |
| `--changed` | Unstaged changes | `git diff --name-only` |
| `--all` | Full codebase + **§P project-level checks** | Glob component and hook files, parallel agents |
| `--multi` | Add external opinions | Combines with any scope above; invokes `second-opinion --quick` |

If `--unpushed` cannot determine a range (nothing unpushed, no upstream, or the range walks back
to the root commit), stop and ask the user to pick another scope. Drop files that neither render
JSX nor call hooks.

## Instructions

1. **Determine scope** (see table) and filter to component and hook files.
2. **Read CLAUDE.md / AGENTS.md** in the repo root for project conventions (state library,
   data-fetching library, styling approach).
3. **Establish the baseline** (table above): enabled hooks rules, compiler on or off, React
   version, renderer and framework. Record it; it calibrates every later step.
4. **Review each file** against the judgment categories, looking at what the diff introduces.
   Load `references/checklist.md`, and from its §6 only the section for this renderer. Add
   **§P only at `--all`**.
5. **Parallelize** if scope has more than 5 files: one sub-agent per category, then merge and
   dedupe.
6. **External opinions** (if `--multi`): invoke `second-opinion --quick` with:

   ```
   Read-only React review. Assume eslint-plugin-react-hooks handles rules-of-hooks, exhaustive-deps and its compiler-backed rules — do NOT repeat lint-level findings. React Compiler is {on|off}; renderer is {react-dom|react-native}. Focus on JUDGMENT: is any state derivable or duplicated? Does each effect synchronize with an external system, or is it event logic / a state-to-state sync? Are fetches race-safe? Are list keys stable? Is state owned at the right height and in the right store? Are boundaries (error, Suspense, client/server) placed well? Which render costs are real rather than hypothetical? 300 words or less.
   ```

   Wait for all external results before proceeding.
7. **Classify severity** (definitions at the end of the checklist) and **report**.

## Judgment categories

`references/checklist.md` carries the full catalogue:

1. **State modeling & placement** — derived or prop-copied state, contradictory flags, state too
   high or too low, server data or URL state held in components, resets done with effects.
2. **Effects** — event logic in effects, effect chains, parent notification, race-prone
   fetches, missing cleanup, hand-rolled external store subscriptions, dependency appeasement.
3. **Component boundaries & identity** — unstable keys, context churn, drilling vs.
   composition, controlled/uncontrolled mixing, boundary placement.
4. **Rendering cost & memoization** — calibrated to the compiler: noise when it is on, only
   measurable costs when it is off.
5. **Async UI** — pending, optimistic and error states, stale closures.
6. **Platform** — react-dom (hydration, Server/Client Components, accessible composite widgets)
   or React Native (lists, JS-thread work, native subscriptions, navigation lifecycle).

State the reasoning for each finding. "This effect copies `user.name` into state, so editing
the profile elsewhere leaves the header stale" is a finding; "avoid useEffect" is not.

## P. Project-level checks — `--all` only

Configuration, not code; raising it on a diff review is noise.

- **Hooks linting**: is `eslint-plugin-react-hooks` on v6+ with its `recommended` preset (or the
  compiler-backed rules enabled individually)? If not, enabling it replaces a large share of
  manual review.
- **Compiler adoption**: on a React 19 project without React Compiler, note what adopting it
  would remove (most manual memoization) and what it needs (code free of the violations its
  lint rules report). A recommendation, not a mandate.
- **Strict Mode** enabled at the root, so double-invoked effects and renders surface impurity
  in development.

## Output Format

```markdown
## React Review: {scope}

### Baseline
{One line: hooks rules enabled, compiler on/off, React version, renderer/framework.
**At `--all` only:** the §P recommendations.}

### Critical (wrong data shown or persisted)
- {file}:{line} — {category}: {description}
  **Why it's not a lint finding:** {what judgment this needed}
  **Impact:** {what the user sees}
  **Fix:** {with code}

### High (will cause bugs as the code evolves)
- {file}:{line} — {category}: {description}
  **Fix:** {solution}

### Medium (structure & cost)
- {file}:{line} — {category}: {description} — {suggested change}

### Suggestions
- {opportunities}
```

If `--multi` was used, append one subsection per advisor that responded (titled with the
advisor's name as reported by `second-opinion`), then a **Cross-Model Agreement** subsection.

## Examples

**Race-prone fetch (web):**
> review-react --staged

A profile page fetches in `useEffect(() => { fetch(`/api/users/${id}`).then(setUser) }, [id])`.
Switching users quickly can show the previous user's profile. Reports Critical with an ignore
flag in cleanup, or the project's query hook if it has one. Not a lint finding:
`exhaustive-deps` is satisfied.

**Effect instead of a handler (React Native):**
> review-react --changed

A checkout screen sends a `purchase_completed` analytics event from an effect that watches
`order.status`. It re-fires when the screen remounts after navigating back. Reports High: move
it into the submit handler's success path.

**Memoization noise under the compiler:**
> review-react

Baseline shows React Compiler on. A new component wraps every handler in `useCallback` and
the component in `memo`. Reports Medium: remove them, since the compiler memoizes the same
values; keep only a `useCallback` whose identity an imperative library depends on.

## Troubleshooting

### Findings overlap with the linter
**Cause:** the baseline was skipped or assumed.
**Solution:** check whether the rule is enabled and runs (`lint` script flags included). If it
runs, drop the finding. If not, keep it and add the configuration gap to §P.

### Can't tell whether the compiler is on
**Cause:** it is enabled in build config the scan did not reach, or only for some directories
(`compilationMode: 'annotation'`, a `sources` filter, `'use no memo'` opt-outs).
**Solution:** read the compiler options where the plugin is configured. If still unclear, say
so in the baseline and skip compiler-dependent memoization findings rather than guessing.

### A pattern looks wrong but the project does it everywhere
**Cause:** a house convention (a global store for all state, a data layer that owns fetching).
**Solution:** follow CLAUDE.md / AGENTS.md. Report a convention only where it causes a concrete
bug in the scoped code, once, not per occurrence.

## Notes

- Model state first, then question effects, then worry about render cost. Most effect
  findings disappear once state is modeled correctly, and most render-cost findings disappear
  under the compiler.
- Don't recommend a library the project doesn't use (a query cache, a state manager) when the
  fix works with what is there; mention it as a suggestion at most.
- Sources: react.dev — "You Might Not Need an Effect", "Choosing the State Structure",
  "Preserving and Resetting State", the React Compiler docs, and the eslint-plugin-react-hooks
  README.
