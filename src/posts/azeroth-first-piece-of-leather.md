---
tags:
 - post
 - published
 - ai-assisted
 - agent-driven-development
 - world-of-warcraft
title: "Building Azeroth: The First Piece of Leather"
description: "Ecoscout gathered leather in a disposable WoW realm. Getting there involved stubborn builds, a red CI run that had succeeded, and unfinished session ownership."
layout: mylayout.njk
author: Philipp
date: 2026-10-15
published: 2026-10-15
ai_assisted: true
---

*Part 2 of our custom WoW server journey. [Start with the conversations that shaped the project]({{ "agent-driven-wow-economy" | postsUrl }}). This installment records the state on October 15, 2026.*

Ecoscout reached Skinning 6/75.

That's a fairly unimpressive achievement in World of Warcraft. For this project, it is the most interesting progress we've made so far.

In a disposable test realm, a dedicated character ran without an attached game client, moved, fought, progressed, and retained Light Leather and Ruined Leather Scraps. One of those legitimately gathered leather items subsequently appeared on the Stormwind Auction House.

**I listed that item manually through the game client.** Autonomous selling is still unfinished. The useful result is narrower: we have exercised a path from headless gameplay to a persistent item and then to an auction, with a human completing the last step.

The [ECO-016 field validation](https://github.com/philsupertramp/custom-wow/pull/29) records the seller, item and auction identifiers. There was an actual item to follow through the system. After several days of patches, builds and infrastructure failures, that feels like a good place to pick up the story.

## Giving the idea a character

The first post described the ambition: dedicated characters gathering, crafting and trading, with the option to log in and observe what they are doing. The scope starts with one character because even one character has an inconvenient number of ways to be half logged in.

We already had a [Python and SQLite registry](https://github.com/philsupertramp/custom-wow/pull/49) for character identity, ownership and intended state. That gives a controller somewhere to record who is supposed to control a character. It doesn't create a functioning session inside AzerothCore.

For that, the research work combined our pinned AzerothCore and Playerbots revisions with `mod-autonomous-altbots`, adapting the upstream module and patches to the versions we actually use. The distinction between patches applying and code working became very concrete.

The patch checks passed. The first combined native build then failed because the module called `PlayerbotAI::IsRealPlayer()`, which our pinned Playerbots API does not provide.

That failure arrived at compilation step 1194 of 2103, after roughly twenty minutes. The disk still had plenty of space. This time the problem was exactly where the compiler said it was: two calls to an unavailable API.

The correction used the pinned implementation's bot-AI lookup at those call sites. Another small patch, another validation pass, another expensive build. Pinning dependencies makes a failure reproducible; it doesn't make independently developed modules compatible by itself.

## The build succeeded. The workflow was red.

The next result was more irritating to interpret.

GitHub Actions lost authorization while polling the Kubernetes build job. The job itself kept running. The recovered Kubernetes logs showed a successful worldserver link and installation, including the autonomous module configuration. The recorded build duration was 5,329 seconds, roughly 89 minutes.

The Actions run was red because it could no longer observe the work it had started.

That matters when working with coding agents. A summary saying “the build failed” would have sent the next conversation looking for another C++ problem. The useful handoff had to preserve two separate facts: compilation succeeded, and the workflow's observation of that compilation failed.

The evidence is recorded in [PR #29](https://github.com/philsupertramp/custom-wow/pull/29), with the authentication follow-up tracked in [issue #64](https://github.com/philsupertramp/custom-wow/issues/64). We also [versioned the restricted credential-rotation procedure](https://github.com/philsupertramp/custom-wow/pull/67), so recovery wouldn't depend on finding a one-off script in a previous conversation.

I keep coming back to this aspect of the process. An agent needs enough initiative to investigate a failure, but its summary also becomes input for the next agent. Losing the distinction between a failed compiler and a failed status check can waste another whole iteration.

## Getting back into the world

Once the combined build was available, the disposable realm gave us something much more useful than another clean patch report.

The recorded checks covered headless login, persistence across restart, clean stop, a sequential handoff to the manual client, movement, combat and progression. MCP control was exercised through strategy changes and a simple `sit` action.

Then there was Ecoscout, with Skinning skill and leather in its inventory.

That is the part of the original idea I wanted to reach: resources entering the economy through a character's activity. There is still a long distance between this experiment and a character deciding what to gather, when to craft, and what price to ask. But we now have a concrete gameplay result to build on.

The manual auction was also useful precisely because it kept the experiment small. It established that one gathered item could survive the handoff and be listed by the same character. It did not establish automated pricing, automated listing, a completed sale, or an economy that runs unattended.

Those are separate things to test. Calling the whole loop finished would make the next task harder to specify.

## One successful handoff leaves a difficult question

The sequential client handoff worked in the disposable test. What happens if a stop request arrives while the character is still logging in?

The lifecycle investigation found that pending bot logins and active bots are tracked differently. A logout operation that removes an active bot doesn't necessarily cancel a database callback already waiting to finish a login. A delayed callback can outlive the moment at which the controller thought it had stopped the character.

For our planned economy, this isn't an obscure edge case. A person may want to take over a character. A controller may restart. A command may be repeated because its first response never arrived.

[PR #69](https://github.com/philsupertramp/custom-wow/pull/69) is the current work on that boundary. It adds per-attempt checks around pending login and queued registration, keeps pending ownership around until registration is resolved, and handles cancellation without immediately tearing down state from inside the callback.

As of this post, that PR remains a draft. Its process-local attempt tracking still needs integration with the persistent registry's ownership rules. Core-side admission must also prevent a human client and a headless controller from claiming the character concurrently. The remaining compile and runtime checks matter.

Meanwhile, [PR #65](https://github.com/philsupertramp/custom-wow/pull/65) has merged the packaging work for the normal native AMD64 release path, with the module disabled by default. Including a module in the build is useful progress. Enabling it on the live realm requires the lifecycle work to catch up.

## The infrastructure kept interrupting

There is no honest version of these few days that leaves out the build pipeline.

After the linker crash came a succession of artifact problems: inherited directory permission bits, an export volume filling with old archives, installed static libraries that didn't belong in a runtime package, and a manifest larger than the verifier allowed. Several failures arrived after compilation had already succeeded.

The [export-space fix](https://github.com/philsupertramp/custom-wow/pull/57) added bounded cleanup and capacity checks before compilation and before copying the actual archive. The [staging fix](https://github.com/philsupertramp/custom-wow/pull/58) removed build-only files from the temporary runtime copy. The [manifest fix](https://github.com/philsupertramp/custom-wow/pull/59) tested a realistically large inventory through packing and verification.

These were useful corrections, but experiencing them one expensive run at a time was frustrating. Each stage had assumptions that the earlier stage hadn't exercised with realistic output.

Even publishing an image exposed another boundary. The binaries had compiled-in paths under `/work`, while the runtime image placed their configuration and SQL elsewhere. [PR #60](https://github.com/philsupertramp/custom-wow/pull/60) restored those expected paths in the image. Separately, the AMD64-only MCP container landed on the Raspberry Pi's ARM64 node; [PR #61](https://github.com/philsupertramp/custom-wow/pull/61) made the architecture constraint explicit in Helm.

The recent workflow changes aim to reduce some of this overhead: [documentation-only edits skip functional and build jobs](https://github.com/philsupertramp/custom-wow/pull/66), and [manual image publication can request a missing matching native artifact](https://github.com/philsupertramp/custom-wow/pull/70). The latter is merged workflow code, with end-to-end dispatch validation still listed as follow-up. I don't have a measured speedup to report.

What I do have is a more demanding definition of a useful agent fix: reproduce the failure cheaply where possible, put the check near the operation that can fail, and leave enough evidence that the next session doesn't repeat the investigation.

## A small window into what the bots are doing

The latest addition under review is a deliberately small [Playerbots observatory](https://github.com/philsupertramp/custom-wow/pull/71): a server-rendered page in the existing Python MCP process, refreshing every five seconds, with a bot list and raw state, position and health diagnostics.

It is an early view into the server, with important gaps. The current bridge enumerates online bots from `RandomPlayerbotMgr`; dedicated headless gatherers may need further integration to appear reliably. There is no production history or resource-flow analysis yet. The endpoint also lacks authentication, so this first slice is intended for private access or a localhost port-forward.

That is still a useful direction. I want to see which character is online and what it is doing while we build out the controls. Eventually I want to follow an item from gathering through crafting and sale. A small inspection page gives us somewhere to start making that visible.

For now, the next difficult milestone is safe ownership through delayed logins, stops, restarts and client takeover. Once that holds up, we can give the character more responsibility.

Ecoscout has some leather. We still owe it a reliable way to clock out.

---

*AI-writing disclosure: This article was drafted with an AI assistant from the linked project PRs and recorded test results. It contains no reconstructed chat quotations. Disposable-realm results, merged implementation and open experiments are distinguished as of October 15, 2026; later project status may differ.*
