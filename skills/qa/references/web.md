# Web and Electron QA

Read `agent-browser skills get core --full` once per session. Commands below were
checked against 0.27.0; use installed help for additional flags. For Electron, also
read `agent-browser skills get electron` and connect to the documented app target.

## Drive and observe

Use a unique session name on **every** call, such as `qa-upload-1430`. Resolve the
actual dev URL from the project's startup output or port allocation, then:

```sh
agent-browser --session qa-upload-1430 open http://localhost:PORT
agent-browser --session qa-upload-1430 snapshot -i
agent-browser --session qa-upload-1430 fill @e3 "fixture input"
agent-browser --session qa-upload-1430 click @e5
agent-browser --session qa-upload-1430 snapshot
agent-browser --session qa-upload-1430 screenshot ./result.png
```

Substitute observed refs and the run's evidence path. Refresh refs after navigation
or re-render. Use the full snapshot for status text: interactive-only snapshots can
omit loading indicators and errors. Open screenshots to inspect layout; an
accessibility tree alone cannot establish visual correctness.

Wait for the expected state or URL with a bounded timeout. Capture pending states
**before** waiting for completion; `networkidle` is unsuitable as a universal wait,
especially with polling or streams. Inspect `console`, `errors`, and relevant
`network requests` after a failure; distinguish expected injected errors from
unexpected ones. Avoid raw authenticated request dumps in evidence.

## Exercise asynchronous states

Discover the actual request first. In the isolated local session, supported tools include:

```sh
agent-browser --session qa-upload-1430 network route "**/api/upload" --abort
agent-browser --session qa-upload-1430 network unroute "**/api/upload"
agent-browser --session qa-upload-1430 set offline on
agent-browser --session qa-upload-1430 set offline off
```

Run the failing action while the fault is active, then remove it and exercise retry.
`--abort` tests transport failure, not an HTTP 500. Use a project mock server or
verified interception facility to return an actual error status or hold a response
pending. Do not invent `--delay` or `--status` flags. For loading QA, delay the
specific response long enough to observe feedback and try a duplicate action,
cancel, or navigation away; then release it and verify the final state. Record
whether each request was real or stubbed. A mocked success cannot prove persistence.

Choose relevant viewports from the product's supported layouts. Check narrow
layout, overflow with long/empty content, keyboard traversal, focus after dialogs
and errors, accessible names, and reduced motion when the feature animates. Test
reload/deep links and back/forward where state or routing changed. Browser mobile
emulation establishes responsive behavior, not native-device compatibility.

If testing unsaved-change dialogs, inspect auto-dialog behavior first:
agent-browser can auto-accept `beforeunload`. Read help for
`AGENT_BROWSER_NO_AUTO_DIALOG` before launch so automation does not hide the case.

Restore routes and emulation settings, stop owned recordings, then close only this
session with `agent-browser --session qa-upload-1430 close`.
