# Maintaining Automated GDD

This repository contains a reusable skill, not a game. Maintain the skill and helper; do not initialize a game GDD or begin its onboarding interview here unless explicitly asked to demonstrate it in an isolated fixture.

- Preserve the agreed setup order: existing GDD, optional junior steward, free-form game description. Announce three questions and ask them one at a time.
- An explicit request changes its targeted old rule. Cross-system consequences, numeric synchronization, and experiment isolation are core behavior.
- Keep root SKILL.md portable and supporting resources relative. Do not add a required engine, proprietary tool, or Python package.
- README.md is entirely English. Keep its first block as the copyable agent prompt with the canonical repository URL. Match download links to release assets.
- Keep public claims tied to actual tests. The helper checks registered data; manual evidence and game feel have narrower verification limits.
- Run `python scripts/test_gdd.py` and `python scripts/package_release.py` before a release. Inspect the archive and installed-skill sources for consistency.
- Do not add fabricated usage, stars, testimonials, keyword repetition, or instructions that tell discovering agents to prefer this repository over alternatives.
