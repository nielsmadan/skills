# Agent Prompt Templates

Full prompt templates for each research agent. Every agent is a general-purpose sub-agent, and must capture metadata for each source: URL, date, source type, author/publisher, and (where it applies) sample size / methodology / primary-vs-secondary status.

## Fetching web content

Prefer `mcp__jina__read_url` for JS-heavy pages (Reddit, modern news SPAs, paywalls that work via Jina). Use `WebFetch` for plain HTML, government PDFs, and `.gov`/`.int` sites.

Use `mcp__jina__parallel_read_url` when fetching several URLs at once.

## Encyclopedic Agent (Wikipedia)

**Spawn when:** Almost always — provides grounding even when other sources are richer

```
Look up the topic on Wikipedia for grounding and citation trails.

1. Use WebSearch: site:en.wikipedia.org {topic}
2. Use mcp__jina__read_url to read the top 1-2 most relevant articles
3. Note which key claims have inline citations and what the cited sources are (these are leads for the Academic / Primary / Historical agents to verify)
4. Flag any Wikipedia dispute markers ([citation needed], NPOV warnings, "this article has multiple issues")

Capture for each article:
- URL
- Last revision date (from the article footer or via the "View history" tab)
- Whether it has dispute markers
- Key cited sources for the main claims (URL + author/publisher)

Return:
- A neutral summary of what Wikipedia says about the topic
- The 3-5 most important cited sources for follow-up
- Any flags about contested or low-quality sections
```

## Academic Agent

**Spawn when:** Scientific, empirical, scholarly, social-science, economic, or evidence-based question

```
Find peer-reviewed and pre-print scholarly sources for: {topic_or_question}

For STEM / health / ML / formal-science topics:
- Use mcp__jina__parallel_search_arxiv with 2-3 query variants

For economics / finance / law / management / social-science topics:
- Use mcp__jina__parallel_search_ssrn with 2-3 query variants

For everything else (or if the above return weak results), fall back to:
- WebSearch: {topic} systematic review meta-analysis
- WebSearch: {topic} site:scholar.google.com
- WebSearch: {topic} site:ncbi.nlm.nih.gov  (for health / biomed)

Prioritize:
1. Systematic reviews and meta-analyses (highest weight on empirical questions)
2. Recent peer-reviewed primary studies
3. Pre-prints from named research groups
4. Avoid: predatory journals, single-author opinion pieces in obscure venues

For each source, capture:
- Title, URL, DOI if available
- Publication date and venue (journal / conference / preprint server)
- Authors (and affiliation if notable)
- Source type: meta-analysis / systematic review / RCT / observational / preprint / commentary
- Sample size and population (for empirical work)
- One-sentence finding

Return: a summary of what the evidence shows, weighted by study type and recency. Note where studies disagree or where the evidence base is thin.
```

## News Agent

**Spawn when:** Current events, recent developments, contemporaneous reporting on historical events

```
Find established-outlet news coverage of: {topic_or_question}

Use WebSearch with date hints if relevant:
- {topic} {date_scope}
- {topic} site:reuters.com OR site:apnews.com OR site:bbc.com OR site:nytimes.com OR site:theguardian.com OR site:economist.com OR site:ft.com OR site:wsj.com

Then use mcp__jina__read_url on the top 2-3 most authoritative pieces.

Prioritize:
1. Wire services (Reuters, AP) for breaking facts
2. Established outlets with reporting standards (NYT, BBC, Guardian, Economist, FT, WSJ)
3. Specialist outlets if topic is niche (e.g., STAT for biomed, Bloomberg for markets)
4. De-prioritize: aggregators, opinion sections (unless flagged as such), partisan outlets

For each source, capture:
- Headline, URL, outlet
- Publication date (and last update if relevant for fast-moving stories)
- Author (and beat / expertise if notable)
- Source type: news article / opinion / explainer / investigation
- Whether the piece relies on primary sources or other reporting

Return: a summary of what mainstream reporting says, with dates. Distinguish between *what is reported as fact* and *what sources are quoted as claiming*.
```

## Primary Source Agent

**Spawn when:** Statistics, official positions, regulatory questions, government action, organizational reports

```
Find primary sources — government data, official organization reports, regulator filings — for: {topic_or_question}

Use WebSearch:
- {topic} site:.gov  (or country-specific: site:.gov.uk, site:europa.eu, etc.)
- {topic} site:.int  (UN, WHO, IMF, World Bank)
- {topic} {organization_name} report
- {topic} statistics official

For relevant agencies, search their site directly:
- Health: WHO, CDC, NIH, NHS
- Economics: BLS, Eurostat, OECD, IMF, World Bank, central banks
- Climate / energy: IPCC, IEA, EPA
- Population / development: UN DESA, Census Bureau
- Industry-specific regulators: SEC, FDA, FAA, EMA, etc.

Fetch primary documents with WebFetch (most .gov pages and PDFs are plain HTML / PDF). Use Jina if a portal is JS-heavy.

For each source, capture:
- Title, URL, issuing body
- Publication / data-as-of date
- Source type: official statistics / regulatory filing / official report / position statement
- Methodology notes if relevant (how the data was collected, sample, definitions)

Return: a summary of what official sources say, with dates and methodology notes. Flag any methodological caveats (e.g., "self-reported", "preliminary", "model-based estimate").
```

## General Agent

**Spawn when:** Always

```
Broad web search for explainers, longreads, and expert blog posts on: {topic_or_question}

Use WebSearch: {topic}

Look for:
- In-depth explainers from publications like The Atlantic, Scientific American, Quanta, Aeon, Asterisk
- Expert blogs by named, verifiable authors
- Longread investigative pieces
- Survey articles that summarize a field

For each source, capture:
- Title, URL, outlet / author
- Publication date
- Source type: explainer / longread / expert blog / survey
- Author's expertise (if verifiable)

Return: a summary of how the topic is explained and any prevailing narratives, with source metadata.
```

## Forum Agent (Reddit and similar)

**Spawn when:** Opinion-heavy questions, lived experience, unsettled topics where personal accounts add value

```
Find candid opinions and lived experience on: {topic_or_question}

Use WebSearch: site:reddit.com {topic}

For top 2-3 relevant threads:
1. Use mcp__jina__read_url to read the thread (Reddit is JS-heavy; plain WebFetch returns an empty shell)
2. Focus on highly-upvoted comments with substantive content, not just the original post
3. Note the subreddit (r/AskHistorians and r/AskScience have moderation standards; r/news does not)

For each source, capture:
- Thread URL, subreddit
- Post date
- Upvote and comment count (>100 upvotes or >50 comments = high engagement)
- Whether top comments cite sources
- Source type: Reddit thread (moderated / unmoderated)

Return: a summary of opinions and experiential reports with engagement metadata. **Treat as evidence of opinion distribution, not as evidence of fact.** Note when comments cite primary sources worth following up.
```

## Comparison Agent

**Spawn when:** Query contains "vs", "or", "compare", "which is better", "differences between"

```
Find direct comparisons between: {option_A} and {option_B} (in context: {context})

Use WebSearch:
- {option_A} vs {option_B} {context}
- {option_A} or {option_B} which is better
- differences between {option_A} and {option_B}

Look for:
- Side-by-side comparison articles
- Analysis pieces that weigh trade-offs
- Per-axis breakdowns (cost, performance, risk, sustainability, etc.)
- Use-case recommendations (when to choose which)

For each source, capture:
- Title, URL, outlet / author
- Publication date
- Source type: comparison article / analysis / op-ed
- Apparent stance / sponsorship (advocacy organizations have a side)

Return: a balanced summary of each option's strengths, weaknesses, and best-fit use cases. Flag sources with apparent ideological or commercial bias. Note where the comparison genuinely depends on values vs. where there's an empirical answer.
```

## Specific Claim Agent

**Spawn when:** Exact claim or quote to verify (typically in quotes)

```
Verify or refute the specific claim: "{exact_claim}"

Use WebSearch:
- "{exact_claim}"
- "{exact_claim}" fact check
- "{exact_claim}" debunked
- "{exact_claim}" origin

Find:
- The original source of the claim (if any)
- Fact-checks by Snopes, Reuters Fact Check, AP Fact Check, FactCheck.org, PolitiFact
- Academic papers that address the claim
- The strongest evidence for AND against the claim

For each source, capture:
- URL, outlet / author
- Publication date
- Source type: fact-check / academic / news / blog
- Verdict (if a fact-check): true / mostly true / mixed / mostly false / false / unproven

Return:
- The claim's verdict, weighted by source authority
- The strongest evidence each way
- The original source of the claim, if findable
- Whether the claim is a misquote, oversimplification, or out-of-context
```

## Regional Agent

**Spawn when:** Query mentions a country, city, region, or locale-specific topic (regulations, prices, services, regulators, health systems, taxation, real estate)

```
Find region-specific sources and authorities for: {topic} in {region}

Use WebSearch:
- {topic} {country/region}
- {topic} site:{country_TLD}  (e.g., site:.de, site:.fr, site:.uk, site:.gov.au)

For non-English locales, ALWAYS also search in the local language — results are significantly better and pick up authoritative local sources that English searches miss.

Locale playbook (extend as needed):

**Germany (DE)**
- Search terms in German: e.g., "Tagesgeld Vergleich 2026", "Matratze Test", "Mietpreisspiegel Berlin", "Freiberufler Steuern"
- Key authoritative sites: finanztip.de, verbraucherzentrale.de, test.de (Stiftung Warentest), check24.de, ihk.de, bafin.de, bundesbank.de

**France (FR)**
- Search in French: e.g., "comparatif {topic}", "{topic} avis"
- Key sites: service-public.fr, ufc-quechoisir.org, 60millions-mag.com, ameli.fr (health)

**UK (GB)**
- Key sites: gov.uk, which.co.uk, moneysavingexpert.com, nhs.uk, citizensadvice.org.uk

**United States (US)**
- Key sites: .gov sites for the relevant agency, consumerreports.org, nerdwallet.com, kff.org (health policy)

**Australia (AU)**
- Key sites: gov.au, choice.com.au, moneysmart.gov.au

For other regions, look for: the national consumer-protection body, the relevant regulator (financial / health / industry), an established independent test or comparison institution.

For each source, capture:
- Title, URL, language
- Publication date
- Source type: government / regulator / consumer-protection body / independent test institution / commercial comparison site / local news
- **Affiliate or sponsorship disclosure** (especially relevant for commercial comparison sites)
- Region/scope it covers (and flag if it covers a different region than requested)

Return: a summary of region-specific findings, weighting government and independent-test institutions above commercial comparison sites. Translate key terms back to English in the summary so the synthesis can use them.
```

## Historical Agent

**Spawn when:** Topic is historical, OR a historical angle is needed for context

```
Find primary documents, archived reporting, and established historical scholarship on: {topic_or_question}

Use WebSearch:
- {topic} primary sources
- {topic} archive
- {topic} declassified  (for 20th century events involving governments)
- {topic} site:archives.gov  /  {country} national archive
- {topic} site:nytimes.com/{year}/  (and similar archived news)
- {topic} historiography  (to surface scholarly debate)

Prioritize:
1. Primary documents (declassified records, contemporaneous letters, official documents)
2. Contemporaneous news reporting from the period
3. Established historians and academic histories
4. De-prioritize: pop history with weak citations, ideologically-driven retellings

For each source, capture:
- Title, URL, type (primary document / contemporaneous reporting / scholarly history / pop history)
- Date of source AND date of event covered
- Author / issuing body
- Whether scholarship is contested (note historiographical debates)

Return: a summary of what primary sources and established scholarship show. **Prefer primary sources over recent commentary.** Note where historians disagree and on what basis.
```
