---
name: xquik-x-data
description: Research public X posts, accounts, and trends with Xquik when a user asks for X or Twitter social context, account analysis, post search, or trend evidence.
---

# Xquik X Data

Use this skill when a user asks for current public X data, including post search, account context, trend checks, or evidence from public conversations.

## Requirements

- An Xquik API key in `XQUIK_API_KEY`
- Permission to query public X data for the user's task

Never print, log, or commit the API key. Do not use this skill for private account data, password-protected content, or attempts to bypass platform access controls.

## Preferred MCP Setup

When the agent runtime supports remote MCP servers, register Xquik's MCP endpoint:

```json
{
  "mcpServers": {
    "xquik": {
      "url": "https://xquik.com/mcp",
      "headers": {
        "Authorization": "Bearer ${XQUIK_API_KEY}"
      }
    }
  }
}
```

Use the MCP tools for searches, account lookups, and trend checks. Prefer structured responses over screenshots or copied page text.

## REST Fallback

When MCP is unavailable but outbound HTTPS is allowed, inspect the OpenAPI contract at `https://xquik.com/openapi.json` and call the public REST routes that match the task. Useful public X routes include:

- `/api/v1/x/tweets/search`
- `/api/v1/x/users/search`
- `/api/v1/x/trends`

Keep REST calls scoped to the user's request. Store the API key in an environment variable and pass it through the documented auth header. Do not paste secrets into prompts, notebooks, shell history, or output.

## Research Workflow

1. Restate the search target, date range, language, and account filters.
2. Query the smallest route that can answer the question.
3. Keep raw evidence separate from interpretation.
4. Cite post URLs, handles, timestamps, and query terms when summarizing.
5. Mark gaps clearly when data is missing, rate-limited, or outside scope.

## Output Rules

- Use concise evidence summaries.
- Do not claim full platform coverage from a sampled query.
- Do not infer identity, intent, or sentiment beyond the available public data.
- Do not disclose internal implementation details, private routing, costs, or provider names.
- Ask for a narrower query when the request is too broad to validate.
