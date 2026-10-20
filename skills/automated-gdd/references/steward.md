# Optional junior GDD steward

Enable only when setup answer 2 or a later explicit instruction selects it. Use a native subagent, not a new user-visible task/chat. All agents may read project records directly.

“Junior” describes a narrow maintenance responsibility, not an invented model capability. Use a user-selected model if available; otherwise use permitted inherited/default settings. Never silently override model preferences. If delegation is unavailable, explain once and maintain inline; record the actual writer for the session without discarding the preference.

## Responsibilities

The main agent interprets requests, inspects implementation, reasons about design consequences, selects checks, and owns the final result. The steward retrieves dependencies, maintains JSON/Markdown/decision records, checks bindings, and flags discrepancies. It does not approve new mechanics, infer adoption from tests, or rewrite accepted intent to match accidental code.

Use one designated writer for canonical GDD per unit of work. Workers send proposed record edits to that writer; do not concurrently edit the same JSON/view. A different session cannot be assumed to share a live steward: reread files/revision before writing. If concurrent changes are detected, reconcile scoped edits against the newest revision rather than overwriting the file wholesale.

## Handoff

Give the steward:

- Project root and allowed write paths (`design/game.json`, affected experiments, `GDD.md`; engine resources stay owned by the implementer unless explicitly delegated).
- The original user request, relevant prior decisions, selected experiment ID if any, current design revision, affected system/parameter IDs, and observed engine values.
- Proposed changes with their rationale and authorized decision source; the checks/evidence available, including binding paths and formats.
- A concrete return condition: records updated, view rendered, checks run, exact unresolved gaps returned. No external side effects.

Before implementation, use it for relevant record/dependency retrieval when helpful. For tiny changes, one post-implementation reconciliation is enough if the main agent already checked the design. For canonical numeric consumption, coordinate a single-writer parameter update before implementation uses it. Never leave a code/JSON mismatch hidden between handoffs.

Require a compact report: changed IDs and revision, validation command/results, actual vs recorded values, experiment state, and unresolved issues. The main agent inspects the resulting diff and verification evidence; an unsupported “all synced” reply is insufficient.

Do not call a task fully synchronized if the steward failed or never returned. Continue maintenance inline if permitted, otherwise report the exact unfinished part. Persistent memory lives in project files; do not rely on a long-running subagent or promise autonomous monitoring after the session ends.
