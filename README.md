# Surmado Python Client

Official Python SDK for [Surmado](https://surmado.com) — the anti-dashboard marketing intelligence engine.

**SEO audits, AI visibility testing, and strategic advisory. Reports cost $25–$50. No subscriptions. No dashboards.**

## Installation

```bash
pip install surmado
```

## Quick Start

```python
from surmado import Surmado

# Initialize (or set SURMADO_API_KEY env var)
client = Surmado(api_key="sur_live_...")

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
print(f"Token (save for Solutions): {report['token']}")

# Wait for completion (or use webhooks)
completed = client.wait_for_report(report["report_id"])
print(f"PDF ready: {completed['download_url']}")
```

## Features

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
    brand_name="Acme Corp",                                           # max 100 chars
    business_story="We're a B2B SaaS company in project management...", # max 2000 chars
    decision="Should we expand to enterprise market?",                # max 1500 chars
    success="$10M ARR in 18 months",                                  # max 1000 chars
    timeline="Q2 2025",                                               # max 200 chars
    scale_indicator="$2M ARR, 20 employees"                           # max 100 chars
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

## Rerun Methods (Automation-Friendly)

Once you've set up a brand with personas in the Surmado dashboard, you can run reports with minimal code:

### Signal Rerun

```python
# Just 4 fields instead of 10+
result = client.signal_rerun(
    brand_slug="acme_corp",
    persona_slug="cto-enterprise",
    email="you@acme.com",
    tier="basic"
)
```

### Scan Rerun

```python
# Just 3 fields
result = client.scan_rerun(
    brand_slug="acme_corp",
    email="you@acme.com",
    tier="premium"
)
```

Perfect for:
- **Zapier/Make/n8n workflows** — set up brand once, automate reports
- **Scheduled monitoring** — weekly SEO scans or monthly AI visibility checks
- **Dashboard "Run Again"** — one-click report refresh

## Async Reports

All reports are processed asynchronously (~15 minutes). Two ways to get results:

### Option 1: Polling

```python
report = client.signal(...)
completed = client.wait_for_report(report["report_id"], timeout_minutes=20)
print(completed["download_url"])
```

### Option 2: Webhooks

```python
report = client.signal(
    ...,
    webhook_url="https://your-server.com/webhook"
)
# Your webhook receives POST when report completes
```

## Response Format

Report creation returns HTTP 202 Accepted:

```python
{
    "report_id": "rpt_abc123def456",
    "token": "tok_xyz789abc123",  # Save this for Solutions Mode 1
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
    "pptx_download_url": "https://storage.googleapis.com/...", # PPTX (Pro only)
    "intelligence_download_url": "https://storage.googleapis.com/...", # Full JSON
}
```

## Error Handling

```python
from surmado import (
    Surmado,
    AuthenticationError,
    InsufficientCreditsError,
    NotFoundError,
    ValidationError,
    SurmadoError
)

client = Surmado()

try:
    result = client.signal(...)
except AuthenticationError:
    print("Invalid API key")
except InsufficientCreditsError as e:
    print(f"Need more credits: {e.response}")
except NotFoundError:
    print("Brand or report not found")
except ValidationError as e:
    print(f"Invalid request: {e}")
except SurmadoError as e:
    print(f"API error: {e.status_code} - {e}")
```

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

| Product | Price | Credits |
|---------|-------|---------|
| Scan Basic | $25 | 1 |
| Scan Premium | $50 | 2 |
| Signal Basic | $25 | 1 |
| Signal Pro | $50 | 2 |
| Solutions | $50 | 2 |

**Credits:** 1 credit = $25. No subscriptions. Credits don't expire.

## Links

- [Documentation](https://help.surmado.com/docs/api-reference/)
- [Get API Key](https://surmado.com/login)
- [API Examples](https://github.com/surmado/surmado-api-public)

## About Surmado

Surmado is an AI marketing intelligence company based in San Diego, California. Founded in October 2025, we build tools that help businesses understand their visibility in AI search results and traditional SEO.

- Website: [surmado.com](https://surmado.com)
- Help: [help.surmado.com](https://help.surmado.com)
- Contact: [hi@surmado.com](mailto:hi@surmado.com)

## License

MIT
