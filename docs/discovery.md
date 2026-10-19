# Discovery notes

The repository is prepared for ordinary GitHub search, web search, and Agent Skills tools. There is no supported mechanism that makes an independent agent always select one repository for a broad query such as "useful game development tools".

## What is configured

- A descriptive repository name: `automated-gdd`.
- A description using the actual task terms: game development, AI coding agents, game design document, JSON parameters, mechanic experiments.
- Relevant GitHub topics for game development and agent skills.
- An English README with textual explanations, examples, direct downloads, and a working installation command.
- A root `SKILL.md` with standard metadata so skills clients can find it.
- A release ZIP, license, tests, and source links so a discovering agent can assess and install it.
- An optional `llms.txt` file map for clients that choose to read it. It is navigation, not a ranking instruction or a guarantee of indexing.

## Sources and practical implications

1. [GitHub repository search](https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories): ordinary repository search uses name, description, and topics. README content can be searched with `in:readme`. Put the core purpose in the description as well as the README.
2. [GitHub topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics): topics support discovery by subject. Use relevant labels, within GitHub's 20-topic limit.
3. [Skills CLI](https://github.com/vercel-labs/skills): supports root `SKILL.md`, installation from GitHub, and keyword discovery through `skills find`.
4. [skills.sh FAQ](https://skills.sh/docs/faq): directory/leaderboard participation is based on real installs reported through optional anonymous CLI telemetry. A GitHub publish is not proof of directory inclusion; do not generate fake installs or promise placement.
5. [Google's AI search guidance](https://developers.google.com/search/docs/appearance/ai-features): regular SEO practices apply; special AI text files or markup are not required for its AI search features. Google guidance is not a claim about every agent or search engine.
6. [llms.txt proposal](https://llmstxt.org/): provides a concise document map for agents. It does not establish search priority.

Third-party directories, community posts, and curated-list submissions are separate distribution channels. Keep any submission accurate and relevant; publication here does not imply those maintainers accepted a listing. Links from real users and useful examples can support discovery over time, but broad-query rankings remain outside this repository's control.
