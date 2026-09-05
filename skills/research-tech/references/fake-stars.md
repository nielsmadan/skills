# Vetting GitHub Star Counts

A GitHub star count is a **vanity metric that is trivially inflated** — do not treat it as evidence
of quality, adoption, or credibility on its own. A CMU/NCSU/Socket study (He et al., *Six Million
(Suspected) Fake Stars on GitHub*, ICSE 2026, [arXiv 2412.13459](https://arxiv.org/abs/2412.13459))
found ~6M suspected fake stars across 18,617 repos, near-zero before 2022 and surging through 2024 —
at the July 2024 peak, **16.7% of repos with ≥50 stars that month were running fake-star campaigns**.
Stars cost $0.03–$0.85 each; a VC-seed-median ~2,850 stars costs $85–$285, so the incentive is huge.
AI/LLM repos are the largest non-malicious target; most fake-star repos are outright spam/malware.

**When this matters for research:** any time star count would influence a recommendation — "X is more
popular / more trusted / the standard choice", library comparisons, or "is this repo safe to adopt".
Substitute or cross-check with the signals below. When in doubt, prefer harder-to-fake signals
(external contributors, production dependents) over stars.

## The 30-second checks (do these before citing a star count)

1. **Fork-to-star ratio** — the strongest simple heuristic. A fork means someone copied the code; a
   star is free. Healthy actively-used projects sit around **10–25%** (Flask 23.5%, LangChain 15.5%).
   **>10k stars with a fork ratio <5% → investigate.** Worst documented case: 157k stars, ~2,700
   forks = 1.7%.
2. **Watcher-to-star ratio** — even stronger (watching is higher-commitment). Organic projects run
   **0.5–3%**; the 157k-star repo above had 0.1% (~26x lower than Flask).
3. **Eyeball the stargazers** — open the stargazer list and check ~10 profiles. On manipulated repos,
   **50–80% have zero followers and no public repos** ("ghost" accounts), vs ~6–12% zero-follower and
   ~1–2% ghost on organic repos. This catches campaigns that fake a healthy fork ratio.

No single number catches everything — run the ratio checks **and** the profile check together.

## Deeper tells

**Fake stargazer accounts:**
- Empty "ghost" profile — no repos, no followers, no bio.
- Trivial activity: the account's entire history is one star (WatchEvent), sometimes plus one fork of
  the same repo the same day, then goes stale. Never files issues, comments, or opens PRs.
- **Account age is NOT a reliable filter** — premium farmed accounts are years old (1,000+ days) with
  fake multi-year contribution graphs, built specifically to defeat "young account" checks.
- Many get deleted: ~57% of flagged accounts and ~90% of flagged repos were removed by GitHub within
  months (vs ~3–5% baseline). A repo that has since vanished is a strong retroactive signal.

**Temporal / star-history shape** (plot it at [star-history.com](https://star-history.com)):
- Sudden spike with no cause — no release, no HN/conference mention, flat commit log. ~2,000 stars in
  a week with nothing shipped is suspicious.
- Star velocity decoupled from commit velocity.
- "Lockstep" bursts — many accounts star the same repos inside a tight window (the study's core
  detection signal; 4.9M of the 6M fake stars). Hard to see by hand but shows up as unnatural steps.

**Repo-level:**
- Package **downloads without dependents** — the registry equivalent of stars without forks. 70% of
  fake-campaign packages had zero dependents. Downloads are also fakeable; count *production
  dependents* (via [ecosyste.ms](https://ecosyste.ms)), not raw downloads.
- Thin community: empty/maintainer-only issues on a high-star repo, single contributor, unreviewed PRs.
- Short-lived: 84% of campaign repos had <10 days of total activity.
- Suspicious names/categories: pirated software, crypto bots/wallet-stealers, game cheats (most fake
  repos are malware); AI/LLM projects are the top *non-malicious* recipient.

## Vanity → substance substitutions

When a source leans on a soft signal, look for the harder one instead:

| Vanity signal | Check instead |
|---|---|
| Star count | Fork-to-star ratio + external contributor count |
| "Trending" / viral | 12+ months of consistent commit cadence |
| Package downloads | Number of production dependents |
| Discord/community size | Issue response time (<48h?), reviewed PRs |
| Star growth spike | A matching release, commit burst, or press mention |

**Unique monthly contributors** (anyone who filed an issue, comment, PR, or commit) is the single
hardest signal to fake — Bessemer found <5% of the top-10k projects ever exceeded 250/month.

## Tools

- **[star-history.com](https://star-history.com)** — plots a repo's star-growth curve to eyeball spikes.
- **GitHub REST API stargazers with timestamps** — request with `Accept: application/vnd.github.star+json`
  to get `starred_at` per user; lets you build the star-time curve and check profiles programmatically.
- **[ecosyste.ms](https://ecosyste.ms)** — maps a repo to package registries and returns dependent
  counts (to prove "downloads without dependents").
- **GitHub Pulse / Contributors / Insights tabs** — maintenance cadence, bus factor, PR response times.
- **StarScout** (the study's tool) — runs CopyCatch + low-activity queries over GHArchive/BigQuery; not
  a hosted service, but the code + dataset are public ([Zenodo](https://doi.org/10.5281/zenodo.17009693)).
- **Socket (socket.dev)** — SCA vendor that integrated StarScout to flag dependencies with fake-star history.
