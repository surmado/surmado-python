# Make (Integromat) Integration

Run Surmado reports from Make scenarios using HTTP modules.

## Setup

1. Create a scenario with your desired trigger
2. Add an **HTTP > Make a request** module
3. Configure the request to call the Surmado API

## Example: Signal Rerun

**HTTP Module Configuration:**

- **URL**: `https://api.surmado.com/v1/reports/signal/rerun`
- **Method**: POST
- **Headers**:
  - `X-API-Key`: your API key
  - `Content-Type`: `application/json`
- **Body**:
```json
{
    "brand_slug": "acme_corp",
    "persona_slug": "cto-enterprise",
    "email": "reports@acme.com",
    "webhook_url": "https://hook.make.com/YOUR_WEBHOOK_URL"
}
```

## Recommended Pattern

1. **Trigger**: Scheduler or Webhook (incoming)
2. **Action**: HTTP module → POST to Surmado API
3. **Webhook**: Use a Make webhook as the `webhook_url` to receive completed reports
4. **Router**: Branch on `event` field — route `report.completed` and `report.failed` separately

## Notes

- Use Make's key store for your API key
- Reports take ~15 minutes — always use webhook-based flows, not polling
- Use rerun endpoints to keep payloads minimal
