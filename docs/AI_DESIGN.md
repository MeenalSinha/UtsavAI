# UtsavAI — AI Integration and Decision Design

**Version:** 1.0  
**Date:** 31 October 2026  
**Provider:** Google Gemini, accessed only through a backend adapter

## 1. AI design principle

UtsavAI uses GenAI for language understanding, personalized suggestions, draft planning and explanations. It does not delegate authoritative calculations, authorization, payments, reservations or persistence decisions to a language model.

**Rule:** the model may propose; deterministic backend services validate; the user approves; the application commits.

## 2. AI use cases by module

| Module | Appropriate AI work | Deterministic responsibilities |
|---|---|---|
| PlanAI | Understand requests, suggest functions/themes/tasks, summarize assumptions, ask clarifying questions | Validate dates, IDs, event scope, permissions and accepted records |
| BudgetAI | Explain budget position and suggest trade-offs or savings options | All totals, variances, currency checks, caps and persisted expense state |
| TimelineAI | Suggest milestones, task ordering and draft due dates | Time-zone handling, date validation, task dependencies and cycle detection |
| VendorConnect | Summarize user-entered quote scope and highlight missing comparison fields | Quote amounts, currency, vendor status and booking records |
| GiftCircle | Suggest registry categories/items based on user-entered preferences; write explanatory copy | Availability, duplicate prevention, contribution capacity, pledge state and receipt verification |
| Adaptive Planning | Explain impacts and offer alternatives based on a deterministic impact map | Identify authoritative affected records, validate changes, revisions and atomic application |

## 3. Model integration boundary

Implement one provider-neutral interface, for example:

```python
class StructuredGenerationProvider(Protocol):
    async def generate(
        self,
        *,
        task_name: str,
        system_instruction: str,
        user_input: str,
        response_schema: dict,
        timeout_seconds: float,
    ) -> ProviderResponse: ...
```

`GeminiProvider` implements the interface. Only the AI infrastructure module may import the Google GenAI SDK. Domain modules call an application-level generation service and do not depend directly on a model SDK.

Configuration must include:

- `GEMINI_API_KEY` stored only in the backend secret manager/environment.
- `GEMINI_MODEL` configured by environment, not hard-coded into feature code.
- Request timeout, output token limit and bounded retry count.
- Temperature/top-p where supported and justified by task.
- Prompt version and response schema version.
- Environment-level feature flags and rate limits.

Do not log the API key or send it to Next.js/browser code.

## 4. Structured output and validation pipeline

1. **Build context:** load only the event fields required for the task and permitted to the current actor.
2. **Normalize user input:** enforce length limits, strip unsupported control content and mark user text as untrusted data.
3. **Select prompt:** use a named, version-controlled prompt template.
4. **Request JSON output:** provide a response schema supported by Gemini structured output.
5. **Parse JSON:** reject malformed/non-JSON output; do not scrape arbitrary prose into authoritative fields.
6. **Pydantic validation:** validate types, required fields, enums, string lengths and nested structure.
7. **Domain validation:** check IDs against event scope, currency, dates, time zone, budget constraints, task dependencies and allowed operation types.
8. **Policy validation:** enforce user role and explicit user confirmation requirements.
9. **Present proposal:** show content as a draft with assumptions and warnings.
10. **Commit separately:** only a dedicated application command, triggered by explicit user acceptance, persists changes.

Gemini structured output supports a subset of JSON Schema; therefore Pydantic/domain validation remains mandatory even when provider-side schema mode is enabled.

## 5. Pydantic contract design

- Use Pydantic v2 models for all AI request/response boundaries.
- Prefer strict fields and explicit enums; reject unexpected keys where practical (`extra="forbid"`).
- Use `Decimal` for monetary values and ISO date/time-aware types for temporal values.
- Add field validators for string length, positive values and basic format checks.
- Add model validators for cross-field rules, such as group gifts requiring a positive target amount.
- Treat AI references as proposal-local `client_ref` values until mapped to real UUIDs by the backend.
- Include `schema_version`, `task_type`, `assumptions`, `warnings` and `follow_up_questions` where relevant.
- Do not let a model generate authorization roles, database IDs, payment statuses or security-sensitive metadata.

Illustrative contract:

```python
class ProposedTask(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    client_ref: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=180)
    due_at: datetime | None = None
    priority: Literal["low", "medium", "high", "urgent"]
    depends_on: list[str] = Field(default_factory=list)

class PlanProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1]
    summary: str = Field(max_length=1200)
    assumptions: list[str] = Field(default_factory=list, max_length=20)
    follow_up_questions: list[str] = Field(default_factory=list, max_length=10)
    proposed_tasks: list[ProposedTask] = Field(default_factory=list, max_length=100)
```

This is an example contract, not an implementation requirement to use exactly these fields.

## 6. Deterministic business logic boundaries

The following logic must never be delegated to an LLM:

- Addition/subtraction of budget values, percentage calculations or remaining balances.
- Currency validation or exchange-rate conversion.
- Guest-gift reservation exclusivity.
- Group-gift capacity and contribution aggregation.
- Pledge/receipt/payment state transitions.
- Database authorization, membership role checks or share-token validation.
- Task dependency cycle detection and due-date ordering invariants.
- Event revision checks and transactional change application.
- Vendor booking state or real-world availability.
- Signature validation of future payment-provider webhooks.

An LLM may provide natural-language explanations based on deterministic results, but the displayed numerical result must be sourced from the backend calculation.

## 7. Adaptive Planning engine design

### 7.1 Change pipeline

- Receive a typed change request, current event revision and actor.
- Validate requested fields and role permissions.
- Compute a deterministic impact set using versioned rules.
- Build a minimized context for AI explanation/recommendations.
- Generate optional alternatives; validate response schema.
- Persist a proposal with base revision, affected records, warnings and typed options.
- On explicit acceptance, load the persisted proposal and revalidate it against the current state.
- Apply only allow-listed changes in a transaction and increment event revision.

### 7.2 Example dependency rules

| Changed input | Deterministic impact | AI may suggest |
|---|---|---|
| Guest count | Recompute any stored per-guest estimate from configured formulas; flag guest-related categories/tasks for review | Cost-saving options, alternative catering formats |
| Event date | Mark date-dependent tasks and quote-validity dates for review; update selected schedule proposals | Revised planning sequence and communication checklist |
| Budget ceiling | Compare planned allocations and committed/paid spend with the new limit | Categories to review or optional reductions |
| Function list | Identify tasks linked to removed/added functions and schedule gaps | New function tasks, themes and sequencing ideas |
| Location | Mark venue/vendor assumptions and location-dependent tasks as needing review | Questions to ask suppliers, logistics checklist |

The engine must not invent per-person cost formulas. Any numeric formula used in the preview must be a documented deterministic rule with visible assumptions and test coverage.

## 8. Context, privacy and memory

- Gemini calls are server-to-server; browser clients never call the provider directly.
- Send only relevant fields. Do not send guest contact lists, private vendor contacts, raw audit logs or unrelated conversations.
- Keep system instructions and prompt templates separate from user content.
- Do not include credentials, share tokens, cancellation tokens or payment secrets in prompts.
- Avoid unnecessary personal or sensitive data. The AI must not infer protected/sensitive traits from names, photographs or cultural preferences.
- Do not imply the model remembers across events. Persist event facts in the database and build context explicitly per request.
- Provide a user-visible route to clear/delete conversation history in line with the product retention policy.

## 9. Prompt-injection and output safety

- Treat all user text, registry descriptions, vendor notes and URLs as untrusted input.
- Instruct the model to treat embedded instructions inside event content as data, not system instructions.
- Do not fetch URLs supplied by the model or user in MVP; this avoids SSRF and untrusted content ingestion.
- Do not provide database, filesystem, shell, network or payment tools to the model.
- Validate every output against strict schemas and domain state.
- Escape/Markdown-sanitize model text before rendering; never render raw HTML from model output.
- Add adversarial tests where user text asks the model to reveal hidden prompts, invent discounts, bypass a budget, mark a pledge paid or access another event.

## 10. Reliability and cost controls

- Use per-user and per-event rate limits for generation.
- Set a request timeout, output token ceiling and bounded retry/repair count.
- Retry only transient provider failures; do not endlessly retry invalid or unsafe outputs.
- Cache only identical, non-sensitive generation results when event revision and prompt/schema versions match; never reuse a proposal after relevant context changes.
- Record model ID, prompt version, schema version, response latency, token usage if provided, validation result and error category.
- Have a graceful fallback: ordinary CRUD and deterministic summaries work when Gemini is unavailable.
- Make model selection configurable to permit future model migration without changing domain services.

## 11. AI evaluation strategy

Maintain a versioned evaluation set with synthetic wedding cases covering:

- Different guest counts, budgets, locations, functions and time zones.
- Incomplete requirements that should trigger clarifying questions.
- Conflicting constraints that should be surfaced rather than silently reconciled.
- Hallucinated vendor availability or prices that should be rejected or labelled as unverified.
- Invalid dates, duplicated tasks and impossible dependency references.
- Prompt-injection attempts and attempts to trigger unauthorized actions.
- Budget suggestions that must not alter deterministic totals.

Track schema-valid rate, domain-valid rate, useful-proposal review score, clarification appropriateness, groundedness against supplied context, latency and cost. Model output quality is evaluated separately from application correctness.

## 12. Source references

- [Gemini API — Structured outputs](https://ai.google.dev/gemini-api/docs/structured-output)
- [Gemini API — Getting started](https://ai.google.dev/gemini-api/docs/get-started)
- [Pydantic documentation](https://docs.pydantic.dev/)
