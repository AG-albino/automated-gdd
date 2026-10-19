# Automated GDD project workflow

<!-- automated-gdd:workflow:v1 -->

Read this with root `AGENTS.md`. The canonical design is `design/game.json`; `design/GDD.md` is its generated readable view. Experiments are separate JSON records in `design/experiments/`. All paths below are relative to the project root; adapt references together if the project uses another location.

## Before changes

Understand the user's requested result, then read relevant systems, parameters, dependencies in BOTH directions, active experiments, and matching implementation. An explicit request changes its targeted old rule. For example, adding a new movement ability authorizes replacing the old movement restriction; check effects on combat, levels, camera, and other affected systems. Ordinary implementation consequences are part of the work. Explain confirmed cross-system conflicts and ask only for unresolved material choices, with options. Label risks/unknowns instead of inventing conflicts.

## JSON contract

`schema_version: 1`, integer `revision` (increment for canonical edits); `project` contains game description/engine/phase; `workflow.steward` is `main` or `subagent`, and `numeric_mode` is `canonical` or `mirrored`.

`systems` is an array of records: `id`, `summary`, `status` (`accepted`, `proposed`, `unknown`), `rules` (array of records with `id`, `text`, `status`, `source`), and `depends_on` (system IDs). Optional fields include intent, acceptance checks and implementation evidence. System dependencies may be bidirectional.

`parameters` maps stable IDs to records with `system` (system ID), `value` (finite number or null), `unit`, `status`, `source`, `depends_on` (parameter IDs; acyclic), and `bindings` (array). Optional `relation` explains a formula using dependency IDs; verify it using actual engine calculation or a tested adapter, not Python eval. For curves/tables, give individual numeric entries stable indexed IDs, with relation/group metadata. Units include explicit dimensionless/count units. Unknown numbers remain null plus an open question. A new/proposed parameter is not automatically accepted just because it exists in code.

A binding identifies a project-relative `path`. For `format: "json"`, `pointer` is a JSON Pointer to the actual numeric field (escape `/` as `~1`, `~` as `~0`). For non-JSON resources use `format: "manual"` and `verification: {"value": <observed number>, "file_sha256": <hash of that file>, "evidence": <actual engine/adapter read and check>}`. Refresh evidence after changing that file. A matching hash proves evidence refers to this file content, not that the helper independently parsed its semantics. Unresolved bindings/coverage must be disclosed, never called full synchronization.

`open_questions` contains `{id, text, affects, blocking}` records. `decisions` contains `{id, summary, source, status}` records; status is `current` or `superseded` (optionally `superseded_by`). Keep obsolete history out of default working context. `coverage` records `status` (`partial` or `reviewed`), `reviewed_paths`, and `unregistered` numeric locations/notes. Reviewed coverage is a human/agent audit claim, not an automatic discovery guarantee.

## Numbers and completion

Catalogue every configurable game number, including tuning, formulas/curve entries and numeric presentation settings. Runtime HP, procedural sample positions, incidental indexes and file versions are state/implementation details, not design parameters. Prefer consuming values from JSON or generated resources. When mirrors are needed, change and verify both sides in the same task. Register newly found numbers and dependencies. Keep game configuration, live state, and intended design distinct.

During authorized implementation, choose ordinary provisional tuning when reasonably delegated by the task; record `provisional: true` and the real agent-choice source, with verified bindings. Do not fabricate user approval or ask a new question for every tuning number. During import, genuinely unknown values remain null until observed or deliberately chosen.

For task completion: canonical/trial values agree with all affected game bindings; affected calculations are checked; the readable view is regenerated; relevant game tests/run checks have actual evidence. Existing unrelated audit gaps need not block work, but the final report must name any affected gap. Do not change requirements just to justify incorrect code. Automated checks cannot prove all numbers were discovered or gameplay is fun.

## Experiments

An experiment file contains `id`, `base_revision`, `status` (`active`, `paused`, `evaluated`, `adopted`, `rejected`), `hypothesis`, `affects` (system IDs), `base_values` (original values for overridden canonical parameter IDs), `overrides` (trial numeric values), `systems` (new experimental systems), `new_parameters` (new parameter records), `trial_rules` (scoped prose), `observations` (evidence/feedback), and `decision: {outcome, source}`. Outcome is `undecided`, `adopt`, or `reject`. Closed records need a real decision source.

Only the explicitly selected active experiment changes the effective rules/values for its scope. Do not change canonical values merely because trial code runs or tests pass, and do not apply two overlapping trials without resolving them. Compare recorded base values with current canonical values before resuming a trial; reconcile changed baselines. A clear user instruction to keep the mechanic authorizes adoption: update canonical rules/parameters/dependencies, bindings and view, record the source, then close the experiment. Rejection closes it with a brief finding and authorized cleanup; it is not an eternal prohibition. Decide separately whether prototype code needs refinement.

For a separate test scene/resource, an optional `binding_overrides` object maps overridden canonical parameter IDs to nonempty arrays of trial bindings. The selected trial uses those bindings, preserving the canonical resource paths. Owners of every overridden/new parameter must be listed in `affects`. An unselected trial with a changed numeric baseline is a warning; selecting it for work/checking requires reconciliation. An unrelated canonical revision change alone does not invalidate it.

## Steward and persistence

All agents read directly. If `workflow.steward` is `subagent` and delegation is available, appoint a single writer to maintain records/views and verify bindings. The main agent owns task intent, cross-system consequences and final evidence; it inspects the steward's diff/results. Use the user's model preference only if available; otherwise disclose the fallback, never silently pick another model. If delegation is unavailable, maintain inline and mention it. Never rely on the steward's chat memory or promise a background watcher.

## Commands

Use Python 3 from the project root (or supply an absolute root):

```text
python design/tools/gdd.py show --root .
python design/tools/gdd.py show --root . --id <system-or-parameter-id>
python design/tools/gdd.py validate --root .
python design/tools/gdd.py validate --root . --experiment <active-id>
python design/tools/gdd.py render --root .
```

`show` defaults to a compact index, not the entire document. A system query includes parameters and incoming/outgoing system dependencies; an experiment selection returns a labelled effective view without adopting it. `validate` checks registered bindings and reports stale generated Markdown/partial coverage. `--strict` fails those readiness warnings too; `--schema-only` checks structure/references without bindings or view freshness and must not be reported as gameplay verification. It never executes relations, edits game files, or adopts experiments.

When writing JSON, preserve unrelated fields and explicit decisions, increment revision, and re-read before writing if others may have changed it. Match project language. Do not restart onboarding each session; the saved preference and records persist. Only run destructive cleanup, publishing, or unrelated configuration changes when separately authorized.
