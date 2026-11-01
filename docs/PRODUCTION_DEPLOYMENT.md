# UtsavAI Production Deployment Guide

## Architecture Overview
- **Frontend:** Next.js 15 on Vercel (Edge-routed, SSR, same-origin BFF proxy).
- **Backend API:** FastAPI on Google Cloud Run (Containerized, auto-scaling 0 to N).
- **Database:** Supabase Managed PostgreSQL 16 (Row-Level Security, transaction connection pooler).
- **AI Engine:** Google Gemini Pro via official Google GenAI SDK (with deterministic fallback).

---

## 1. Prerequisites
1. **Supabase Project:**
   - Run all migrations in `supabase/migrations/` sequentially.
   - Verify 22 tables have RLS enabled and `app.current_user_id()` is defined.
2. **Google Cloud Project:**
   - Enable Artifact Registry and Cloud Run API.
   - Configure Secret Manager for `DATABASE_URL` and `GEMINI_API_KEY`.
3. **Vercel Account:**
   - Link repository `MeenalSinha/UtsavAI` with root directory set to `apps/web`.

---

## 2. Environment Variables Configuration

### Backend (Cloud Run)
| Variable | Value / Format | Purpose |
| :--- | :--- | :--- |
| `APP_ENV` | `production` | Enables strict error redaction and production defaults |
| `DATABASE_URL` | `postgresql://utsavai_app:<pw>@<host>:6543/postgres?sslmode=require` | Supabase pooler connection string |
| `SUPABASE_URL` | `https://<ref>.supabase.co` | Supabase auth issuer |
| `GEMINI_API_KEY` | `AIza...` | Google GenAI SDK key (optional for AI generation) |
| `CORS_ALLOWED_ORIGINS` | `https://app.utsavai.com` | Allowed frontend origins |
| `LOG_JSON` | `true` | Structured production logging |
| `LOG_LEVEL` | `INFO` | Standard production logging verbosity |

### Frontend (Vercel)
| Variable | Value / Format | Purpose |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://<ref>.supabase.co` | Public Supabase endpoint |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJ...` | Supabase anon key |
| `NEXT_PUBLIC_APP_ENV` | `production` | Frontend environment flag |
| `API_BASE_URL` | `https://api.utsavai.com` | Cloud Run backend origin (BFF proxy only) |

---

## 3. Container Build & Push (FastAPI)
```bash
# Build production container
docker build -t gcr.io/<PROJECT_ID>/utsavai-api:v1.0.0 apps/api/

# Push to Artifact Registry
docker push gcr.io/<PROJECT_ID>/utsavai-api:v1.0.0

# Deploy to Cloud Run
gcloud run deploy utsavai-api \
  --image gcr.io/<PROJECT_ID>/utsavai-api:v1.0.0 \
  --platform managed \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars APP_ENV=production,LOG_JSON=true \
  --set-secrets DATABASE_URL=DATABASE_URL:latest,GEMINI_API_KEY=GEMINI_API_KEY:latest
```

---

## 4. Post-Deployment Smoke Verification
Run automated health check:
```bash
curl -I https://api.utsavai.com/api/v1/health
curl -I https://api.utsavai.com/api/v1/health/ready
```
Both endpoints must return `HTTP 200 OK`.

