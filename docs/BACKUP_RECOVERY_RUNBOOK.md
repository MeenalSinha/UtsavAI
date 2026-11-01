# UtsavAI Backup & Disaster Recovery Runbook

## 1. Automated Backups
- **Supabase Point-in-Time Recovery (PITR):** Continuous WAL archiving allowing restoration to any second in the preceding 7 days (or 30 days on Enterprise tier).
- **Daily Schema & Data Dumps:** Scheduled automated `pg_dump` jobs exporting to Cloud Storage with KMS encryption.

## 2. Disaster Recovery Procedure
In the event of database corruption or primary region disaster:
1. Navigate to Supabase Project Dashboard -> Database -> Backups.
2. Select target recovery timestamp (e.g. 5 minutes prior to incident).
3. Initiate clone to a new restore instance.
4. Update `DATABASE_URL` secret in Google Secret Manager:
   ```bash
   gcloud secrets versions add DATABASE_URL --data-file=new_connstring.txt
   ```
5. Restart Cloud Run service to establish connections to the restored database:
   ```bash
   gcloud run services update utsavai-api --region asia-south1
   ```
6. Execute `/api/v1/health/ready` to verify connectivity.

