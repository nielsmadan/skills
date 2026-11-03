# SEO Reference (2025-2026)

## Ranking Factor Weights (First Page Sage, Q1 2025)

| Factor | Weight |
|--------|--------|
| Consistent publication of satisfying content | 23% |
| Keyword in meta title tag | 14% |
| Backlinks from authoritative domains | 13% |
| Niche expertise (topic authority) | 13% |
| Searcher engagement (dwell time, bounce) | 12% |
| Content freshness/recency | 6% |
| Mobile-friendly / mobile-first | 5% |
| Trustworthiness (E-E-A-T) | 4% |
| Link distribution diversity | 3% |
| Page speed | 3% |
| HTTPS | 2% |
| Internal links | 1% |

*Note: These are directional estimates, not published by Google.*

---

## On-Page SEO Checklist

### Title and Meta
- [ ] Unique title tag, 50-60 characters, primary keyword near start
- [ ] Unique meta description, 150-160 chars, includes keyword and CTA
- [ ] Open Graph tags (og:title, og:description, og:image, og:url, og:type)
- [ ] Twitter Card tags (twitter:card, twitter:title, twitter:description, twitter:image)

### Headings
- [ ] Single H1 containing primary keyword
- [ ] Logical H2/H3 hierarchy (no skipped levels)
- [ ] At least one H2 with keyword variation or related question
- [ ] No heading tags used purely for styling

### URL
- [ ] Short, descriptive, hyphenated, lowercase
- [ ] Primary keyword in URL
- [ ] HTTPS
- [ ] Consistent trailing slash with canonical tag

### Content
- [ ] Primary keyword in first 100 words
- [ ] Comprehensive topic coverage
- [ ] Original data, examples, or insights
- [ ] Author attribution with bio link
- [ ] Publication date and "last updated" date visible
- [ ] External links to authoritative sources
- [ ] Answers likely user questions (AI Overview eligibility)

### Images
- [ ] Descriptive file names (not image001.jpg)
- [ ] Alt text on all images (descriptive, keyword where natural)
- [ ] Explicit width and height attributes
- [ ] WebP format, compressed
- [ ] `loading="lazy"` on below-fold images

### Internal Linking
- [ ] Links to relevant internal pages with descriptive anchor text
- [ ] No orphan pages
- [ ] Pillar page linked to cluster content

### Structured Data
- [ ] Appropriate schema type (Article, FAQ, Product, LocalBusiness, etc.)
- [ ] JSON-LD format
- [ ] Validated with Google Rich Results Test

### Technical
- [ ] Page indexed (check via `site:domain.com/page/`)
- [ ] Canonical tag set correctly
- [ ] No accidental noindex tag
- [ ] Core Web Vitals passing (LCP <2.5s, INP <200ms, CLS <0.1)
- [ ] Mobile-friendly
- [ ] Page loads under 2.5s on mobile

---

## Meta Tag Specifications

**Title tag:** 50-60 characters. Primary keyword near start. Brand at end.
```html
<title>Primary Keyword - Secondary Context | Brand</title>
```

**Meta description:** 150-160 characters. Keyword + CTA.
```html
<meta name="description" content="Compelling description with keyword. Actionable CTA." />
```

**Canonical:**
```html
<link rel="canonical" href="https://example.com/preferred-url/" />
```

**Open Graph:**
```html
<meta property="og:title" content="Page Title" />
<meta property="og:description" content="Description for social shares" />
<meta property="og:image" content="https://example.com/image.jpg" />
<meta property="og:url" content="https://example.com/page/" />
<meta property="og:type" content="article" />
```

**Twitter Card:**
```html
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="Page Title" />
<meta name="twitter:description" content="Description" />
<meta name="twitter:image" content="https://example.com/image.jpg" />
```

---

## Structured Data Templates (JSON-LD)

### Article
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Article Title",
  "image": "https://example.com/image.jpg",
  "author": { "@type": "Person", "name": "Author Name", "url": "https://example.com/author/" },
  "publisher": {
    "@type": "Organization",
    "name": "Publisher Name",
    "logo": { "@type": "ImageObject", "url": "https://example.com/logo.png" }
  },
  "datePublished": "2025-01-15",
  "dateModified": "2025-12-01",
  "description": "Brief summary."
}
```

### FAQPage
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [{
    "@type": "Question",
    "name": "Question text?",
    "acceptedAnswer": { "@type": "Answer", "text": "Answer text." }
  }]
}
```

### LocalBusiness
```json
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Business Name",
  "image": "https://example.com/photo.jpg",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Main St",
    "addressLocality": "City",
    "addressRegion": "ST",
    "postalCode": "12345",
    "addressCountry": "US"
  },
  "telephone": "+1-555-000-0000",
  "url": "https://example.com",
  "openingHoursSpecification": [{
    "@type": "OpeningHoursSpecification",
    "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "opens": "09:00", "closes": "17:00"
  }]
}
```

### Organization
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Company Name",
  "url": "https://example.com",
  "logo": "https://example.com/logo.png",
  "sameAs": ["https://twitter.com/handle", "https://linkedin.com/company/name"]
}
```

### Product
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Product Name",
  "image": "https://example.com/product.jpg",
  "description": "Product description",
  "brand": { "@type": "Brand", "name": "Brand Name" },
  "offers": {
    "@type": "Offer",
    "price": "29.99",
    "priceCurrency": "USD",
    "availability": "https://schema.org/InStock",
    "url": "https://example.com/product/"
  }
}
```

### BreadcrumbList
```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://example.com/" },
    { "@type": "ListItem", "position": 2, "name": "Category", "item": "https://example.com/category/" },
    { "@type": "ListItem", "position": 3, "name": "Page Title" }
  ]
}
```

---

## Core Web Vitals Thresholds

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| LCP (Largest Contentful Paint) | ≤2.5s | 2.5s - 4.0s | >4.0s |
| INP (Interaction to Next Paint) | <200ms | 200ms - 500ms | >500ms |
| CLS (Cumulative Layout Shift) | <0.1 | 0.1 - 0.25 | >0.25 |

*FID was replaced by INP in March 2024.*

**LCP fixes:** Preload LCP element, use CDN, defer JS, inline critical CSS, WebP images, set width/height on images.

**INP fixes:** Minimize JS execution, break long tasks (>50ms), use web workers, debounce event handlers.

**CLS fixes:** Set width/height on images/videos, reserve space for ads/embeds, use `transform` animations, preload fonts with `font-display: swap`.

---

## AI Overview Optimization

- AI Overviews appear in 50%+ of Google searches (2026)
- Question-based queries trigger AIO 99.2% of the time
- Structure: question-based H2 → 50-70 word direct answer → expand
- Use FAQ, HowTo, Article schemas to increase citation likelihood
- Strong E-E-A-T signals increase chance of being cited
- Sites cited in AIO see ~35% higher CTR

---

## E-E-A-T Signals

**Experience, Expertise, Authoritativeness, Trustworthiness**

Implement via:
- Author bylines with linked bio pages showing credentials
- Publication and "last updated" dates
- Links to authoritative external sources
- Third-party citations and reviews
- For YMYL (health, finance, legal): demonstrated professional expertise required

---

## Common Mistakes

- Keyword stuffing (write for humans)
- Missing/duplicate title tags and meta descriptions
- No canonical tags on duplicate content
- Broken internal links (404s)
- Redirect chains (consolidate to single hop)
- Uncompressed images (biggest LCP killer)
- Missing image dimensions (causes CLS)
- Render-blocking JS without async/defer
- Accidental noindex tags from staging
- AI content without editorial review
- Targeting multiple competing keywords on one page
- Orphan pages with no internal links
