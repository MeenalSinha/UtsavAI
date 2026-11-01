# UtsavAI AI Usage & Algorithmic Transparency Disclosure

**Effective Date:** November 1, 2026 &bull; **Version:** 1.0

## 1. Purpose and Architecture
UtsavAI employs artificial intelligence to eliminate tedious planning overhead and offer contextual insights for multi-day cultural events. Our system is engineered with strict human-in-the-loop safeguards: **no AI model can autonomously alter your event schedule, update your budget, sign vendor agreements, or modify your gift registry without explicit user approval.**

## 2. Underlying Models & Service Providers
Where AI generation is active, UtsavAI uses Google Gemini large language models via the official Google GenAI SDK with Pydantic structured output validation.

In environments where AI capabilities are disabled or API quotas are unavailable, UtsavAI automatically falls back to deterministic heuristic engines and localized calculation algorithms with zero functional disruption.

## 3. Determinism vs. Generation Matrix
| Module | Deterministic Engine | AI Augmentation |
| :--- | :--- | :--- |
| **PlanAI** | PostgreSQL schema, sequence ordering | Multi-day cultural itinerary structuring |
| **BudgetAI** | Python Decimal & SQL NUMERIC financial math | Category allocation recommendations |
| **TimelineAI** | DAG topological sort, cycle prevention | Pre-event preparation checklist suggestions |
| **VendorConnect** | Normalized line-item comparison tables | Unstructured quote extraction & notes |
| **Adaptive Planning** | Mathematical cross-module impact rules | Natural-language impact explanations |

## 4. Data Privacy Safeguards
We do not use customer wedding data or guest lists to train public foundation models. Only minimal context required for the specific request (e.g. event city, function list, guest count) is included in prompts.
