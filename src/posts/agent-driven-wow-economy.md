---
tags:
 - post
 - published
 - ai-assisted
 - agent-driven-development
 - world-of-warcraft
title: "Building Azeroth, One Conversation at a Time"
description: "A few actual exchanges from building an autonomous World of Warcraft economy with coding agents: design pivots, tests that should test themselves, and finding the right amount of autonomy."
layout: mylayout.njk
author: Philipp
date: 2026-10-12
published: 2026-10-12
ai_assisted: true
---

> "instead of telling me, include it into the test"

That's one of the more useful things I've said to an AI coding agent recently.

It wasn't a clever prompt. It wasn't even particularly polite. We were testing a modification to my World of Warcraft server, an integration fixture had produced the rather anticlimactic output `kick requested%`, and the conversation was drifting toward one more thing for me to check manually.

I didn't want another instruction to paste into a terminal. I wanted the test to verify what actually happened.

That exchange is a better description of my experience with agent-driven development than the usual story about giving an AI a feature request and watching it write code. Most of the interesting work has happened in the back-and-forth: describing a slightly vague idea, discovering a constraint, pushing back on an answer, making the agent encode an assumption in a test, or figuring out which agent should work on which part next.

Here are some excerpts from those conversations while building [custom-wow](https://github.com/philsupertramp/custom-wow), my AzerothCore Wrath of the Lich King server. **My quoted messages are taken from the project chats; the agent's reasoning and actions are summarized rather than presented as fabricated verbatim replies.** GitHub links point to the corresponding implementation and tracking work. This is a field note from an ongoing project, not a claim that an autonomous economy is finished.

## 1. The conversation that changed the product

I initially asked what we would need to make better use of our Playerbots MCP integration. Should the MCP grow new functionality? Would the game backend need new hooks? Was the missing piece something else?

The answer I really cared about came out a little later:

> "my dream would be building an economy in which Agents collect and craft materials and items and sell them on the auctionhouse"

It's a pleasant thing to picture: a world that stays busy when you aren't logged in. An agent mines copper, crafts something useful, sells it, earns gold and makes its next decision. Not an auction house that merely spawns items, but characters whose activities cause items to appear.

We could have stopped at a list of API endpoints. Instead, the discussion wandered toward something I hadn't quite specified: **what would it feel like to watch one of those agents?**

> "having an observability aspect, like running a dungeon with `.playerbots bot self` and still watching the progress, would feel way more natural"

Then came the practical objection:

> "But logging in N clients on one or many machines would also be quite inefficient"

And then the idea that turned into an architectural requirement:

> "A hybrid would be cool. Like a way how we can log in an existing account without an active client, but then be able to log into this character to observe what the agent is doing"

That is a very different request from "make a gathering bot." It means an agent character needs a stable identity and a safe handoff between a headless session and an actual WoW client. It also means you have to care about login/logout callbacks, session ownership, state continuity, and what happens if the person logging in interrupts the agent.

After talking through alternatives, I handed over a compact set of decisions:

> "Use these architectural decisions for the autonomous Azeroth economy implementation plan:
> Character model: dedicated
> Observation: both
> Auction House strategy: hybrid
> Agent intelligence: hybrid
> Initial scope: one"

The agent translated that into an implementation plan and GitHub issues, starting with audits of Playerbots lifecycle and economic capabilities rather than immediately inventing a bot controller. The [lifecycle audit (ECO-001)](https://github.com/philsupertramp/custom-wow/issues/2) and [economy audit (ECO-002)](https://github.com/philsupertramp/custom-wow/issues/3) were consequences of that conversation.

What's interesting to me is that the specification emerged *during* the exchange. I didn't arrive with a perfectly formed product brief, and the agent didn't simply execute one. We were finding out what the product was.

## 2. "Sure, let's test it" has a price tag

When an agent audits a C++ game server, the next natural move is to add tests and compile something. Unfortunately, "compile something" isn't a small step in this repository.

During the Playerbots lifecycle audit, I pointed out the constraint:

> "we can add a testing CI to allow that, but a build takes usually around 35-40 minutes :/"

The discussion changed from *should we test?* to *which evidence is worth paying for, and when?*

> "github is perfectly fine for the runners, we can even chose the faster runtime and only build for it instead of the multi-arch build; if that speeds up the CI runtime"

> "Once we're certain about the plan, please create the tasks required"

The outcome was a separation that sounds obvious in retrospect: [CI-001](https://github.com/philsupertramp/custom-wow/issues/18) added fast checks for patches and related changes; [CI-002](https://github.com/philsupertramp/custom-wow/issues/19) tracked the expensive, opt-in native AMD64 integration build. Neither a patch applying cleanly nor a quick unit test should be mistaken for a compiled, functioning world server.

I like this exchange because the useful contribution wasn't a brilliant algorithm. The agent could propose a validation strategy, but I supplied the operational constraint that made the first strategy unrealistic. From there we could make the tradeoff explicit and record it.

This was a recurring pattern: the agent was willing to propose complete workflows. I kept asking what they would cost to run on *this* repository.

## 3. "Include it into the test"

Back to the `kick requested%` moment.

While validating the existing MCP patch against a disposable world server in [ECO-003](https://github.com/philsupertramp/custom-wow/issues/4), I was following a fixture and checking its output. At one point I ran a command inside the test container:

```sh
docker exec eco003-world sh -c '
  cat /fixture/control/result 2>/dev/null || true
'
```

The result was:

```text
kick requested%
```

That is evidence that a request was recorded. By itself, it doesn't tell us whether the subsequent game-state transition happened as intended.

And my response to the next round of manual verification advice was:

> "instead of telling me, include it into the test"

The useful boundary is simple: **if checking an outcome is part of deciding whether the work is done, the verification probably belongs in the fixture.**

Later I supplied the final checks file, merged the PR, and asked the agent to close the issue with a summary and conclusion:

> "I merged the PR, please close the issue with a summary and conclusion"

This is where an agent becomes more useful than a very patient search engine. I can ask for an explanation, but I can also insist that the explanation turn into a reproducible check, documentation, or a closed issue with evidence.

A manual command in chat is easy to forget. A test can fail for the next person.

## 4. How much independence is the right amount?

At first, I was treating each small step as a conversation of its own. The agent would do some work, report back, and ask what to do next. That's useful when a decision is risky; it is tiresome when the next step is merely another small, reversible change.

Eventually I said:

> "Continue, you don't need to stop between every single small step"

That's not the same as "do whatever you want." In another exchange I asked:

> "Is this still in the scope of your task?"

The two statements belong together. An agent should be able to carry a bounded assignment through several ordinary edits, tests and reviews without asking permission at every turn. It should also know when a new architectural detour, production operation, or expensive workflow is no longer obviously authorized by that assignment.

There were plenty of informal checkpoints:

> "The pr looks good so far"

> "looks like it failed again"

> "nice, that patch was successful. the apply check succeeded but the build will take forever"

Those aren't detailed specifications. They're the kind of high-bandwidth status messages you'd send to a collaborator who already has the issue, the diff, and the CI context open.

I still want a review point before something is merged, and I particularly want approval gates around production operations. But I don't want to micromanage every grep, test run, and Markdown edit.

The surprising part has been how much of agent-driven development is really a negotiation over **initiative**: enough to be useful, not enough to silently change the mission.

## 5. The best response to an agent isn't always agreement

Our build pipeline eventually became a whole thread of its own. This isn't the main story, but it produced some very recognizable conversations.

After a failed image-publishing attempt and another run heading in the same direction, I said:

> "the pod/node ran out of disk space before and it'll happen again with this current run - I'm 100% sure about that"

And when discussing possible fixes:

> "the history download will save probably the most, the quickest"

That steered the work toward an experiment in shallow pinned source fetches and reducing Docker build-layer waste, recorded in [PR #48](https://github.com/philsupertramp/custom-wow/pull/48).

I think this is an important distinction. The agent can read logs, search code, and propose plausible remedies. The human may have just watched a job consume tens of gigabytes of scratch space and recognize the pattern before another expensive run finishes.

Neither intuition nor a plausible patch is proof, of course. PR #48 explicitly treats the savings as hypotheses until a real build measures them. But the conversation helped choose which hypothesis to test.

The best interactions haven't been the ones where I said "sounds good." They've been the ones where I could say "that will fail again" or "why aren't we testing that automatically?" and get a concrete change in direction.

## 6. A conversation can hand work to another conversation

As the number of issues grew, we started treating separate agent sessions almost like developers assigned to different tickets.

One exchange captures it:

> "ok, because I'm currently waiting with you for #24 to finish so we can move on with #25, can you pass me some instructions for the next agent that can already do something that isn't related to the CI features?"

This was less about fancy multi-agent orchestration than about practical project management. The current thread knew the state of a blocked CI dependency. Rather than make everything wait, I wanted a useful, independent slice of work and a prompt that carried over the right context.

That pattern repeated: audit one part, open or review a PR, merge it, update the issue, then ask for a handoff prompt for whatever should happen next.

Eventually one of those milestones was the [dedicated character registry (ECO-005)](https://github.com/philsupertramp/custom-wow/issues/6), implemented in [PR #49](https://github.com/philsupertramp/custom-wow/pull/49). The registry records ownership and intended character state, with tests for leases, duplicate registrations and recovery. It does **not** yet solve the game-server session handoff that inspired the whole thing.

> "PR #49 looks good to me!"

That is a nice moment, not because everything is finished, but because a vague aspiration—"I want to be able to log into the character an agent was using"—has become a set of components with explicit boundaries and tracked follow-up work.

The GitHub issues preserve those boundaries between conversations. The handoff prompts preserve enough context to continue without re-explaining the entire project. And the actual test results keep both the human and the next agent from rewriting history as a series of uninterrupted successes.

## What I'm actually finding interesting

The repository is full of artifacts: code, manifests, docs, tests, issue comments, CI workflows. But the *process* is in sentences like these:

> "A hybrid would be cool."

> "Once we're certain about the plan, please create the tasks required."

> "instead of telling me, include it into the test"

> "Continue, you don't need to stop between every single small step"

> "Is this still in the scope of your task?"

Taken out of context they're mundane. In sequence they describe a working relationship: suggest, clarify, formalize, implement, challenge, verify, and hand over.

I don't think this proves that agent-driven development is faster or better in general. We have spent significant time debugging infrastructure, and several of the most interesting game-side features still need runtime validation. I also don't have reliable enough measurements to declare a productivity victory.

But the conversations have changed how I build a personal project. I can stay at the level of a half-formed idea long enough to explore it, then ask an agent to turn the decision into code and evidence, while reserving the right to say: no, that's not what I meant; this is outside scope; or please stop making me run that check manually.

I still want to watch an autonomous character mine copper, craft something and sell it on the auction house. For now, the most interesting thing to watch has been the development process itself.

---

*AI-writing disclosure: This article was drafted with an AI assistant using excerpts available from our ChatGPT project conversations and linked GitHub issues. Quoted user messages are reproduced from that context; agent replies have been summarized rather than reconstructed as fake direct quotes. The article is an editorial account, not a complete chat transcript. Expect slop; verify the technical claims.*
