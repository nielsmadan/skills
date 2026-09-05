# Agent Prompt Templates

Full prompt templates for each research agent. Every agent is a general-purpose sub-agent, and must capture metadata for each source: URL, date, and source type.

## Fetching web content

When an agent needs to read a URL, prefer `mcp__jina__read_url` over `WebFetch` — Jina renders JS server-side and returns clean markdown, avoiding the empty-shell problem `WebFetch` has on SPAs (Reddit, Stack Overflow, many modern docs sites).

Exceptions where plain `WebFetch` is fine or better:
- `github.com` URLs (issues, PRs, repo files) — no JS hydration needed
- Plain HTML blogs, RSS feeds, PDFs
- When Jina is unavailable or returns thin content — fall back to `WebFetch`

Use `mcp__jina__parallel_read_url` when fetching several URLs at once.

## Docs Agent (Context7)

**Spawn when:** Library/framework is identified

```
Use Context7 to look up documentation for {library_name}.

1. First call resolve-library-id with libraryName="{library_name}" and query="{goal_or_problem}"
2. If resolve-library-id returns no match, fall back to WebSearch: "{library_name} official documentation {goal_or_problem}"
3. If a match is found, call query-docs with the resolved library ID and query="{goal_or_problem}"

Focus on finding:
- API usage relevant to: {goal_or_problem}
- Configuration options
- Common patterns and examples

For each finding, note:
- Source URL
- Date (if available, or note "official docs - current")
- Source type: official docs

Return a concise summary of relevant documentation findings with source metadata.
```

## GitHub Agent

**Spawn when:** Library with known GitHub repo

```
Search GitHub for issues AND discussions related to this topic.

Use WebSearch to search: site:github.com {library_name} "{key_terms}"

Look for:
- Issues (bugs, feature requests)
- Discussions (implementation questions, best practices)
- Pull requests with relevant changes

If you find relevant results:
1. Use WebFetch to read the top 2-3 most relevant
2. Extract: problem/question, any solutions posted, recommended approaches

For each result, note:
- URL
- Date opened/last updated
- Type (issue/discussion/PR)
- Status (open/closed/merged)
- Whether maintainer responded
- Source type: GitHub issue (maintainer) / GitHub issue (community) / GitHub discussion

If the repo's star count comes up as a credibility/popularity signal, do NOT take it at face value —
star counts are trivially inflated. Sanity-check it: fork-to-star ratio (healthy ~10-25%; <5% on a
>10k-star repo is suspicious) and whether stars track real activity (commits, contributors,
dependents). See `references/fake-stars.md` for the full checklist. Report the ratio, not just the raw count.

Return a summary of relevant findings with metadata.
```

## General Solutions Agent

**Spawn when:** Always

```
Search for general solutions and guides for this topic.

Use WebSearch to search: how to {goal_or_problem} {library_name}

Focus on:
- Tutorial articles
- Implementation guides
- Blog posts with solutions
- Official guides

For each source, note:
- Source URL
- Publication date (look for date in article or URL)
- Source type: blog / tutorial / official guide
- Author credibility if apparent (known developer, company blog, random post)

Return a summary of approaches found with source metadata.
```

## Specific Error Agent

**Spawn when:** Error message is provided

```
Search for this specific error message.

Use WebSearch to search: "{exact_error_message}" {library_name}

Find:
- What causes this error
- How others have fixed it
- Any library-specific solutions

For each source, note:
- Source URL
- Date
- Source type
- Whether it's an exact match for the error or similar

Return findings with the most common causes and fixes, including source metadata.
```

## Stack Overflow Agent

**Spawn when:** Common programming problem or implementation pattern

```
Search Stack Overflow for solutions and implementations.

Use WebSearch to search: site:stackoverflow.com {library_name} {keywords}

For the top 2-3 relevant questions:
1. Use `mcp__jina__read_url` to read the accepted/top answers (Stack Overflow is JS-heavy; plain WebFetch often returns an empty shell)
2. Extract the solution approach

For each answer, note:
- Question URL
- Answer date
- Vote count (>10 votes = higher credibility signal)
- Whether it's the accepted answer
- Source type: SO answer (accepted + >10 votes) = Medium authority, SO answer (not accepted, <10 votes) = Low authority

Return a summary of community solutions with metadata.
```

## Changelog Agent

**Spawn when:** Version mentioned OR upgrade-related problem ("stopped working", "after upgrade")

```
Search for changelog and breaking changes.

Use WebSearch to search: {library_name} {version} changelog breaking changes migration

Find:
- What changed in this version
- Known breaking changes
- Migration guides

For each source, note:
- Source URL
- Date/version it covers
- Source type: official changelog / migration guide / release notes

Return relevant version changes that might affect: {goal_or_problem}
```

## Best Practices Agent

**Spawn when:** Feature implementation query (no error message present)

```
Search for best practices and recommended patterns.

Use WebSearch to search: {library_name} best practices {goal_description}
Also search: {library_name} recommended architecture {goal_description}

Focus on:
- Official style guides and recommendations
- Architecture patterns from experienced developers
- Common pitfalls to avoid
- Production-ready patterns

For each source, note:
- Source URL
- Publication date
- Source type: official guide / architecture blog / tutorial
- Author credibility (core team, recognized expert, unknown)

Return a summary of recommended approaches with source metadata.
```

## Reddit Agent

**Spawn when:** Comparison, best practices, or "real world experience" queries

```
Search Reddit for real-world developer opinions and experiences.

Use WebSearch to search: site:reddit.com {library_name} {keywords}

Focus on:
- Real-world experience reports ("we used X in production and...")
- Warnings and gotchas that don't appear in docs
- Candid opinions on trade-offs
- "Don't do this" advice from experience

For the top 2-3 relevant threads:
1. Use `mcp__jina__read_url` to read the thread (Reddit is JS-heavy; plain WebFetch often returns an empty shell)
2. Focus on highly-upvoted comments, not just the original post

For each source, note:
- Thread URL
- Date
- Upvote count and comment count (>50 upvotes or >20 comments = high engagement signal)
- Source type: Reddit thread (>50 upvotes) = Medium authority, Reddit thread (<10 upvotes) = Very Low authority

Return a summary of real-world opinions and warnings with metadata.
```

## Comparison Agent

**Spawn when:** Query contains "vs", "or", "compare", "which", "best library/package"

```
Search for comparisons between the options mentioned.

Use WebSearch to search: {option_A} vs {option_B} {context}
Also search: {option_A} or {option_B} which is better {context}

Find:
- Direct comparison articles
- Pros and cons of each option
- Performance benchmarks if relevant
- Use case recommendations (when to use which)

For each source, note:
- Source URL
- Publication date (crucial for comparisons - libraries change fast)
- Source type: comparison article / benchmark / discussion
- Whether it covers recent versions

If a comparison ranks options by GitHub stars / "popularity", treat that as weak evidence — star
counts are trivially bought and often decoupled from real adoption. Prefer harder-to-fake signals
(fork-to-star ratio, external contributor count, production dependents). Flag any "X has more stars
so it's better" claim; see `references/fake-stars.md`.

Return a balanced summary of each option's strengths and weaknesses with source metadata.
```
