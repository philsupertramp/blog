---
tags:
 - post
 - published
 - ai-assisted
 - agent-driven-development
 - world-of-warcraft
title: "I Wanted Autonomous WoW Bots. I Got a Second Job in CI."
description: "What happened when I handed an AzerothCore economy experiment to coding agents and became the person reviewing PRs, debugging CI, and asking whether any of it actually works."
layout: mylayout.njk
author: Philipp
date: 2026-10-12
published: 2026-10-12
ai_assisted: true
---

I had a reasonably simple idea: make a World of Warcraft server feel alive even when nobody is playing.

Not by spawning more NPCs, but by giving agents actual characters. They would gather herbs, mine ore, craft items, list them on the auction house and, ideally, start behaving like participants in an economy rather than background scenery.

Obviously, the sensible way to approach this was to give a bunch of coding agents a repository and see what happened.

The result so far is not a finished autonomous Azeroth economy. It's a collection of architectural decisions, patches, tests, GitHub issues, pull requests, and a surprisingly intimate relationship with Kubernetes and CI. Which is, in its own way, a decent introduction to agent-driven development.

## The idea was bigger than a chatbot with a sword

The project is built on [AzerothCore](https://www.azerothcore.org/) for Wrath of the Lich King, with [Playerbots](https://github.com/mod-playerbots/mod-playerbots) and a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) adapter in [my custom-wow repository](https://github.com/philsupertramp/custom-wow).

The MCP bridge lets an AI client inspect online random-managed bots, and on a patched server ask them to execute actions or change strategies. That's useful, but it is not yet the same as managing an autonomous character with a persistent identity, profession, inventory, and economic goals.

For the economy experiment, we settled on a few constraints:

- **Dedicated characters**, not disposable random bots.
- **Hybrid intelligence**: use conventional bot logic for routine game mechanics, with a higher-level agent making economic decisions.
- **A hybrid auction house**, where simulated market activity can coexist with agent-owned listings.
- **Two ways to observe**: telemetry without a game client, plus the ability to take over a character in a normal client when we want to see what it is doing.
- **A deliberately tiny initial scope**. Make one economic loop work before attempting an entire world.

That last point matters. "Make the bots build an economy" sounds like one feature until you have to specify exactly who owns a character session, how a player can log into the same character safely, and what happens when the bot disconnects halfway through a task.

## The agents are productive. So is the issue tracker.

What changed most was the rhythm of development.

Instead of keeping the entire implementation in my head, I started creating sharply scoped GitHub issues, handing them to agents, reviewing their discoveries, and using pull requests as checkpoints. An agent could audit Playerbots lifecycle behavior while another investigated the auction house integration, and we could lay out the next tasks before attempting the risky runtime work.

The distinction between **investigated**, **implemented**, **compiled**, and **proved in a live server** became important very quickly. Agents are exceptionally good at producing plausible-looking work. That does not mean the work has survived the environment it is supposed to run in.

For example, [ECO-016](https://github.com/philsupertramp/custom-wow/issues/23) is about establishing whether an autonomous-altbots module can safely coexist with our pinned AzerothCore and Playerbots revisions. The compatibility and client-takeover questions are still research and validation work, not a feature I can honestly call finished.

A detailed issue is not bureaucracy here. It is a way to keep the next agent from confidently mistaking a proposed architecture for a tested implementation.

## Then CI became the actual game

At some point we ran into a fairly traditional problem: AzerothCore takes a long time to compile.

Our reported full builds were running at **90 minutes or more**. A comparison with upstream suggested roughly **55 minutes** there, but the hardware, build configuration, and module set are different, so that is a motivation to investigate rather than a fair benchmark. That investigation lives in [issue #31](https://github.com/philsupertramp/custom-wow/issues/31).

The first instinct was to optimize compilation and caching. Reasonable. Then came the runner bill and available GitHub Actions minutes. Then on-demand Kubernetes runners. Then the realization that an ephemeral runner does not magically solve Docker Buildx or persistent compiler-cache storage. Then the separate problem of publishing container images.

By [issue #40](https://github.com/philsupertramp/custom-wow/issues/40), the work had shifted toward running trusted AMD64 image publishing on our own Kubernetes infrastructure, with isolation, credentials, build cache and admission policy all needing attention.

One publishing attempt got the MCP image out, but the server build hit an **80 GiB BuildKit scratch-volume limit** after roughly 100 minutes. The follow-up [PR #48](https://github.com/philsupertramp/custom-wow/pull/48) explores shallow fetches of pinned revisions and smaller build layers. Those changes still need measurement; saving download history does not automatically guarantee a successful compile or a smaller peak disk footprint.

I wanted bots to sell copper ore. I am now reading about BuildKit snapshotters.

## The interesting part is the feedback loop

There's a temptation to judge coding agents by how quickly they create a diff. That's the wrong metric for this kind of work.

A diff is cheap. Knowing whether it safely patches a pinned C++ codebase, respects the game server's session lifecycle, survives the CI environment, and can be rolled back is expensive.

Some things that have helped:

1. **Give agents bounded ownership.** One audit, one integration seam, or one CI failure mode at a time. Define what counts as evidence.
2. **Treat status words literally.** An architecture proposal isn't a working feature. A static check isn't a full build. A successful image push isn't proof that the world server behaves correctly.
3. **Put expensive work behind deliberate gates.** A speculative PR should not silently start a two-hour compilation or publish a production image.
4. **Keep the human in the loop where consequences accumulate.** Reviewing a diff is one thing. Deciding which secrets, runtime privileges, production workloads, or persistent characters to expose is another.
5. **Optimize for getting useful feedback sooner.** Faster builds, better logs, disposable test environments, and predictable artifacts improve the agents' effectiveness more than another paragraph of clever prompting.

I spend less time typing implementation code than I would have expected. I spend more time asking, "How do we know this works?" and, occasionally, "Why is this pod still here?"

That's not necessarily a failure of agent-driven development. It is a change in where the work goes.

## A world I still want to watch

The original goal hasn't changed.

I want to see a character decide to gather something, travel into the world, produce an item, list it on the auction house, and change course when market conditions change. And I want to be able to log into that character to watch the adventure without making the agent's state explode.

We aren't there yet. The compatibility spike, character lifecycle, safe client handoff, economic planning, and runtime observability still need actual implementation and validation. The [project repository](https://github.com/philsupertramp/custom-wow) is the more reliable place to see which parts have crossed that line.

But I have already learned something useful: delegating code does not delegate responsibility. It changes a solo coding project into a small, slightly chaotic engineering organization in which every contributor happens to be an AI.

And apparently I am the CI department.

---

*Writing note: This post was drafted with an AI assistant from project discussions and linked GitHub work. The narrative, priorities, and factual claims still deserve human review before publication. Expect slop.*
