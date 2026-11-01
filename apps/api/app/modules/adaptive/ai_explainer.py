"""Advisory explanation and natural-language interpretation via Gemini."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.modules.adaptive.schemas import (
    ImpactResult,
    TypedChangeRequest,
)
from app.modules.ai.provider import StructuredGenerationProvider
from app.modules.events.context import SharedEventContext

logger = logging.getLogger(__name__)


def generate_fallback_explanation(
    context: SharedEventContext,
    request: TypedChangeRequest,
    impact: ImpactResult,
) -> str:
    lines: list[str] = [
        f"### Adaptive Planning Impact Summary (Severity: {impact.severity.upper()})",
        "",
        f"**Requested Change:** {request.request_text}",
        "",
    ]

    if impact.affected_modules:
        lines.append(f"**Affected Modules:** {', '.join(m.capitalize() for m in impact.affected_modules)}")
        lines.append("")

    if impact.warnings:
        lines.append("#### Key Considerations & Advisories:")
        for w in impact.warnings:
            lines.append(f"- **[{w.severity.upper()}] {w.code}**: {w.message}")
            lines.append(f"  *Recommended Action:* {w.recommended_action}")
        lines.append("")

    if impact.calculations:
        lines.append("#### Impact Calculations:")
        for c in impact.calculations:
            lines.append(f"- **{c.metric}:** {c.before_value} → {c.after_value} (Delta: {c.delta} {c.unit})")
        lines.append("")

    if impact.suggested_options:
        lines.append("#### Recommended Adjustments:")
        for opt in impact.suggested_options:
            lines.append(f"- **{opt.title}**: {opt.description}")
        lines.append("")

    lines.append(
        "> *Note: This proposal preserves full database integrity. "
        "Review the affected records and approve to apply mutations atomically.*"
    )
    return "\n".join(lines)


async def explain_impact(
    provider: StructuredGenerationProvider | None,
    context: SharedEventContext,
    request: TypedChangeRequest,
    impact: ImpactResult,
) -> str:
    if not provider:
        return generate_fallback_explanation(context, request, impact)

    system_instruction = (
        "You are the UtsavAI Adaptive Planning Advisor. You explain complex, cross-module impacts "
        "of celebration requirement changes (dates, guest count, budgets, functions) to wedding planners. "
        "Be clear, empathetic, practical, and structured. Explain why downstream items are affected and how "
        "the suggested options mitigate risks. Return your explanation in clean, concise markdown."
    )

    user_input = json.dumps(
        {
            "event_title": context.event.title,
            "current_guests": context.event.expected_guest_count,
            "current_dates": f"{context.event.start_at.isoformat()} to {context.event.end_at.isoformat()}",
            "requested_change_text": request.request_text,
            "event_changes": request.event_changes.model_dump(mode="json") if request.event_changes else None,
            "budget_changes": (
                request.budget_changes.model_dump(mode="json") if request.budget_changes else None
            ),
            "function_changes": [f.model_dump(mode="json") for f in request.function_changes],
            "severity": impact.severity,
            "affected_modules": impact.affected_modules,
            "warnings": [w.model_dump(mode="json") for w in impact.warnings],
            "calculations": [c.model_dump(mode="json") for c in impact.calculations],
            "suggested_options": [o.model_dump(mode="json") for o in impact.suggested_options],
        },
        indent=2,
    )

    try:
        res = await provider.generate(
            task_name="adaptive_plan_explanation",
            system_instruction=system_instruction,
            user_input=user_input,
            timeout_seconds=25.0,
        )
        if res.raw_text and len(res.raw_text.strip()) > 20:
            return res.raw_text.strip()
    except Exception as exc:
        logger.warning("Gemini explanation generation failed, using deterministic fallback: %s", exc)

    return generate_fallback_explanation(context, request, impact)


async def interpret_change_prompt(
    provider: StructuredGenerationProvider | None,
    context: SharedEventContext,
    prompt: str,
) -> tuple[str, dict[str, Any]]:
    default_summary = "Structured change request generated from user input."
    default_changes: dict[str, Any] = {
        "base_revision": context.event.revision,
        "request_text": prompt.strip(),
        "event_changes": None,
        "budget_changes": None,
        "function_changes": [],
    }

    if not provider:
        return default_summary, default_changes

    system_instruction = (
        "You are the UtsavAI Natural Language Change Interpreter. Parse the user's natural language change "
        "description for a celebration into structured JSON change fields.\n"
        "Return a JSON object with:\n"
        "- 'summary': a brief 1-2 sentence description of the interpreted changes\n"
        "- 'event_changes': object with optional guest count, dates, and location\n"
        "- 'budget_changes': object with optional 'total_limit'\n"
        "- 'function_changes': list of objects with 'action', 'name', 'function_type'\n"
        "Only extract fields explicitly or clearly implied by the prompt. Preserve null for untouched fields."
    )

    user_input = json.dumps(
        {
            "event_title": context.event.title,
            "start_at": context.event.start_at.isoformat(),
            "end_at": context.event.end_at.isoformat(),
            "expected_guest_count": context.event.expected_guest_count,
            "currency": context.event.currency,
            "user_prompt": prompt,
        }
    )

    try:
        res = await provider.generate(
            task_name="interpret_change_prompt",
            system_instruction=system_instruction,
            user_input=user_input,
            timeout_seconds=25.0,
        )
        data = res.parsed_json
        summary = data.get("summary") or default_summary
        candidate = {
            "base_revision": context.event.revision,
            "request_text": prompt.strip(),
            "event_changes": data.get("event_changes"),
            "budget_changes": data.get("budget_changes"),
            "function_changes": data.get("function_changes") or [],
        }
        return summary, candidate
    except Exception as exc:
        logger.warning("Gemini interpretation failed, returning default container: %s", exc)
        return default_summary, default_changes
