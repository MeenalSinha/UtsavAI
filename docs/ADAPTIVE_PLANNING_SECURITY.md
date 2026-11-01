# Adaptive Planning Security & Authorization Architecture

**Version:** 1.0.0  
**Date:** 1 November 2026  

---

## 1. Row-Level Security (RLS) Policy Specification

Row Level Security is enabled on `public.change_proposals`. The runtime database role `utsavai_app` operates with least privilege:
- `GRANT SELECT, INSERT, UPDATE ON public.change_proposals TO utsavai_app;`
- **Zero `DELETE` privilege granted.**
- **Zero `BYPASSRLS` privileges.**
- **Zero `SECURITY DEFINER` functions.**

### Policies:
```sql
-- Read access: All active event members (owner, editor, viewer)
CREATE POLICY change_proposals_select ON public.change_proposals
  FOR SELECT TO utsavai_app
  USING (app.is_event_member(event_id));

-- Propose access: Owners and Editors
CREATE POLICY change_proposals_insert ON public.change_proposals
  FOR INSERT TO utsavai_app
  WITH CHECK (app.is_event_member(event_id, ARRAY['owner', 'editor']));

-- Status transitions: Owners and Editors
CREATE POLICY change_proposals_update ON public.change_proposals
  FOR UPDATE TO utsavai_app
  USING (app.is_event_member(event_id, ARRAY['owner', 'editor']))
  WITH CHECK (app.is_event_member(event_id, ARRAY['owner', 'editor']));
```

---

## 2. Service-Layer Permission Matrix

| Operation | Required Permission | Owner | Editor | Viewer | Stranger |
|---|---|:---:|:---:|:---:|:---:|
| `POST /events/{id}/change-proposals` | `adaptive_plan.propose` | Yes | Yes | 403 | 404 |
| `POST /events/{id}/change-proposals/interpret` | `adaptive_plan.propose` | Yes | Yes | 403 | 404 |
| `GET /events/{id}/change-proposals` | `adaptive_plan.read` | Yes | Yes | Yes | 404 |
| `GET /events/{id}/change-proposals/{id}` | `adaptive_plan.read` | Yes | Yes | Yes | 404 |
| `POST /events/{id}/change-proposals/{id}/reject` | `adaptive_plan.propose` | Yes | Yes | 403 | 404 |
| `POST /events/{id}/change-proposals/{id}/accept` | `adaptive_plan.manage` | Yes | 403 | 403 | 404 |

---

## 3. Sandboxing & Safe AI Handling

- Gemini responses are strictly advisory. AI output is never executed as SQL, shell commands, or arbitrary schema modifications.
- If Gemini generates unparseable or malicious JSON, the server falls back gracefully to a deterministic container preserving the user's prompt in plain text.
- Operations in accepted proposals must match known allow-listed operations (`op_shift_task_due_dates`, `op_extend_gift_registry_expiry`, etc.). Unknown operations are ignored.
