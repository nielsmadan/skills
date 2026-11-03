# Judgment Checklist (full catalogue)

Load when reviewing files. Every item assumes the lint layer recorded in the baseline already
owns the rules it runs — a finding a running rule would raise is not yours to report.

## 1. State modeling & placement

- **Derived state stored as state.** A `useState` whose value is computable from props or other
  state during render (a filtered list, a full name, a count) can drift from its source and
  needs an effect or handler to keep it in sync. Compute it in render instead.
- **State copied from props.** `useState(props.value)` captures only the initial prop; later
  changes are ignored. Either make the component controlled, rename the prop to
  `initialValue`, or reset the subtree with a `key` when the identity changes.
- **Contradictory flags.** `isLoading` + `isError` + `data` as separate `useState`s permit
  impossible combinations. Recommend one state value modeled as a discriminated union, or a
  reducer when transitions carry rules.
- **State at the wrong height.** Too high: a keystroke in one field re-renders a whole screen.
  Too low: siblings keep copies and sync them through effects or callbacks. Lift to the
  closest common owner, no higher.
- **State in the wrong store.** Server data held in component state (stale, refetched per
  mount, no dedupe) when the project already has a query cache; shareable or
  navigation-relevant state (filters, tabs, selected id) that belongs in the URL or route
  params.
- **Reset via effect.** An effect that clears state when an id changes, where `key={id}` on
  the subtree resets it without a render of stale data.

## 2. Effects

The question for every effect: *what external system does this synchronize with?* No answer
means it probably should not be an effect.

- **Event logic in an effect.** Work caused by a specific user action (submit, purchase,
  analytics for a click) belongs in the handler. As an effect it re-fires on remount, under
  Strict Mode, and whenever a dependency happens to change.
- **Effect chains.** Effect A sets state that triggers effect B that sets state. Each hop is an
  extra render and an ordering hazard; compute in render or do it in the handler.
- **Notifying the parent from an effect.** `useEffect(() => onChange(value), [value])` renders
  twice and runs late; call `onChange` in the same handler that changed `value`, or lift the
  state.
- **Fetching without race handling.** An effect that fetches on an id with no abort or ignore
  flag can apply a slow earlier response over a newer one. Recommend cleanup that ignores
  stale results, or the project's query library.
- **Missing or wrong cleanup.** Subscriptions, timers, listeners and native event emitters
  without teardown; teardown that does not undo exactly what setup did.
- **Hand-rolled external store subscription.** `useEffect` + `useState` to mirror an external
  store (a module-level store, `matchMedia`, network state) instead of
  `useSyncExternalStore`, which avoids tearing and the extra render.
- **Dependency appeasement.** Dependencies removed, objects memoized, or refs introduced
  purely to stop an effect re-running. The usual fix is to move the logic out of the effect,
  or (React 19.2+) to read the latest value through `useEffectEvent`.

## 3. Component boundaries & identity

- **Unstable or index keys** on lists that reorder, insert or delete: state and DOM/native
  views attach to the wrong row. Also keys generated in render (`Math.random()`, `uuid()`),
  which remount every row on every render.
- **Context value churn.** A provider whose value is a fresh object each render re-renders
  every consumer; a single context carrying fast-changing and slow-changing data together.
  Split the context or stabilize the value (unless the compiler already does).
- **Prop drilling vs. context vs. composition.** Five layers threading a prop is a smell, but
  so is a context used by one child. Passing `children` or a render slot often removes both.
- **Controlled/uncontrolled mixing.** A component accepting `value` but also keeping its own
  copy, or switching between `value={undefined}` and a defined value.
- **God components.** A component mixing data loading, business rules and layout that cannot
  be tested or reused; split along those seams. Leave size alone if the pieces are cohesive.
- **Error and Suspense boundaries** placed so one failing widget blanks the whole screen, or
  so a loading fallback replaces content the user was already reading.

## 4. Rendering cost & memoization

Calibrate to the baseline first.

- **Compiler on:** hand-written `useMemo`/`useCallback`/`memo` in new code is noise unless it
  serves a reason the compiler cannot see (a value used as an effect dependency that must stay
  referentially stable across compiler bail-outs, an imperative library's identity
  requirements). Flag code that defeats the compiler: mutating props or state, reading refs in
  render, side effects in render — usually already reported by the compiler-backed lint rules
  when they run.
- **Compiler off:** flag only measurable costs — expensive computation in a hot render path,
  a fresh object/function passed to a `memo`'d child that therefore never skips, a large list
  rendered without virtualization. Do not ask for memoization everywhere.
- **Work in render that belongs elsewhere:** parsing, sorting large arrays or building lookup
  maps on every render when the input rarely changes.
- **Slow updates blocking input:** a keystroke that re-renders a heavy result list; recommend
  `useTransition`/`useDeferredValue` over debouncing in an effect.

## 5. Async UI

- **Optimistic and pending state** hand-rolled with several `useState`s where React 19's
  form actions, `useActionState` and `useOptimistic` would model it (check the React version
  first).
- **Unhandled pending/error states:** a mutation with no disabled state (double submit), an
  error swallowed into a `console.error`, a loading state with no way out on failure.
- **Stale closures** in timers, intervals or listeners registered once that read state captured
  at registration.

## 6. Platform-specific

Load only the section matching the baseline's renderer.

### react-dom (web)

- **Hydration mismatch sources** in server-rendered code: `Date.now()`, `Math.random()`,
  locale formatting, `window`/`localStorage` reads during render. Move them to an effect or
  make the server and client agree.
- **Server/Client Component boundaries** (Next.js App Router, other RSC setups): `'use client'`
  placed higher than needed, pulling a large subtree into the client bundle; non-serializable
  props crossing the boundary; server-only data or secrets passed into a client component.
- **Interactive elements built from `div`s** without role, keyboard handling and focus
  management, where a native `button`/`a`/`input` would have provided them. Static jsx-a11y
  rules catch some of this; judgment covers composite widgets (menus, dialogs, comboboxes).
- **Effects for layout measurement** using `useEffect` where `useLayoutEffect` is needed to
  avoid a visible flicker — and the reverse on the server, where `useLayoutEffect` warns.

### React Native

- **Lists:** `ScrollView` + `map` for long or unbounded data instead of `FlatList`/
  `FlashList`; `renderItem` or `keyExtractor` recreated each render on a non-compiled
  codebase; missing `getItemLayout` for fixed-height rows that need scroll-to-index.
- **JS-thread work during animation or gesture:** state updates per frame, heavy work in
  `onScroll`, animations driven from JS where Reanimated worklets or the native driver apply.
- **Platform branching** scattered through components instead of `Platform.select` or
  `.ios.tsx`/`.android.tsx` files when the divergence is large.
- **Native event subscriptions** (`AppState`, `Keyboard`, `Linking`, `Dimensions`,
  native-module emitters) without `remove()` in cleanup.
- **Navigation lifecycle:** work in `useEffect` that should run on screen focus
  (`useFocusEffect`), or screens assuming they unmount when navigated away from — stack
  screens stay mounted.

## Severity

- **Critical** — wrong data shown or persisted: stale response overwriting a newer one, state
  attached to the wrong list row, server secret reaching the client.
- **High** — will cause bugs as the code evolves: derived or duplicated state, event logic in
  effects, missing cleanup, contradictory state flags.
- **Medium** — structure and cost: state placement, context churn, measurable render cost,
  boundary placement.
- **Suggestion** — newer APIs or patterns that would simplify the code without fixing a bug.
