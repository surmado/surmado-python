# Surmado Python SDK

[![PyPI version](https://img.shields.io/pypi/v/surmado.svg)](https://pypi.org/project/surmado/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

Official Python client for Surmado's AI visibility testing and SEO reports.

One-time reports. No subscriptions. API-first.

## Installation

```bash
pip install surmado
```

## Quick Start

```python
from surmado import Surmado

client = Surmado()  # uses SURMADO_API_KEY env var

# Run an AI Visibility Test
report = client.signal(
    url="https://example.com",
    brand_name="Example Brand",
    email="you@example.com",
    industry="E-commerce",
    location="United States",
    persona="Small business owners looking for affordable solutions",
    pain_points="Finding reliable vendors, managing costs",
    brand_details="Affordable solutions for growing businesses",
    direct_competitors="Competitor A, Competitor B"
)

print(f"Report queued: {report['report_id']}")

# Wait for completion (or use webhooks)
completed = client.wait_for_report(report["report_id"])
print(f"PDF ready: {completed['download_url']}")
print("(Save for Surmado Solutions) Report Token: ", completed['token'])
```

## Products

### Signal — AI Visibility Testing

Test how your brand appears across 7 AI platforms: ChatGPT, Perplexity, Google Gemini, Claude, Meta AI, Grok, DeepSeek.

```python
result = client.signal(
    url="https://acme.com",
    brand_name="Acme Corp",                              # max 100 chars
    email="you@acme.com",
    industry="B2B SaaS",                                 # max 200 chars
    location="United States",                            # max 200 chars
    persona="CTOs at mid-market companies",              # max 800 chars
    pain_points="Integration challenges, lack of visibility",  # max 1000 chars
    brand_details="Modern, dev-focused tooling",         # max 1200 chars
    direct_competitors="Asana, Monday.com",              # max 500 chars
    tier="pro"  # "basic" (1 credit) or "pro" (2 credits)
)
```

### Scan — SEO Auditing

Comprehensive technical SEO audits with prioritized recommendations.

```python
result = client.scan(
    url="https://acme.com",
    brand_name="Acme Corp",
    email="you@acme.com",
    tier="premium",  # "basic" (1 credit) or "premium" (2 credits)
    competitor_urls=["https://competitor1.com", "https://competitor2.com"]
)
```

### Solutions — Strategic Advisory

Multi-AI strategic recommendations from 6 specialized agents.

**Mode 1: With Signal Token** (recommended)

```python
# Run Signal first, then pass the token
signal_result = client.signal(...)
solutions_result = client.solutions(
    email="you@acme.com",
    signal_token=signal_result["token"]
)
```

**Mode 2: Standalone**

```python
result = client.solutions(
    email="you@acme.com",
    brand_name="Acme Corp",
    business_story="We're a B2B SaaS company in project management...",
    decision="Should we expand to enterprise market?",
    success="$10M ARR in 18 months",
    timeline="Q2 2025",
    scale_indicator="$2M ARR, 20 employees"
)
```

**Mode 3: With Financial Analysis**

```python
result = client.solutions(
    email="you@acme.com",
    signal_token=signal_result["token"],
    include_financial="yes",
    financial_context="Growing but need to optimize costs",
    monthly_revenue="$50K",
    monthly_costs="$40K",
    cash_available="$200K"
)
```

## Rerun Methods

Once you've set up a brand with personas in the Surmado dashboard, run reports with minimal code:

```python
# Signal: 4 fields instead of 10+
result = client.signal_rerun(
    brand_slug="acme_corp",
    persona_slug="cto-enterprise",
    email="you@acme.com",
    tier="basic"
)

# Scan: 3 fields
result = client.scan_rerun(
    brand_slug="acme_corp",
    email="you@acme.com",
    tier="premium"
)
```

Perfect for Zapier/Make/n8n workflows, scheduled monitoring, and dashboard integrations.

## Async Reports & Polling

All reports process asynchronously (~15 minutes). Two ways to get results:

### Polling

```python
report = client.signal(...)

# Block until complete (default 20 min timeout)
completed = client.wait_for_report(report["report_id"], timeout_minutes=20)
print(completed["download_url"])
```

### Webhooks

```python
report = client.signal(
    ...,
    webhook_url="https://your-server.com/webhook"
)
# Your webhook receives POST with full report data when complete
```

## Handling Errors

When the API returns a non-success status code, a typed exception is raised:

```python
from surmado import (
    Surmado,
    AuthenticationError,
    InsufficientCreditsError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    SurmadoError
)

client = Surmado()

try:
    result = client.signal(...)
except AuthenticationError:
    print("Invalid or missing API key")
except InsufficientCreditsError as e:
    print(f"Not enough credits: {e.response}")
except RateLimitError:
    print("Too many requests — back off and retry")
except NotFoundError:
    print("Brand or report not found")
except ValidationError as e:
    print(f"Invalid request params: {e}")
except SurmadoError as e:
    print(f"API error: {e.status_code} - {e}")
```

### Error Status Mapping

| Status Code | Exception |
|-------------|-----------|
| 400 | `ValidationError` |
| 401 | `AuthenticationError` |
| 402 | `InsufficientCreditsError` |
| 404 | `NotFoundError` |
| 429 | `RateLimitError` |
| ≥500 | `SurmadoError` |

All exceptions inherit from `SurmadoError` and include `status_code` and `response` attributes.

## Timeouts

Default request timeout is 30 seconds. Configure per-client or per-request:

```python
# Client-level default
client = Surmado(api_key="...", timeout=60)

# Per-request override
result = client.signal(..., timeout=45)
```

For `wait_for_report`, the polling timeout is separate:

```python
# Wait up to 30 minutes for long reports
completed = client.wait_for_report(report_id, timeout_minutes=30)
```

## Response Format

Report creation returns HTTP 202 Accepted:

```python
{
    "report_id": "rpt_abc123def456",
    "token": "tok_xyz789abc123",  # Save for Solutions Mode 1
    "org_id": "org_xyz789",
    "product": "signal",
    "status": "queued",
    "brand_slug": "example_brand",
    "brand_name": "Example Brand",
    "credits_used": 1,
    "created_at": "2025-01-15T10:30:00Z"
}
```

Completed reports include download URLs (expire in 15 minutes):

```python
{
    "status": "completed",
    "download_url": "https://storage.googleapis.com/...",      # PDF
    "pptx_download_url": "https://storage.googleapis.com/...", # PPTX (Pro/Premium)
}
```

## Webhook Payload

When using `webhook_url`, your endpoint receives a POST with this structure:

```python
{
    "event": "report.completed",  # or "report.failed"
    "timestamp": "2025-12-17T20:33:58.737743+00:00",
    "report": {
        "id": "daSwEVPimdjKStdgx3HS",
        "token": "SIG-2025-12-3AHGD",
        "product": "signal",
        "status": "completed",
        "tier": "pro",
        "data_url": "https://api.surmado.com/v1/reports/daSwEVPimdjKStdgx3HS",
        "pdf_url": "https://api.surmado.com/v1/reports/view/C9VUr2VhSQvPG...",
        "credits_refunded": False,
        "summary": {
            "business_name": "Acme Corp",
            "contact_email": "you@example.com",
            "industry": "B2B SaaS",
            "brand_url": "https://acme.com",
            "location": "San Francisco, CA",
            "presence_score": 72,
            "category_share": 18.9,
            "authority_score": 85,
            "competitive_rank": 1,
            "competitive_tier": "Leader",
            "top_competitor": "Competitor X",
            "insights_summary": ["..."],
            "pain_points_summary": ["..."]
        }
    }
}
```

### Webhook Fields

| Field | Type | Description |
|-------|------|-------------|
| `event` | `string` | `report.completed` or `report.failed` |
| `timestamp` | `string` | ISO 8601 when webhook was sent |
| `report.id` | `string` | Report ID |
| `report.token` | `string` | Report token (e.g., `SIG-2025-12-3AHGD`) |
| `report.product` | `string` | `signal`, `scan`, `solutions`, or `monitor` |
| `report.status` | `string` | `completed` or `failed` |
| `report.tier` | `string` | `basic`, `pro`, or `premium` |
| `report.data_url` | `string` | API endpoint to fetch full report |
| `report.pdf_url` | `string` | Magic link to view PDF (30-day expiry) |
| `report.credits_refunded` | `bool` | `True` if credits were refunded |
| `report.failure_reason` | `string` | Error message (only present when `status=failed`) |
| `report.summary` | `object` | Curated metrics (fields vary by product) |

### Summary Fields (Signal)

| Field | Type | Description |
|-------|------|-------------|
| `business_name` | `string` | Brand name |
| `contact_email` | `string` | Email from request |
| `industry` | `string` | Industry category |
| `brand_url` | `string` | Brand website |
| `location` | `string` | Geographic location |
| `presence_score` | `number` | AI visibility score (0-100) |
| `category_share` | `number` | Share of category mentions (%) |
| `authority_score` | `number` | Brand authority rating (0-100) |
| `competitive_rank` | `number` | Rank among competitors |
| `competitive_tier` | `string` | `Leader`, `Challenger`, etc. |
| `top_competitor` | `string` | Highest-ranked competitor |
| `insights_summary` | `string[]` | Key insights from analysis |
| `pain_points_summary` | `string[]` | Customer pain points |

### Summary Fields (Scan)

| Field | Type | Description |
|-------|------|-------------|
| `business_name` | `string` | Brand name |
| `contact_email` | `string` | Email from request |
| `seo_score` | `number` | Overall SEO score (0-100) |
| `performance_score` | `number` | Page performance score (0-100) |
| `accessibility_score` | `number` | Accessibility score (0-100) |
| `total_pages` | `number` | Total pages analyzed |
| `schema_types_count` | `number` | Number of schema markup types found |
| `critical_issues_count` | `number` | Count of critical SEO issues |
| `critical_issues` | `string[]` | List of critical issues found |
| `content_coverage_percentage` | `number` | Content coverage (%) |
| `page_analysis_summary` | `string` | Executive summary of page analysis |
| `link_analysis_summary` | `string` | Executive summary of link analysis |
| `quick_wins` | `object` | Combined quick wins from analysis |



## Field Length Limits

| Field | Max Length |
|-------|------------|
| brand_name | 100 chars |
| industry | 200 chars |
| location | 200 chars |
| persona | 800 chars |
| pain_points | 1000 chars |
| brand_details | 1200 chars |
| direct_competitors | 500 chars |
| indirect_competitors | 500 chars |
| keywords | 500 chars |
| product | 1000 chars |
| business_story | 2000 chars |
| decision | 1500 chars |
| success | 1000 chars |
| timeline | 200 chars |
| scale_indicator | 100 chars |

## Pricing

1 credit = $25. Basic reports cost 1 credit, Pro/Premium cost 2. No subscriptions.

## Versioning

This package follows [SemVer](https://semver.org/). To check your installed version:

```python
import surmado
print(surmado.__version__)
```

## Links

- **Docs:** [help.surmado.com/docs/api-reference](https://help.surmado.com/docs/api-reference/)
- **API Key:** [surmado.com/login](https://surmado.com/login)
- **Examples:** [github.com/surmado/surmado-api-public](https://github.com/surmado/surmado-api-public)
- **Issues:** [github.com/surmado/surmado-python/issues](https://github.com/surmado/surmado-python/issues)

## License

MIT
