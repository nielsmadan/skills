---
name: library-use
description: Official docs, changelogs, pinned versions, and the key correct-usage conventions for THIS repo's fast-moving / niche libraries — {LIB_LIST}. Consult before writing or changing code that uses any of them. Regenerate or refresh by running the global `library-docs` skill.
---

# Library Use — {REPO_NAME}

<!-- library-use-managed: v1
     GENERATED FILE. The `## <lib>` headers, version tags, and Docs/Changelog links
     are written by the global `library-docs` skill — do not hand-edit those; re-run
     `library-docs` to refresh. The "Conventions" bullets MAY be hand-tuned; the
     refresher preserves hand-added bullets and only rewrites lines it recognizes.
     Generated: {DATE} · deps from: {MANIFESTS} -->

Consult the entry for a library **before** writing or modifying code that uses it. Each
entry is pinned to the version this repo actually resolves — the conventions below are
correct for that version, not necessarily the latest.

## {LIBRARY} `{VERSION}`
- **Docs:** {DOCS_URL}
- **Changelog:** {CHANGELOG_URL}
- **Conventions:**
  - {One important correct-usage rule, API contract, or footgun for this version.}
  - {Another — prefer the things the model gets wrong from stale training data.}
  - {3–6 bullets max. Version-specific > generic. Cite the doc section if useful.}

<!-- Repeat one `## <library> <version>` block per documented library. -->
