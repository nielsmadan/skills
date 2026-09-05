# Native App QA

Start with `agent-device --version`, `agent-device help manual-qa`, and the relevant
command's `--help`. Read `agent-device help macos` or `help physical-device` for
those targets. These examples were checked against 0.19.3; installed help governs
flags and platform support.

## Select the right build and device

Use the project's launch procedure and its assigned simulator/emulator or claimed
physical device. If it uses Splashdown, follow its documented target and port
selection. Do not pick the first booted simulator or a sibling checkout's server.
Confirm the bundle/package identifier and build correspond to the scoped code.
For a UI library, run its existing example/consumer app.

Choose a unique session and an explicit device selector from help when needed:

```sh
agent-device open com.example.app --platform ios --session qa-profile-1430
agent-device snapshot -i --session qa-profile-1430
agent-device fill @e13 "fixture input" --settle --session qa-profile-1430
agent-device press @e12 --settle --session qa-profile-1430
agent-device wait text "Saved" 3000 --session qa-profile-1430
agent-device screenshot ./result.png --session qa-profile-1430
```

Replace the identifier, refs, expected text, timeout, and artifact path. Use
`--platform android` for Android. Keep device mutations serial. Settled output can
serve as the next observation, but settling is UI quietness, not proof that async
work completed. Observe actual outcomes and open screenshots for visual checks.

## States and lifecycle

Use documented app fixtures/debug controls or a local test server to delay or fail
requests. `trigger-app-event` only works when the app implements and configures
that event; it is not an arbitrary state setter. Record before the action when a
transition is brief: `agent-device record start ./loading.mp4 --session NAME`, then
`record stop --session NAME`. Do not let `--settle` skip the pending state under test.

**On iOS simulators, Wi-Fi/airplane settings change status-bar presentation, not
connectivity.** Establish offline behavior through an actual failed request or a
controlled app/server fault. `network dump` depends on app logging and is not a
general network interceptor. On Android, verify the actual network effect of a
connectivity change and restore the prior setting.

Add relevant keyboard occlusion, back gestures, background/foreground, interrupted
work, relaunch/persistence, deep links, orientation, text scaling, and permission
deny/retry cases. Check platform support with `settings --help`; iOS permission and
biometric helpers are simulator-specific, and Android permission revocation can
terminate the app. Relaunch before assessing recovery. Keep animations enabled
when judging transitions. Clear app data only in a disposable QA instance whose
reset is within scope.

## macOS

Use `agent-device open APP --platform macos --session NAME`. For a menu-bar app,
select `--surface menubar`; an empty normal app tree may mean the wrong surface.
Test menu items, shortcuts, focus, window reopen, and relevant permission recovery.
Prefer observed refs over coordinates; re-snapshot after opening a context menu.

macOS has no mobile boot/rotation/push helpers. Accessibility and screen-recording
access may require the user's TCC approval; a permission helper cannot silently
grant it. Report that exact blocker and continue independent cases.

Restore changed permissions/settings and test fixtures; stop recordings and close
only the owned session using `agent-device close --session NAME`. Preserve a
simulator or app session that was already in use before QA.
