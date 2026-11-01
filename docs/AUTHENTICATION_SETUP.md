# Authentication Setup

## Architecture

```text
Browser ──(HTTP-only cookie)──> Next.js (middleware + Server Actions + BFF Route Handler)
                                    │  getUser() validates the session with Supabase Auth
                                    │  Authorization: Bearer <access token>
                                    ▼
                                FastAPI ── verifies JWT (JWKS, issuer, audience, exp, role)
                                    │  BEGIN; set_config('app.user_id', sub, true)
                                    ▼
                                PostgreSQL (role utsavai_app, NOBYPASSRLS, RLS policies)
```

* Supabase Auth is the only identity provider. No passwords or custom tokens are handled here.
* All auth calls run on the server (Server Actions and route handlers) with `@supabase/ssr`
  using the `getAll`/`setAll` cookie interface. Cookies are forced to HTTP-only, SameSite=Lax and
  Secure in production, so browser JavaScript can never read a token. No browser Supabase client exists.
* Middleware refreshes the session on every request and redirects unauthenticated users away from
  `/dashboard`, `/events` and `/profile`. The authenticated layout re-validates on the server.
* The BFF (`/api/bff/*`) allow-lists routes and methods, rejects cross-origin mutations (Origin /
  `Sec-Fetch-Site` check), forwards only whitelisted query parameters and returns the standard
  error envelope. Business rules live only in FastAPI.
* FastAPI accepts only asymmetric JWTs (ES256, RS256, EdDSA) from the project JWKS, or HS256 when a
  legacy shared secret is configured and no JWKS URL is set. The algorithm comes from an allow-list,
  never from the token header. Required claims: `exp`, `iat`, `sub` (UUID), `iss`, `aud`, and
  `role = authenticated`.
* The user id comes only from the verified `sub` claim. Request bodies cannot supply an owner
  (`extra=forbid`) and identity headers are ignored.

## Supabase project configuration

1. **URL configuration** (Authentication, URL Configuration)
   * Site URL: your deployed web origin (local: `http://localhost:3000`).
   * Redirect URLs: `<origin>/auth/callback` for every environment.
2. **Email provider**: enable email and password sign-in. Keep "Confirm email" enabled for
   production. Disable it only in the dedicated E2E test project.
3. **JWT signing keys**: use asymmetric signing keys (JWKS). No secret is copied into UtsavAI.
   The backend derives `https://<ref>.supabase.co/auth/v1/.well-known/jwks.json` automatically.
4. **Password policy**: minimum length 8 or higher. The app enforces length, a letter and a digit
   client-side and server-side before calling Supabase.
5. **Email templates** (PKCE): the default confirmation and recovery links work with
   `/auth/callback` (`?code=`). Token-hash links are also handled:
   `{{ .SiteURL }}/auth/callback?token_hash={{ .TokenHash }}&type=email&next=/dashboard` and
   `...&type=recovery`.
6. **Rate limits**: tune Supabase Auth rate limits for sign-in, sign-up and password reset. They are
   the primary brute-force defence. Add CAPTCHA in Supabase if abuse appears.

## Flows

| Flow | Route | Behaviour |
| --- | --- | --- |
| Register | `/sign-up` | Server Action `signUp`; shows a verification message; identical response for existing and new addresses |
| Verify email | `/auth/callback` | Exchanges `code` or verifies `token_hash`, then redirects to a validated relative path |
| Sign in | `/sign-in` | Generic error for bad credentials; honours a validated `next` path |
| Session refresh | middleware | Refreshes expiring tokens and rewrites cookies |
| Sign out | topbar | Server Action `signOut` clears cookies |
| Forgot password | `/forgot-password` | Always shows the same confirmation |
| Reset password | `/reset-password` | Requires the recovery session created by the emailed link |
| Expired session | any API call | BFF returns 401, the client redirects to `/sign-in?reason=expired&next=...` |

## Profile provisioning

The first authenticated call to `GET /api/v1/me` (or `POST /api/v1/events`) inserts the profile with
`INSERT ... ON CONFLICT DO NOTHING` using the verified `sub`. A database policy independently
requires `user_id` to equal the caller. No database trigger on `auth.users` is needed.

## Verifying your setup

1. Start both apps with real variables.
2. Register, follow the email link, land on the dashboard.
3. Create an event and confirm the row in the `events` and `event_members` tables.
4. Run `scripts/verify_supabase_live.py` (see DATABASE_SETUP.md).
5. Optionally run the Playwright scenario against a dedicated test project (TESTING_GUIDE.md).
