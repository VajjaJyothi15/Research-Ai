# ResAI Security & Compliance Policy

## Server-Side Request Forgery (SSRF) Protection
ResAI enforces multi-layered SSRF validation on all URL fetching operations (`fetch_url`, `web_search`, `extract_page_content`):
1. **URL Scheme Restriction**: Only `http://` and `https://` schemes are permitted.
2. **IP Network Range Blocking**: Resolves hostnames via DNS prior to connection and blocks private, loopback, link-local, multicast, and cloud metadata ranges (e.g. `127.0.0.0/8`, `10.0.0.0/8`, `169.254.169.254`).
3. **Redirect Target Re-validation**: Re-verifies every HTTP 30x redirect destination against SSRF rules before following redirects.

## Upload & File Handling Security
1. **Allowlisted Extensions**: `.pdf`, `.txt`, `.md`, `.csv`, `.xlsx`.
2. **Size Limits**: Enforces default 10MB maximum upload limit.
3. **No Code Execution**: Document contents are sanitized and treated as untrusted input. Spreadsheet macros and executable scripts are never executed.

## Prompt Injection Resistance
Untrusted web page content and uploaded text are passed inside strict data blocks and sanitized using input filters to prevent prompt override or instruction injection.
