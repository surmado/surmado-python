# Zapier Integration

Run Surmado reports from Zapier workflows using the Python SDK via Zapier's Code by Zapier action.

## Setup

1. Create a Zap with your desired trigger (schedule, form submission, etc.)
2. Add a **Code by Zapier** action (Python)
3. Set `SURMADO_API_KEY` as an input variable mapped from your Zapier storage or trigger
4. Use the rerun methods for minimal configuration

## Example: Scheduled Signal Report

```python
# Code by Zapier action
# Input: api_key (from Zapier storage)
import requests

headers = {
    "X-API-Key": input_data["api_key"],
    "Content-Type": "application/json",
    "User-Agent": "surmado-zapier/1.0"
}

response = requests.post(
    "https://api.surmado.com/v1/reports/signal/rerun",
    json={
        "brand_slug": "acme_corp",
        "persona_slug": "cto-enterprise",
        "email": "reports@acme.com",
        "webhook_url": "https://hooks.zapier.com/hooks/catch/YOUR_HOOK_ID"
    },
    headers=headers,
    timeout=30
)

output = response.json()
```

## Recommended Pattern

1. **Trigger**: Schedule (weekly/monthly) or form submission
2. **Action**: Code by Zapier → call Surmado rerun endpoint
3. **Webhook**: Set `webhook_url` to a Zapier Catch Hook to receive results
4. **Follow-up**: Route completed report to email, Slack, Google Sheets, etc.

## Notes

- Zapier's Code by Zapier has a 10-second timeout — use `webhook_url` instead of polling
- Store your API key in Zapier Storage, not hardcoded in the action
- Use rerun methods (`signal/rerun`, `scan/rerun`) to minimize payload size
