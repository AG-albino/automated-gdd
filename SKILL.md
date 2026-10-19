---
name: automated-gdd
description: "Automated game design document (GDD) for AI-assisted game development: linked JSON gameplay parameters, game-balance values, readable Markdown, and separate mechanic experiments. Use when adding an automated GDD, importing a game design, checking cross-system consequences, or maintaining a project using this workflow."
license: MIT
metadata:
  author: AG-albino
  version: "1.0.0"
---

# Automated GDD

Preserve the game's current intent while allowing deliberate changes and experiments. The user's explicit request authorizes changing the targeted old rule. Check consequences for **other affected systems**, rather than treating the old rule itself as an objection.

Use the user's language for conversation and project prose. The English instructions and Python helper are portable; do not require Codex-specific APIs, any engine, network access, or another skill. Python 3 is optional for the workflow, required for the bundled helper. Do not claim background monitoring: synchronization occurs during agent tasks or project checks that are actually configured.

## Choose the operation

- **First setup:** Read [onboarding.md](references/onboarding.md), then the data contract below. Ask the three setup questions in that order. Do not initialize this workflow just because the skill was mentioned in a discussion.
- **Existing automated GDD:** Read project `AGENTS.md`, `design/WORKFLOW.md`, and the relevant JSON records. Reuse the saved setup; do not repeat onboarding each session.
- **Discussion only:** Discuss and research without creating project files.

Default project layout (reuse an existing equivalent location and adapt links):

```text
AGENTS.md
design/game.json               # authoritative current design and numeric catalogue
design/GDD.md                  # deterministic readable view; not a second editable spec
design/WORKFLOW.md             # persistent rules for future agents
design/experiments/<id>.json    # hypotheses, trial rules/numbers, observations, decisions
design/tools/gdd.py            # portable checks, selective reading, rendering
```

Read [data-contract.md](references/data-contract.md) when creating/migrating data, changing numeric bindings, or recording experiments. Start from [game.template.json](assets/game.template.json); it intentionally contains no invented game facts. Create experiment records only when needed.

## Before a task

1. Interpret the requested result and distinguish implementation, experiment, discussion, and adoption of a trial. Reuse prior explicit decisions.
2. Read the relevant systems and parameters, their incoming/outgoing dependencies, and applicable active experiments. Inspect corresponding code/resources; neither docs nor code are automatically current.
3. Identify targeted rules the request replaces. Trace effects on **other systems** using the recorded graph AND implementation references. Missing graph edges are not proof of no effects; add discovered links.
4. Proceed with ordinary necessary work when scope and consequences are clear. Separate confirmed contradictions, plausible risks, and unknowns. Ask only for a material unresolved choice; offer concrete consequences and a recommended resolution. Do not ask permission again for the user's explicit change.

Example: adding jumping replaces a no-jump rule. Input and animation wiring are normal implementation work. A low fence that gates a mandatory puzzle creates a separate level-design decision; explain options such as changing the fence or accepting a shortcut. Do not invent such a conflict without inspecting the project.

A concise impact summary is useful for meaningful changes. Avoid mandatory reports or design interviews for every small fix, and read only relevant sections. Provide conclusions, not private reasoning transcripts.

## Numeric ownership and completion

- Register **all configurable game numbers**: health/damage, movement/physics, durations/distances, economy/progression/probabilities, camera and presentation tuning, counts/budgets, numeric tables/curves. Give stable IDs, units, provenance, and relevant dependencies. Expand the catalogue as the project is inspected; track incomplete coverage honestly.
- Prefer game code/resources consuming JSON values directly or generated engine resources. For existing projects, verified mirrors are acceptable. Inspect engine conventions before choosing; do not introduce a new runtime dependency or rewrite the game's architecture just to initialize documentation.
- Every changed game number must have a current JSON value AND corresponding game binding, or an explicitly reported unresolved binding. Values missing from the design are `null` with an open question, not made-up defaults. Trial values belong to the experiment JSON.
- During authorized implementation, ordinary tuning choices may use reasonable provisional values when the task delegates those details. Record their real source as an agent choice and `provisional: true`; do not attribute them to the user or require a questionnaire for every number. Import-time unknowns remain unknown until observed or deliberately chosen.
- Record formulas/curves and input IDs where values are derived. A textual formula is documentation, not an automatically evaluated expression; use the game's actual calculation or a tested project adapter to verify derived values. No `eval`.
- On each numeric task, update affected records and bound resources in the same unit of work, recompute affected derived values, run sufficient engine checks, and regenerate Markdown. Do not quietly copy the code back into the design to conceal an implementation mistake.
- Use the helper for registered JSON bindings. Other engine formats need a real engine read/project adapter and recorded evidence tied to the file hash. Structural validation cannot discover every numeric literal or certify game feel.
- Never report complete synchronization when values differ, changed numbers are unregistered, checks were skipped, or a required binding is unresolved. Report the specific remaining gap; do not stall unrelated work on old, documented gaps.

Configuration describes initial/max values and behavior. Live state such as a character's remaining HP belongs to runtime/save data. Generic loop counters, file-format versions, and incidental implementation literals need not become design parameters unless they affect the designed game.

## Experiments

“Try a heavier-feeling sword for one test arena” creates an experiment, not an accepted combat redesign. Keep the accepted rules/values intact; record scoped trial rules, overrides, base values/revision, hypothesis, affected systems, and observations separately. New trial mechanics may have their own experimental systems and parameters.

- An explicit selected experiment overrides only its listed targets for the current task/test context. Other accepted constraints still apply. Preserve visibility through scenes, flags, branches, or the least disruptive suitable mechanism; do not require a branch for every trial.
- Read active experiments before calling a deliberate trial a bug. Do not silently combine overlapping experiments or use the newest trial as a global default. Validate with its ID explicitly.
- Code existing, passing tests, merging a branch, or “it works” does not adopt a mechanic. A clear instruction to keep it in the game is sufficient authorization; no ritual confirmation phrase is required.
- On adoption, update canonical records, dependencies, implementation status and numeric bindings, record the user's decision source, then close the experiment. Adopting the idea and keeping prototype code are separate decisions.
- On rejection, retain a short observation/rationale, close the experiment, and remove/disable trial behavior only within the authorized task. Historical rejection is not a permanent ban on revisiting the idea.

## Optional GDD steward

Use the saved answer to setup question 2. Read [steward.md](references/steward.md) only when delegated maintenance is enabled or requested. All agents read records directly. One designated writer maintains canonical data; the main agent remains responsible for cross-system reasoning and final verification. If subagents are unavailable, disclose the fallback and perform the same work inline. Do not silently change the selected model or create another user-visible chat.

## Persistent project instructions

After setup answers, copy the helper to `design/tools/gdd.py`, copy the project workflow asset, and merge the managed block into root `AGENTS.md`. Preserve all unrelated content. Repeated setup updates one block and existing records; it does not reset decisions or spawn parallel GDDs. Inspect existing unmarked GDD instructions and reconcile them before installing another block.

For agents that use a different native instruction entrypoint, add a short reference to `AGENTS.md` and `design/WORKFLOW.md` in that existing entrypoint when supported. Preserve its current content; do not claim every tool auto-loads `AGENTS.md`. Keep essential operation rules in the project so the skill need not be reinstalled for every reader.

Run from any directory, using the actual script and project paths:

```text
python <skill>/scripts/gdd.py install-rules --root <project>
python <project>/design/tools/gdd.py show --root <project>
python <project>/design/tools/gdd.py show --root <project> --id player.health
python <project>/design/tools/gdd.py validate --root <project>
python <project>/design/tools/gdd.py validate --root <project> --experiment exp-heavy-sword
python <project>/design/tools/gdd.py render --root <project>
```

`validate` fails known structural/reference/binding mismatches and reports incomplete coverage and stale views as warnings. `--strict` makes readiness warnings fail too. `--schema-only` skips engine bindings and view freshness; never present it as game verification. `show --experiment` returns an explicit effective view without writing/adopting it. The helper never edits game resources, chooses mechanics, or auto-promotes trials.

After any completed change, report relevant behavior, GDD/parameter changes, meaningful verification, and unresolved limits briefly. Use the onboarding reference's ordinary-language examples to explain the workflow after first setup.
