# Integrations

Integration guides for using the Surmado Python SDK with third-party platforms and automation tools.

## Available Integrations

| Integration | Description | Guide |
|-------------|-------------|-------|
| Zapier | Trigger Surmado reports from Zapier workflows | [zapier.md](zapier.md) |
| Make (Integromat) | Connect Surmado to Make scenarios | [make.md](make.md) |
| n8n | Self-hosted workflow automation with Surmado | [n8n.md](n8n.md) |
| Webhooks | Receive real-time report completion notifications | [webhooks.md](webhooks.md) |

## Common Patterns

All integrations follow the same core pattern:

1. **Trigger** — An event starts the workflow (schedule, form submission, API call)
2. **Run Report** — Call `client.signal()`, `client.scan()`, or `client.bundle()` via the SDK
3. **Receive Results** — Use `webhook_url` for async delivery or `client.wait_for_report()` for polling
4. **Act on Data** — Route the completed report to your destination (email, Slack, dashboard, etc.)

## Rerun Methods for Automation

For recurring reports, use the rerun methods — they require minimal inputs because they pull from your stored brand profile:

```python
# 3 fields instead of 10+
result = client.signal_rerun(
    brand_slug="acme_corp",
    persona_slug="cto-enterprise",
    email="you@acme.com"
)
```

See [Rerun Methods](../README.md#rerun-methods) in the main README for full details.
