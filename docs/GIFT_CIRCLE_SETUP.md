# GiftCircle Setup & Operational Guide

## Overview

GiftCircle is the Phase 5 module of UtsavAI. It provides couples with an intelligent wedding gift registry and group gifting system that guests can access without creating an account.

---

## 1. Local Database Migrations

GiftCircle requires migrations `20261101001700` and `20261101001800`.

### Applying to Local Test Database
```bash
# Set environment variables
ADMIN_URL="postgresql://postgres:<password>@localhost:5432/postgres"
APP_ROLE_PASSWORD="ci_runtime_password"

# Run setup script (creates database if missing and applies all migrations)
scripts/setup_local_db.sh utsavai_test
```

### Applying to Supabase Development Project
```bash
npx supabase db push
```

---

## 2. Configuration & Environment Variables

No third-party payment gateways or API keys are required for GiftCircle. The system relies strictly on PostgreSQL row-level security and SHA-256 token hashing.

Required base environment variables:
```env
# Backend (apps/api/.env)
APP_ENV=development
DATABASE_URL=postgresql://utsavai_app:<password>@localhost:5432/utsavai_test
DATABASE_ADMIN_URL=postgresql://postgres:<password>@localhost:5432/utsavai_test
CORS_ALLOWED_ORIGINS=http://localhost:3000

# Frontend (apps/web/.env.local)
NEXT_PUBLIC_APP_ENV=development
API_BASE_URL=http://localhost:8000
BFF_ALLOWED_ORIGINS=http://localhost:3000
```

---

## 3. Running Backend and Frontend

### Starting FastAPI Backend
```bash
cd apps/api
uv run uvicorn app.main:app_factory --factory --reload --port 8000
```

### Starting Next.js Web Application
```bash
cd apps/web
npm run dev
```

---

## 4. Host Workflow
1. Navigate to your celebration dashboard and open an event.
2. Click the **GiftCircle** tab in the workspace navigation bar.
3. Click **Add Gift Item** to add items to your wishlist:
   - Select **Individual Gift** for traditional items (e.g., espresso machine, dinnerware).
   - Select **Group Gifting** for funds or larger experiences (e.g., honeymoon stay, celebration fund) and set a target amount.
4. Click **Share Registry** to generate a secure share link for wedding guests.
5. Copy and share the URL (`http://localhost:3000/g/<token>`) with your guests.

---

## 5. Guest Workflow
1. Open the share link provided by the hosts (no account or login required).
2. Browse the curated wishlist and filter by category or availability.
3. For individual gifts:
   - Click **Reserve This Gift** to prevent duplicate purchases.
   - Enter your name/alias and warm wishes.
   - Save the generated cancellation code in case your plans change.
4. For group gifts:
   - Click **Contribute Any Amount**.
   - Enter your intended pledge amount (up to the remaining target capacity).
   - Settle your contribution directly with the couple on celebration day.
