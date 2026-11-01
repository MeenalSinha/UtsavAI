# UtsavAI Staging Deployment Guide

## 1. Purpose
The staging environment mirrors production architecture and configuration while providing isolated verification for release candidates.

## 2. Infrastructure Setup
- **Staging URL:** `https://staging.utsavai.com`
- **Staging API:** `https://staging-api.utsavai.com`
- **Staging Database:** Dedicated Supabase staging project (`utsavai-staging`).

## 3. Deployment Procedure
1. Create a release tag: `git tag -a v1.0.0-rc1 -m "Release Candidate 1"`
2. Trigger the automated staging workflow or deploy container:
   ```bash
   gcloud run deploy utsavai-api-staging \
     --image gcr.io/<PROJECT_ID>/utsavai-api:v1.0.0-rc1 \
     --region asia-south1 \
     --set-env-vars APP_ENV=staging,LOG_JSON=true
   ```
3. Run migrations on staging database:
   ```bash
   psql "$STAGING_DATABASE_ADMIN_URL" -f supabase/migrations/20261101001900_change_proposals_schema.sql
   psql "$STAGING_DATABASE_ADMIN_URL" -f supabase/migrations/20261101002000_change_proposals_rls_and_grants.sql
   ```
4. Seed demo dataset for end-to-end user testing:
   ```bash
   DATABASE_URL="$STAGING_DATABASE_URL" python scripts/seed_demo_data.py
   ```

