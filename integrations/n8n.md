# n8n Integration

Run Surmado reports from self-hosted n8n workflows.

## Setup

1. Create a workflow with your desired trigger
2. Add an **HTTP Request** node
3. Store your API key in n8n credentials (Header Auth)

## Example: Scheduled Bundle Report

**HTTP Request Node Configuration:**

- **Method**: POST
- **URL**: `https://api.surmado.com/v1/reports/bundle`
- **Authentication**: Header Auth
  - **Name**: `X-API-Key`
  - **Value**: `{{ $credentials.surmadoApi.apiKey }}`
- **Body (JSON)**:
```json
{
    "brand_slug": "acme_corp",
    "email": "reports@acme.com",
    "webhook_url": "https://your-n8n-instance.com/webhook/surmado-callback"
}
```

## Receiving Results

Add a **Webhook** node as a separate workflow to receive completed reports:

1. Create a new workflow with a Webhook trigger
2. Set the webhook URL as the `webhook_url` in your report request
3. Parse the incoming payload for `event`, `report.status`, and `report.pdf_url`

## Recommended Pattern

1. **Trigger**: Cron (weekly/monthly) or Webhook (incoming)
2. **HTTP Request**: POST to Surmado API
3. **Webhook receiver**: Separate workflow to handle completed reports
4. **Actions**: Send email, post to Slack, update Airtable, etc.

## Notes

- n8n has no execution timeout issues — but still prefer webhooks over polling for report completion
- Use n8n's credential store for API key management
- Use rerun endpoints (`/signal/rerun`, `/scan/rerun`) for recurring reports
