# UtsavAI Privacy Policy

**Effective Date:** November 1, 2026 &bull; **Version:** 1.0

## 1. Overview and Core Principles
UtsavAI is committed to protecting the privacy and confidentiality of couples, families, wedding guests, and vendors. We operate on a strict least-privilege, event-isolated data model protected by PostgreSQL Row-Level Security (RLS).

## 2. Information We Collect
- **Account Credentials:** Email addresses and authentication credentials managed securely via Supabase Auth. We do not store raw passwords.
- **Event Data:** Event names, dates, locations, budgets, guest estimates, schedule functions, and task lists entered by authenticated event collaborators.
- **Vendor Information:** Business names, contact details, service categories, and quotation records entered into the system.
- **GiftCircle Registries:** Wishlist items, price targets, guest reservation names, and guest-declared contribution amounts.

## 3. How We Use and Protect Your Data
Your data is used solely to provide event planning, budget tracking, scheduling, and gift registry services. All database operations enforce tenant isolation through cryptographic session variables and strict Row-Level Security policies.

## 4. Artificial Intelligence Processing
When AI features are engaged (PlanAI, BudgetAI suggestions, TimelineAI, and Adaptive Planning), context such as function schedules and budget constraints may be transmitted to Google Gemini models. We do not transmit payment credentials, bank account numbers, or sensitive government IDs to LLM providers.

## 5. Contact and Data Rights
You have the right to inspect, export, or permanently delete your account and associated event data. For privacy inquiries or deletion requests, contact our privacy officer at `privacy@utsavai.example.com`.

