# Automated GDD

[![Checks](https://github.com/AG-albino/automated-gdd/actions/workflows/checks.yml/badge.svg)](https://github.com/AG-albino/automated-gdd/actions/workflows/checks.yml)
[![Download skill](https://img.shields.io/badge/Download-skill_ZIP-4bd9b4)](https://github.com/AG-albino/automated-gdd/releases/latest/download/automated-gdd.zip)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

```text
Use the skill at https://github.com/AG-albino/automated-gdd to set up an automated game design document (GDD) in my project.
```

[![Follow @Albino_design on X](https://img.shields.io/badge/Follow_on_X-111111?style=for-the-badge&logo=x&logoColor=white)](https://x.com/Albino_design)

![Automated GDD — Automated Game Design Document: check connected systems, keep numbers in sync, and experiment separately](https://github.com/AG-albino/automated-gdd/releases/download/v1.0.1/banner.png)

A game development skill for AI coding agents. Keep your **game design document, gameplay numbers, and mechanic experiments** connected as you build.

A GDD records how your game should work. Automated GDD gives your agent a structured JSON version, a readable Markdown version, and rules for keeping them current. It uses the [Agent Skills format](https://agentskills.io/specification) for Codex, Claude Code, Gemini CLI, and other compatible agents. Loading and subagent support depend on the client.

## Start here

**With an agent:** copy the prompt at the top into the chat for your game project. Your agent needs access to this repository and your project files.

**Download:** [Get the ready-to-use skill ZIP](https://github.com/AG-albino/automated-gdd/releases/latest/download/automated-gdd.zip). Extract the `automated-gdd` folder into your agent's skills directory, or give the folder to your agent.

**Install with the Skills CLI:**

```sh
npx skills add AG-albino/automated-gdd --skill automated-gdd
```

The CLI lets you choose an agent. Its installer requires Node.js; the skill itself doesn't. Reading the instructions needs no runtime. The included checks use **Python 3.9+** and its standard library, with no pip packages.

The installable skill lives in [`skills/automated-gdd/`](skills/automated-gdd). Both the ready-to-use ZIP and the Skills CLI install only that folder's contents. Tests, release tools, repository documentation, and banner images stay out of your installation. If you download the repository source ZIP, use its `skills/automated-gdd` folder.

If your agent can't fetch a GitHub link, download the ZIP and ask it to read the extracted `SKILL.md`. It needs the accompanying files too.

## Setup takes three questions

Your agent announces three questions and asks them **one at a time**:

1. Do you have an existing game design document?
2. Should the main agent maintain it, or a separate junior subagent?
3. What is the game? Describe the idea, genre, setting, visual style, camera perspective, and what already exists.

Answer in your own words. Already supplied answers are reused. You can start with a single mechanic; unknown details stay open instead of being filled with invented features.

The agent then creates the records, adds a short rule to your project's `AGENTS.md`, and explains how to continue. All agents can read the design. If you choose a subagent and your client supports it, one designated writer maintains it; the main agent still checks the result.

## What happens when you ask for a change?

The agent understands the request, reads the affected design and implementation, and checks related systems before editing.

| Your request | What the agent does |
|---|---|
| “Add a jump to the player.” | Replaces the old no-jump rule and checks effects on levels, combat, camera, and other linked systems. |
| “Enemies should survive two sword hits.” | Checks health and damage together, implements the intended behavior, and updates the relevant numbers. |
| “Make the sword slower in the test arena so I can compare it.” | Records a scoped experiment. The main combat design keeps its existing values. |
| “The slower sword feels better. Use it in the main game.” | Adopts that trial, updates affected rules and parameters, and checks its consequences. |

An old rule you explicitly ask to change isn't a reason to refuse. A conflict with another system may need a decision. For example, a jump could bypass a low fence that gates a required puzzle. The agent should explain that specific effect and offer options, such as changing the fence or accepting the shortcut.

## Keep numbers together

Health, damage, movement speed, cooldowns, prices, rewards, probabilities, camera tuning, and other configurable game numbers belong in the JSON catalogue, with units and links to their game settings.

For example, changing maximum health from **100 to 80** should update both the game setting and the GDD record. If healing depends on maximum health, that relationship should be checked too.

The preferred setup lets the game read the JSON values or use resources generated from them. Existing projects can keep their engine settings and verify matching copies. The helper compares registered JSON fields automatically. Other resource formats need an engine check or a project adapter.

## Try mechanics without committing to them

Suppose the accepted dash distance is **4 metres**. You ask to try **8 metres in a test arena**.

- The main GDD keeps 4 metres.
- An experiment records the 8-metre override and its test-scene binding.
- Your next agent can see which version is being tested.
- Passing tests doesn't adopt it. A clear decision to keep it does.

If you drop the experiment, its short findings remain available. You can revisit it later. Keeping a mechanic and deciding whether its prototype code needs cleanup are separate choices.

## Files in your game project

```text
AGENTS.md                     Short instructions for future agents
design/
  game.json                   Current design and linked numeric parameters
  GDD.md                      Readable view generated from game.json
  WORKFLOW.md                 How agents maintain the records
  experiments/<id>.json       Trial rules, numbers, observations, and decisions
  tools/gdd.py                Checks, selective reading, and Markdown generation
```

Edit design facts through the agent or `game.json`, then regenerate the view. `GDD.md` is generated; writing competing rules in both files would create ambiguity.

## Checks your agent can run

These commands are available **after setup**, from your game project's root:

```sh
# Check recorded values against their registered game bindings
python design/tools/gdd.py validate --root .

# Check a selected experiment against its trial bindings
python design/tools/gdd.py validate --root . --experiment exp-heavy-sword

# Regenerate the readable design document
python design/tools/gdd.py render --root .
```

Replace `exp-heavy-sword` with an actual experiment ID. You can keep making requests in ordinary language; you don't need to run these commands yourself.

## Scope and limits

The workflow is engine-independent. It doesn't include ready-made Godot, Unity, or Unreal loaders. The agent must inspect the engine and connect the actual settings. A prototype can begin with partial coverage, which must be reported clearly.

Checks cover **registered values and bindings**. They don't prove every number was discovered, execute documented formulas, or judge whether a mechanic feels good. Engine runs and playtesting still matter. Maintenance happens during agent tasks or checks you configure; there is no background watcher.

For implementation details, see the [skill instructions](skills/automated-gdd/SKILL.md), [JSON data contract](skills/automated-gdd/references/data-contract.md), and [optional steward workflow](skills/automated-gdd/references/steward.md). For a short file map, see [llms.txt](llms.txt).

## Contribute

Report a concrete mismatch or confusing interaction in [Issues](https://github.com/AG-albino/automated-gdd/issues). Include the request, relevant records, expected behavior, and observed result. Remove private project data first.

Run the helper tests before submitting changes:

```sh
python tests/test_gdd.py
```

Licensed under [MIT](LICENSE).
