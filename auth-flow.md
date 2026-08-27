# Auth Flow

1. User visits `GET /auth/login` → redirected to Google's OAuth consent screen
   (`state` param stored server-side for CSRF protection)
2. Google redirects back to `GET /auth/callback?code=...&state=...`
3. Server exchanges `code` for a Google access token, fetches user info
   (email, subject id)
4. Server finds-or-creates a `User` row keyed by email
5. Server issues its **own** opaque token:
   - `raw_token = secrets.token_urlsafe(32)` — given to the user, never stored
   - `token_hash = sha256(raw_token)` — stored in `api_tokens` table
   - expires in 90 days, revocable via `revoked` flag
6. User configures their MCP client with:
   ```json
   {
     "mcpServers": {
       "mcp-saas-platform": {
         "url": "https://your-domain.com/mcp",
         "headers": { "Authorization": "Bearer <raw_token>" }
       }
     }
   }
   ```
7. Every subsequent request: `auth_middleware` hashes the incoming bearer
   token, looks it up, checks `revoked` and `expires_at`, and sets the
   tenant context for that request.

## Why hash the token server-side?

If the `api_tokens` table were ever leaked/dumped, the hashes alone can't be
replayed as valid tokens (same principle as password hashing) — only the raw
token, which the server never persists, can authenticate.
