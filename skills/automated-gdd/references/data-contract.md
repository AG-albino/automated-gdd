# JSON data contract (schema version 1)

The starter asset is an intentionally empty valid structure. Build records from actual answers/inspection, never from the example values below. Preserve extra task-specific fields; the helper renders them too. Write UTF-8 JSON with unique keys and finite numeric values. Increment `revision` for canonical edits. Use stable lowercase dot/hyphen/underscore IDs and project-relative binding paths.

## Ownership

`design/game.json` owns current accepted/proposed design, all configurable numbers, questions and current decisions. `GDD.md` is a deterministic view, never a second independent source. If the user edits Markdown, reconcile that edit into JSON before rendering; do not erase their unsaved design changes. Old chat transcripts and obsolete decisions do not belong in the default context. Archive substantial superseded history when useful.

The root fields are `schema_version`, `revision`, `project`, `workflow`, `systems`, `parameters`, `open_questions`, `decisions`, `coverage`. `workflow.steward` is `main` or `subagent`; `preferred_model` is optional/null unless selected; `numeric_mode` is `canonical` (consumed/generated) or `mirrored` (verified engine copies).

## Systems and rules

Each system: `id`, `summary`, `status` (`accepted`, `proposed`, `unknown`), `rules` and `depends_on` (other system IDs). Bidirectional system relationships are allowed. Optional `intent`, `acceptance`, and `implementation: {status, evidence}` separate accepted decisions from implemented/tested reality. A rule: `{id, text, status, source}`. A real explicit user request is a source; cite the decision faithfully without inventing message IDs or approval.

Record behavior and meaningful constraints, not a duplicate of every method. Before a task, inspect incoming/outgoing dependencies AND relevant implementation references. Missing edges do not establish independence.

## Numeric catalogue

`parameters` is an object keyed by stable IDs. Example:

```json
{
  "player.max-health": {
    "system": "player",
    "value": 100,
    "unit": "hp",
    "status": "accepted",
    "source": "Explicit user choice during design",
    "rationale": "Baseline survivability",
    "depends_on": [],
    "bindings": [
      {"path": "data/player.json", "format": "json", "pointer": "/max_health"}
    ]
  }
}
```

Include gameplay and numeric presentation tuning. Numbers in tables/curves get separate stable indexed IDs and optional group/index/interpolation metadata; the game adapter reconstructs its native structure. Record units (including count/dimensionless), status, source, rationale when useful, owning system, dependencies and all affected bindings. Status concerns design authority; use separate implementation evidence for what actually runs.

For an authorized mechanic, ordinary tuning choices delegated to the implementer may be current accepted configuration with `provisional: true` and a truthful agent-choice source. Their numbers still need binding checks. This does not authorize inventing new mechanics or claiming that the user explicitly selected those values. Unobserved import-time values remain null; do not populate them with genre defaults.

`value: null` represents unknown, accompanied by an open question. Do not fill unknowns from a generic genre template. Code observations can be recorded as observations/proposed values; they do not silently override a supplied GDD. `relation` documents calculations and relevant dependency IDs. Parameter calculation dependencies must be acyclic; the helper checks the graph but **does not execute formulas or prove their outputs**. Verify derived numbers through engine logic or a tested project adapter whenever their inputs change. Qualitative relationships belong in system rules instead of creating formula cycles.

Every configurable number changed in a task must be registered. Track inspected paths and unregistered values in `coverage`; `reviewed` is a claim about the stated scope, not proof that a scanner found all numbers. The helper compares only registered bindings. Runtime state, indices and implementation literals with no designed effect do not become GDD configuration.

### Engine bindings

- **Canonical consumption/generated resources:** The game's loader or build adapter reads `game.json` and materializes native resources. Document/test that integration in the project; the bundled helper does not install a universal loader. A binding can point to generated JSON fields; verify native non-JSON resources through an adapter.
- **JSON mirrors:** `{path, format: "json", pointer}` addresses a real numeric JSON field. RFC 6901 escaping: `~1` means `/`, `~0` means `~`; arrays use numeric indices. The helper compares exact numeric values (booleans are not numbers).
- **Non-JSON formats:** Use an actual engine read/adapter, then record `{path, format: "manual", verification: {value, file_sha256, evidence}}`. The digest is SHA-256 of the entire bound file. Update it only after a real value read at that file version. The helper compares value/digest and warns it has not independently parsed the engine format; strict validation does not certify manual evidence.
- Empty bindings are an explicit pending integration gap. Report it. A strict check fails unresolved values/bindings and other readiness warnings. Do not replace real bindings with an empty list to suppress a mismatch.

## Experiments

Each `design/experiments/<id>.json` is a separate record; `<id>` equals its `id`. Required fields:

```json
{
  "id": "exp-health",
  "base_revision": 1,
  "status": "active",
  "hypothesis": "Lower health makes a short test encounter more tense",
  "affects": ["player"],
  "base_values": {"player.max-health": 100},
  "overrides": {"player.max-health": 80},
  "systems": [],
  "new_parameters": {},
  "trial_rules": ["Apply only to the test arena"],
  "observations": [],
  "decision": {"outcome": "undecided", "source": null}
}
```

States: `active`, `paused`, `evaluated`, `adopted`, `rejected`. Closed states require a matching `adopt`/`reject` outcome and a real decision source. Existing numeric overrides require matching canonical `base_values`; a changed baseline needs reconciliation, while an unrelated new design revision does not automatically invalidate a trial. `base_revision` must reference an existing revision.

New trial mechanics use experimental `systems` and `new_parameters` with the same record shapes. IDs must not collide with current canonical records. Trial rules can document nonnumeric behavior overrides; `affects` gives their system scope. Accepted rules outside that scope still apply. The helper cannot verify prose rules or scene/flag isolation.

Selecting `--experiment <id>` applies ONE active overlay for reading/checking without mutating canonical data. Accepted bindings are checked against trial values in that context. Point new experimental parameters at actual trial assets. If an override runs only in a separate scene/resource, give the experiment an optional `binding_overrides` map from existing parameter ID to its trial binding array; the canonical binding is then preserved. Do not falsify canonical bindings to make trial checks pass.

An active baseline conflict is surfaced before reuse; reconcile values/rationale, pause, or close the trial as appropriate. Overlapping active trials require explicit selection and implementation isolation. On adoption, merge only authorized rules/values into canonical records, update bindings, dependencies and actual implementation, record the source, close the trial, render and verify. No automatic promotion because tests passed. Preserve useful findings without feeding all archived experiments into every task.

## Questions, decisions, coverage

- Question: `{id, text, affects: [IDs], blocking: boolean}`. Ask when current work depends on the answer; do not turn unresolved future content into a setup interview.
- Decision: `{id, summary, source, status: "current" | "superseded", superseded_by?: ID}`. A direct change supersedes the targeted prior rule. Archive stale history out of default views when it grows.
- Coverage: `{status: "partial" | "reviewed", reviewed_paths: [...], unregistered: [...]}`. List scoped locations/notes and do not claim complete synchronization beyond verified coverage.

## Validation sequence

Use `show --id` to retrieve relevant records. After editing, run relevant engine/game checks, `render`, then `validate` (with the selected experiment if applicable). `--strict` additionally fails readiness warnings; ordinary validation can pass while explicitly reporting unrelated coverage gaps. `--schema-only` validates structure/references without engine binding or view checks. For manual bindings, report the actual engine/adapter check and the helper's narrower digest check separately.

The command utility never edits engine resources, copies observed values into design, chooses between conflicting intentions, evaluates formulas, or adopts experiments. These actions need the agent's task context and actual verification.
