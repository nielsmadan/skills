# Backend and Worker QA

Use the project's local/test service stack, documented HTTP/RPC client, queue
producer, or existing integration harness. Verify the target environment and fixture
data before sending mutations. Unit tests help select cases; they do not establish
that the running service has correct wiring, configuration, or persistence.

Exercise the changed consumer contract with a small, meaningful sequence:

- Valid request: status, headers/content type, body, and persisted or emitted effect.
- Missing/malformed/boundary inputs and missing/expired/insufficient authorization,
  including another test user's resource when ownership matters.
- Create → read → update → read, or enqueue → pending → complete → fetch result.
- Slow/unavailable dependency, timeout, retry, duplicate request/delivery, and
  recovery after removing the fault where those are part of the feature.
- Pagination/cursors, concurrent conflicting writes, cancellation, or eventual
  consistency when affected. Use bounded polling against the documented contract.

Read responses and verify state through the service's public interface. A request
accepted with 202 does not establish job completion; a success body does not prove
the transaction committed. Use logs to explain failures, not as a replacement for
the consumer-visible result. Check a real client integration when the risk is in
cookies, CORS, redirects, or streaming; an HTTP CLI alone cannot prove browser policy.

For non-visual products, map “loading” to pending status, progress, streaming, or
timeout/cancel behavior. Do not demand a spinner from an API. A controlled dependency
failure should still exercise the real service's error handling and retry path.

Reuse existing contract/stateful tests when they exercise these boundaries; retain
their actual output and distinguish automated evidence from new exploratory runs.
For a pure internal refactor with adequate contract coverage, state that no extra
runtime exploration is justified. For missing infrastructure, record the blocked
scenario and prerequisite; do not substitute code inspection and call it a pass.
