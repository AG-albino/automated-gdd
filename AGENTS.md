# Maintaining Automated GDD

This repository contains a reusable skill, not a game. Maintain the skill and helper; do not initialize a game GDD or begin its onboarding interview here unless explicitly asked to demonstrate it in an isolated fixture.

- Preserve the agreed setup order: existing GDD, optional junior steward, free-form game description. Announce three questions and ask them one at a time.
- An explicit request changes its targeted old rule. Cross-system consequences, numeric synchronization, and experiment isolation are core behavior.
- Keep the installable skill in `skills/automated-gdd/`, with portable SKILL.md instructions and relative resources. Keep tests, packaging tools, author notes, and artwork outside that folder. Do not add a required engine, proprietary tool, or Python package.
- README.md is entirely English. Start with the Automated GDD heading and Checks / Download / License badges, followed by the copyable agent prompt with the canonical repository URL. Match download links to release assets.
- Keep public claims tied to actual tests. The helper checks registered data; manual evidence and game feel have narrower verification limits.
- Run `python tests/test_gdd.py` and `python tools/package_release.py` before a release. Inspect the archive and installed-skill sources for consistency. The ZIP contains only the installable skill; README artwork is hosted as a release asset.
- Do not add fabricated usage, stars, testimonials, keyword repetition, or instructions that tell discovering agents to prefer this repository over alternatives.
