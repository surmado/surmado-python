# Webhooks Integration

Receive real-time notifications when Surmado reports complete processing.

## Setup

Pass a `webhook_url` to any report method:

```python
from surmado import Surmado

client = Surmado()

result = client.signal(
    url="https://acme.com",
    brand_name="Acme Corp",
    email="you@acme.com",
    industry="B2B SaaS",
    location="United States",
    persona="CTOs at mid-market companies",
    pain_points="Integration challenges",
    brand_details="Modern dev-focused tooling",
    direct_competitors="Asana, Monday.com",
    webhook_url="https://your-server.com/api/surmado-webhook"
)
```

## Payload

Your endpoint receives a POST with this structure:

```json
{
    "event": "report.completed",
    "timestamp": "2025-12-17T20:33:58.737743+00:00",
    "report": {
        "id": "daSwEVPimdjKStdgx3HS",
        "token": "SIG-2025-12-3AHGD",
        "product": "signal",
        "status": "completed",
        "data_url": "https://api.surmado.com/v1/reports/daSwEVPimdjKStdgx3HS",
        "pdf_url": "https://api.surmado.com/v1/reports/view/...",
        "credits_refunded": false,
        "summary": {
            "business_name": "Acme Corp",
            "presence_score": 72,
            "category_share": 18.9,
            "authority_score": 85,
            "competitive_rank": 1,
            "competitive_tier": "Leader"
        }
    }
}
```

## Events

| Event | Description |
|-------|-------------|
| `report.completed` | Report finished processing successfully |
| `report.failed` | Report processing failed (includes `failure_reason`) |

## Requirements

- Webhook URL must use HTTPS
- Your endpoint must return a 2xx status code
- Timeout: 10 seconds

## Handling Failed Reports

When `event` is `report.failed`, the payload includes a `failure_reason` field and `credits_refunded: true` if credits were automatically refunded.

```python
# Example Flask webhook handler
@app.route("/api/surmado-webhook", methods=["POST"])
def surmado_webhook():
    payload = request.json
    event = payload["event"]
    report = payload["report"]

    if event == "report.completed":
        pdf_url = report["pdf_url"]
        # Process completed report...
    elif event == "report.failed":
        reason = report.get("failure_reason", "Unknown")
        # Handle failure...

    return "", 200
```
