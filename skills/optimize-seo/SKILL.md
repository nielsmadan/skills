---
name: optimize-seo
description: Audit and optimize web pages for SEO — meta tags, Open Graph, JSON-LD, structured data. Triggers "optimize SEO", "check SEO", "add meta tags", "SEO audit".
---

<!-- Generated from https://github.com/nielsmadan/agentic-coding — edits here are overwritten. -->

# Optimize SEO

Audit a web page against current SEO best practices (2025-2026) and generate missing or improved elements.

## Gotchas
- On SPAs, SSG sites (Next.js, Gatsby), or template-driven systems, the HTML file may be a build artifact. Fixes applied to generated output are lost on the next build — find the source template instead.
- Adding meta tags without checking for existing ones creates duplicates. Most parsers use the first match, so the old (wrong) tag wins. Check for existing tags before adding new ones.

## Instructions

### Step 1: Identify the Target

Determine what to audit:
- **HTML file(s):** Read the file(s) directly
- **URL:** Use WebFetch to retrieve the page
- **Component/template:** Read the source files that produce the page

If the user provides a URL or file, read it. If unclear, ask what page to optimize.

### Step 2: Audit

Consult `references/seo-checklist.md` for the full checklist and reference material.

Run through each category and report issues:

**Title & Meta** — Check title tag (50-60 chars, keyword near start, unique), meta description (150-160 chars, keyword + CTA), canonical tag, Open Graph tags, Twitter Card tags.

**Headings** — Single H1 with primary keyword, logical H2/H3 hierarchy, no skipped levels, no heading tags used for styling.

**Images** — Alt text on all images, explicit width/height, descriptive filenames, WebP format, lazy loading on below-fold images.

**Structured Data** — Check for existing JSON-LD. Determine appropriate schema type(s) for the page content (Article, FAQ, Product, LocalBusiness, BreadcrumbList, Organization, etc.).

**Internal Linking** — Descriptive anchor text, no orphan pages, links to related content.

**Content** — Primary keyword in first 100 words, comprehensive coverage, author attribution, publication/update dates, external authority links.

**Technical** — HTTPS, canonical URL, no accidental noindex, mobile-friendly markup, no render-blocking resources.

### Step 3: Report Issues

Present findings grouped by severity:

1. **Critical** — Missing title tag, no H1, accidental noindex, missing canonical, broken structured data
2. **Important** — Missing meta description, missing Open Graph, no structured data, missing alt text, no internal links
3. **Improvements** — Title too long/short, meta description could be stronger, missing Twitter Card, image optimization opportunities

For each issue: state what's wrong, why it matters, and the fix.

### Step 4: Generate Fixes

Generate the actual markup for all issues found:

- **Meta tags** — Title, description, canonical, robots
- **Open Graph + Twitter Card** — Full tag set
- **Structured data** — Complete JSON-LD block(s) using templates from `references/seo-checklist.md`
- **Image attributes** — Alt text, width/height, loading="lazy"
- **Heading restructure** — If hierarchy is broken, suggest corrected structure

Apply fixes directly to the file(s) when the user has given edit access. Otherwise, present the generated markup for the user to apply.

### Step 5: Validate

After applying fixes:
- Confirm structured data is valid JSON (parse it)
- Verify title length is 50-60 characters
- Verify meta description is 150-160 characters
- Check that canonical URL is absolute and correct
- Ensure no duplicate tags were introduced

## Examples

### Example 1: Audit an HTML file
User says: "optimize SEO on src/pages/about.html"

1. Read the file
2. Audit against checklist — find: title too long (72 chars), no meta description, no Open Graph tags, images missing alt text, no structured data
3. Report issues by severity
4. Generate and apply: shortened title, meta description, full OG + Twitter tags, Organization JSON-LD, alt text for images

### Example 2: Generate structured data
User says: "add schema markup to our product page"

1. Read the product page
2. Identify it needs Product + BreadcrumbList schemas
3. Generate JSON-LD from product details on the page (name, price, image, description, availability)
4. Add the `<script type="application/ld+json">` block to `<head>`

### Example 3: Audit a URL
User says: "check SEO on https://example.com/blog/post"

1. WebFetch the URL
2. Full audit against checklist
3. Report all issues with severity
4. Provide copy-paste markup fixes

## Troubleshooting

### Page has no `<head>` section
**Cause:** Single-page app or component that doesn't control the HTML document.
**Solution:** Identify where the `<head>` is managed (layout file, _app.tsx, index.html) and apply meta tags there. For structured data, JSON-LD can go anywhere in `<body>`.

### Structured data conflicts with existing markup
**Cause:** Page already has partial or outdated schema.
**Solution:** Merge with existing schema rather than duplicating. Remove deprecated schema types. Validate the combined result.

### Dynamic content (SPA/React/Next.js)
**Cause:** Meta tags need to be set per-route, not just in a static HTML file.
**Solution:** Use the framework's head management (Next.js `<Head>`, React Helmet, Vue Meta) to set tags per page. Ensure SSR/SSG renders meta tags in the initial HTML response.
