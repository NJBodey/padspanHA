# PadSpan — Phase 2 Strategic Review (2026-09-19)

Garry: "It has gotten big and complex, I'm ok with that, but I need
confirmation that I am on the right path, and where the gaps are. Do a
ton of research and build a phase 2 plan for me to review. Really dig
for this one, even outside HA if you need for ideas."

This document is being written incrementally and committed as it fills
in — treat an unfinished section below as "not started yet," not as a
finding.

**Companion doc:** [PROJECT_SYNOPSIS.md](PROJECT_SYNOPSIS.md) is the
day-1 (2026-02-04) founding vision. Section 1 below measures the
7.5-month delta between that and what's actually shipped — the most
direct answer to "am I on the right path."

---

## Status

`[IN PROGRESS — multiple research angles running/committing in parallel;
see the per-section notes below for which angles are in]`

1. Where this project actually stands today — `[DONE]`
2. Are you on the right path? (direct verdict) — `[PENDING — written last, after all angles below]`
3. External research findings — `[IN PROGRESS: 3.1-3.3 alarm/alert angle done; 3.4 analytics-depth angle done; 3.5 monetization/pricing angle done; other angles may still land]`
4. Gaps — `[IN PROGRESS: 4.1 alarm/alert done; 4.2 analytics depth done; 4.3 monetization/pricing done]`
5. Phase 2 plan — `[IN PROGRESS: 5.1 alarm engine done; 5.2 analytics depth done; 5.3 monetization/pricing done]`

**On the research method below, for calibration:** built from live web
search, direct page fetches, and — for long-standing, stable facts about
named products (GPL terms, WordPress's freemium norm, Fowler's
refactoring catalog) — existing knowledge, since live search on those
would only reconfirm something unlikely to have changed. This session's
live web search ran out of its per-session call budget partway through
(a hard cap, not a topic search coming up empty); a couple of sub-
questions below are marked **unverified live** and reasoned from direct
fetches plus general knowledge instead. Flagged as such rather than
presented as confirmed, per this repo's own rule not to assert without
checking.

---

## 1. Where This Project Actually Stands Today

### Scale (measured 2026-09-19)
- **7.5 months old** (first commit 2026-02-04) — 1,667 commits total.
- **~37,300 lines of Python**, **~63,200 lines of JS** across 76 backend
  files and 44 frontend view files. The frontend outweighs the backend
  more than 3:2 — worth noting when reasoning about where complexity
  actually lives (see Gaps).
- **2,008 automated tests** across 154 test files, all currently green.
- **24 releases in the last 14 days** (~1.7/day). This is not a typo —
  it is the real, sustained cadence of this project right now.
- **4 licence variants** live: PadSpan HA (free), PadSpan Pro ($45/yr),
  PadSpan Bright (free), PadSpan Bright Pro ($35/yr, $12 upgrade path
  from Bright to Pro) — two separately-listed HACS repos generated from
  one source tree.

### What day-1 set out to build, vs. what exists now
PROJECT_SYNOPSIS.md (2026-02-04) describes a **BLE room-presence
assistant** — the 4-pane map model (Physical / Radio / Distortion /
Combined), guided calibration, "no MAC-address workflows." That core is
still exactly there and is arguably the most mature, most tested part
of the codebase (positioning, Kalman smoothing, k-NN calibration,
floor-transition learning).

What's been ADDED since, that day-1 never scoped:
- **Atlas** — a full device/lighting map (lights, fans, locks, motion,
  temperature, humidity, air-quality, flood/leak sensors), each placed
  at a real position/shape/size, independent of BLE presence entirely.
- **Automorph + Showcase** — decorative rendering layers for Atlas.
- **Flood alarm latching** — an event-driven, life-safety-adjacent
  alerting subsystem (2-day latch, ISA-18.2-informed reset semantics),
  shipped in the last 24 hours of this session.
- **Locate** — room-graph wayfinding ("which way do I walk to find
  this"), derived from the presence fabric, not from BLE at all in its
  reasoning — it's a navigation feature riding on top of a tracking
  product.
- **Insights / Busy Times** — historical analytics (dwell time, peak
  occupancy, aggregate room-activity heatmaps).
- **PadSpan Bright** — a whole second *product*, not a feature: the
  same codebase with BLE presence stripped out, sold as a standalone
  lighting-map tool.
- Forensics (opt-in presence-session recording), RSSI capture sessions,
  an Install Base admin dashboard, a training/help system with 16
  animated walkthroughs plus a full manual — none of these existed in
  the original scope either.

**The honest read:** this is no longer "a BLE presence integration."
It's a general-purpose *building visualization and control platform*
for Home Assistant, with BLE presence as its most-developed subsystem
and increasingly independent as a value proposition. That's not
necessarily wrong — see Section 2 — but it is a real, measurable shift
from the founding document, and the rest of this report treats that
shift as the central question, not a side note.

### A concrete structural finding (not speculation — counted directly)
Today's flood-sensor feature (one new device class: motion, temp,
humidity, air-quality, lock, door already existed) required edits
across:
- `light_codes.js` (classifier function, border colour, code-series
  letter, shape entry, health-check carve-out)
- `lights_map.js` (domain admission filter, 2 border-colour chains, 2
  state-label branches, hide-untouched exemption, onRowMore exclusion,
  aggregate counts × 2, LIGHT_CLASSES chip)
- `iso_lights.js` (lightClassOf, border chain, 7 separate "which
  lights actually cast light/aura/pool" exclusion chains, the render
  effect itself)
- `maps.js` (the inspector panel's Turn On/Off exclusion — a SEPARATE
  copy of the same exclusion list `lights_map.js` already has one of)
- `const.py` / a Python backend module, twice over across this
  session's own two attempts

That's **~25 distinct edit sites across 4 files** for one device class.
The backend/frontend split for the flood *alarm* feature specifically
(as opposed to just drawing the sensor) needed a 5th file
(`flood_latch.py`) and a settings-schema change in a 6th
(`ws_settings.py`) plus a 7th test file. This pattern is not unique to
flood — the same "N files, each with its own copy of the exclusion
list" shape governs every device class Atlas has (motion, temp,
humidity, air, door, lock, flood). See Gaps §4 for what this actually
costs going forward, not just today.

---

## 2. Are You On The Right Path?

**Short answer: yes, on the fundamentals — with one specific, correctable
architecture debt that is exactly at the age where the research below says it
either gets fixed cheaply or gets expensive.**

The literature on AI-paired high-velocity development (§3) converges on a
single variable that decides whether a fast solo/small-team project stays
sound or hits a wall: **whether shipping speed is backed by a control
system that catches what the human's eyes no longer catch on their own** —
Google's 2025 DORA report states this almost exactly: *AI adoption has a
positive relationship with delivery throughput, but a negative relationship
with delivery **stability**, and the difference between teams that get both
and teams that get only the first is the strength of their automated
testing, version control discipline, and fast feedback loops.* PadSpan
already has the single most load-bearing piece of that control system: 2,008
automated tests, CI-enforced on every push and PR across two Python
versions (`.github/workflows/pytest.yml`), covering a test suite (40,641
lines) that is larger than the Python source it tests (37,300 lines). That
ratio is unusual in a good way — most of the "vibe coding debt" literature
describes projects where tests are thin, decorative, or skipped under
velocity pressure. PadSpan's aren't; they're the majority of the repo by
line count and they stay green.

The project also already does two of the other things the research
identifies as separating 6-month-plus sustainers from wall-hitters (§3E):
written architecture documentation the agent (and the human) can re-read
instead of re-deriving from scratch (`docs/00_REPO_LOGIC_OVERVIEW.md`
through `09_HARD_WON_RULES.md`), and — this is the finding that most
directly answers "am I on the right path" — **evidence of a completed,
closed-loop self-audit.** `docs/AUTOMORPH_CRITIQUE.md` is a genuine
four-lens design review that found 27 real defects, 24 of which were
applied, followed by an independent adversarial re-review that found 16
*more* defects in the applied fixes themselves, all of which were also
fixed, reproduction-first. That is, verbatim, the practice Simon Willison
names as the top defense against architecture drift — periodically stepping
back and asking a fresh pass to find what the forward-only building missed
— and it is the single strongest piece of evidence in this repo that the
project is being run with the right instincts, not just at high speed. (An
earlier note in this session's memory described this critique as
"unapplied" — that was wrong; reading the actual file shows 24 of 27 landed
and the other 3 are deliberately deferred behind stated gates, not
abandoned. Corrected here per the rule to verify before asserting.)

**The caveat.** Today's own flood-sensor session produced a textbook,
freshly-counted instance of the failure mode §3C and §3F below call
"agentic entropy" / Shotgun Surgery: one new device class required edits
across ~25 sites in 4 separate frontend files, each maintaining its own
copy of a device-class exclusion list. This is not a one-off — it is the
*shape* every device class in Atlas has taken (motion, temp, humidity, air,
door, lock, flood, each hand-threaded through the same four files
separately), and `maps.js` (11,075 lines) and `iso_lights.js` (6,116 lines)
are now large enough that no single read of either file gives an agent (or
Garry) the whole picture in one pass — which is precisely the condition
under which the research says agents produce code that is locally correct
and globally wrong. The "90-Day Reckoning" pattern in §3B describes almost
this exact trajectory: duplicated logic implemented three or four times
independently, each instance individually reasonable, until a routine
feature starts costing multiples of what it used to. PadSpan is not past
that line yet — today's session counted the cost precisely instead of
discovering it via a production bug, which is itself a good sign — but the
device-class pattern is the one structural element in this codebase that
is compounding rather than plateauing, and it should be the first thing
Phase 2 fixes rather than the tenth.

**Where I'd push back on the premise.** The framing "24 releases in 14 days
— is that sustainable?" treats release *cadence* as the risk variable. The
research doesn't support that framing on its own: nothing in §3 ties release
frequency itself to instability; what it ties to instability is the ratio of
**untested, unreviewed surface** to changes shipped. A project releasing
1.7x/day behind 2,008 green tests and a CI gate is categorically different
from a project releasing 1.7x/day on "if it's under 200 lines and the tests
pass, just merge it" (the unofficial rule one engineer described to
researchers in §3B) — because in PadSpan's case the tests are not
decorative. The cadence is not the finding. The scattered device-class
logic is. Don't slow down the release rate to fix this; fix the specific
architectural debt, because the release rate isn't what's carrying the
risk.

One open question this report can't answer from the repo alone, and that
the research (§3D) says matters as much as any structural fix: **is every
diff still being read, or has trust shifted to "tests green → ship"?**
Review-fatigue research is explicit that this shift is gradual and usually
invisible to the person it's happening to. This isn't a finding — there's
no way to verify it from outside the review process — but given the pace,
it's worth Garry answering for himself, honestly, before it becomes a
finding in a future retro.

---

## 3. External Research Findings

Organized by theme; each item says explicitly whether it confirms or
challenges PadSpan's current trajectory and why.

### A. High solo/small-team velocity is real, documented, and not inherently a red flag
- A solo developer built a 385,000-line multi-tenant SaaS platform (245k
  app code, 140k tests) in three months using Cursor/Claude Code, following
  a structured methodology of pre-coding domain modeling, staged
  build/audit windows, and **fresh AI review passes that re-examine
  finished work without having written it** — deliberately re-creating a
  second set of eyes. ([dev.to](https://dev.to/alex-zaporozhan/385000-lines-of-code-in-three-months-solo-with-ai-agents-is-that-a-good-result-id-like-to-1m4g))
- Armin Ronacher (Flask's creator) published widely-discussed "Agentic
  Coding Recommendations": write the simplest code the agent can
  understand, prefer explicit/typed code over clever abstraction, and
  maintain an AI-conventions doc the agent reads every session — almost
  exactly what PadSpan's `docs/00-09` series already is.
  ([HN discussion](https://news.ycombinator.com/item?id=44255608))
- Industry productivity claims cluster around 8-12x on routine work,
  2-3x on novel work, for teams doing "level-3 agentic pairing."
  ([digitalapplied.com](https://www.digitalapplied.com/blog/case-study-ai-coding-rollout-100-dev-team-quarterly-data-2026))

**Read on PadSpan:** the raw pace (1667 commits / 7.5 months, 24
releases/14 days) is high but not unprecedented or, by itself, alarming
for 2026-era AI-paired solo development. This **confirms** the cadence
itself isn't the risk variable — consistent with the pushback in §2.

### B. The "vibe coding" technical-debt literature — timelines and numbers
- GitClear's longitudinal analysis (150M lines, 2020-2026) found an
  **8x increase in duplicated code blocks** and code duplication rising
  from 8.3% to 12.3% of shipped code as AI-tool adoption grew.
  ([HackerNoon](https://hackernoon.com/vibe-coding-is-a-technical-debt-factory), [Autonoma](https://getautonoma.com/blog/vibe-coding-technical-debt))
- A widely-cited "90-Day Reckoning" model: Day 30, duplicated logic and
  inconsistent error handling start showing up as debugging sessions that
  run long; Day 60, a feature that should take 2 days takes 2 weeks
  because e.g. "checkout logic spreads across seven files with
  inconsistent state" — **this is structurally the same shape as today's
  flood-sensor finding, one class further along**; Day 90, teams are
  spending 20-30% of sprint capacity tracing bugs back to the original
  rushed implementation, and rewrite-vs-remediate becomes unavoidable.
  ([Autonoma](https://getautonoma.com/blog/vibe-coding-technical-debt))
- Google's 2025 DORA report: 90% of respondents use AI at work, 80%+
  report a productivity increase, but AI adoption has a **measured
  negative relationship with delivery stability** — the report frames
  this as acceleration exposing weaknesses downstream in teams that lack
  automated testing, version control discipline, and fast feedback loops.
  ([Google Cloud](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report))

**Read on PadSpan:** this **challenges** the device-class pattern
specifically (it is inside the Day-30-to-60 window the model describes)
but **confirms** that PadSpan's heavy automated-test investment is the
correct hedge against the DORA-identified stability risk — it's the
variable the report says actually matters, and PadSpan has it on the
Python side. It does not yet have it on the JS side (§4.1).

### C. Why this happens mechanically: "agentic entropy" and architecture drift
- An arXiv paper on "agentic entropy" defines it as disorder that
  accumulates specifically because agents optimize for local, per-file
  correctness while lacking visibility into system-wide invariants —
  producing code that is "locally reasonable and globally arbitrary."
  Its proposed mitigation, "Process-Oriented Explainability," amounts to
  constraining agents to route changes through existing modules rather
  than letting each change quietly re-implement its own copy of shared
  logic. ([arXiv 2604.16323](https://arxiv.org/pdf/2604.16323))
- Anthropic's own engineering guidance on context engineering recommends
  structured persistent memory (a NOTES.md-equivalent), sub-agents with
  clean context windows for deep work, and explicit file organization as
  the signal agents use to infer "where this kind of logic belongs."
  ([Anthropic](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents))
- A Hacker News thread from a solo developer running a 223k-line codebase
  with four differently-roled AI "team members" (research, architect,
  programmer, reviewer) reported the same mechanism in their own words:
  *"The AI would write clean functions that were globally wrong, quietly
  breaking earlier design decisions and long-range invariants"* — solved,
  in their case, by never letting the implementation-tier agent touch
  architecture decisions, and keeping a dedicated architect role that
  writes interfaces only. ([HN item 46462910](https://news.ycombinator.com/item?id=46462910))

**Read on PadSpan:** this set of sources **confirms**, mechanistically,
exactly why the flood-sensor edit landed in 4 separate files instead of
one: there is no single place in the codebase that declares "here is the
list of device classes and what each one means" for an agent (or a human)
to route a new class through. The fix implied by all three sources is the
same one classical refactoring literature has a name for (§3F).

### D. Review fatigue at high AI-driven velocity
- Practitioner-discourse research on code review after AI adoption
  documents a real, gradual shift: *"everything starts looking correct...
  developers stop asking second-order questions about null inputs or
  concurrency... they trust the pattern."* One account puts AI-driven code
  review time up **91%** even as raw output accelerates (Google's 2025
  DORA data, cited alongside GitClear's numbers).
  ([Augment Code](https://www.augmentcode.com/blog/generating-tech-debt-at-the-speed-of-light), [StackOverflow blog](https://stackoverflow.blog/2026/05/21/coding-agents-are-giving-everyone-decision-fatigue/))
- The Stack Overflow piece documents a concrete team case: one engineer
  produced roughly 7x the code of teammates with AI assistance, and *"the
  other six people on the team were spending the majority of their time
  reviewing her code [rather] than writing code"* — i.e. velocity doesn't
  remove review load, it relocates it, and at solo scale there is no one
  to relocate it to.
- The recommended discipline, repeated across sources: *"if you didn't
  read the diff, you don't approve."* AI-generated PR summaries are for
  triage, not for substituting the read.

**Read on PadSpan:** this **doesn't confirm or challenge** anything
measurable from outside — there's no way to observe from the repo whether
every diff at 1.7 releases/day is genuinely being read start to finish or
whether trust has shifted to "tests green → ship." It's flagged in §2 as
the one open question worth Garry answering honestly for himself, because
every source above says this specific erosion is invisible to the person
experiencing it until a bug exposes it.

### E. What separates 6-month-plus sustainers from people who hit a wall
Synthesizing across sources (Ronacher's recommendations, Willison's
patterns, the 385k-LOC case study, and the HN four-agent-team thread), the
practices that recur among people who've sustained high AI-paired velocity
for 6+ months, versus people who describe hitting a wall around 2-3 months,
are consistently:

1. **A written, agent-readable conventions/architecture doc**, kept
   current, that the agent reads before working rather than re-deriving
   design intent from the diff history.
2. **Tests as the primary gate, not manual review as the primary gate** —
   tests catch "does it work," a human catches "should it exist here,"
   and the two are treated as separate jobs rather than one.
3. **A scheduled, recurring "fresh pass"** — a walkthrough, critique, or
   adversarial re-review done by a context that didn't write the original
   code — done on a cadence, not only reactively after something breaks.
4. **Role/phase separation even when solo**: planning/architecture
   decisions kept separate from implementation execution, so the
   implementation agent is constrained rather than free to also decide
   structure.
5. **Written records of *why*, not just *what*** — design-decision docs
   survive past the commit that made them, so a later change doesn't
   silently contradict an earlier invariant nobody remembers setting.
6. **A named, deliberate point where net-new feature work pauses for a
   remediation pass**, before the debt crosses the point (§3B's Day 60-90)
   where routine work starts taking multiples of its old cost.

**Read on PadSpan:** items 1, 2, and 3 already exist here in real, working
form (the numbered docs series, the 2,008-test CI gate, and the
Automorph critique plus its adversarial re-review). Item 5 exists partially
— `docs/` is unusually rich with dated design-decision records
(`fabric-independence-plan-2026-08-10.md`,
`identity-and-geometry-invariants-2026-08-19.md`, etc.) for a solo project.
Items 4 and 6 are the two genuinely missing pieces: there's no evidence of
a standing architecture-only pass gating new device classes before they're
implemented, and no evidence of a scheduled (as opposed to one-off)
remediation cadence. Both are addressed directly in §5.

### F. The specific, named fix for the specific, counted problem
The flood-sensor finding — one logical change (add a device class)
forcing edits across many files that each hold their own copy of the same
classification logic — has a name in the refactoring literature:
**Shotgun Surgery**, one of the original Fowler/Beck code smells: *"a
single change is made to multiple classes simultaneously... many small
changes across numerous classes."* ([refactoring.guru](https://refactoring.guru/smells/shotgun-surgery))
The canonical fix family is **Replace Conditional with Polymorphism** /
consolidating the scattered per-type branches into one place each type's
behavior is declared once — in a codebase built around a small number of
crosscutting attributes (color, shape, code letter, aggregability, "does
it cast light") rather than inheritance hierarchies, this takes the
concrete shape of a **single device-class registry**: one data table, in
one place, that every consumer (light_codes.js, lights_map.js,
iso_lights.js, maps.js, the Python backend) reads from instead of
maintaining its own list. This is not a novel idea invented for this
report — it is the oldest, most mechanical fix in the refactoring canon
for exactly this smell, and it maps directly onto the concrete files
named in §1.

PadSpan already has a working precedent for "one generator, no second
source to drift" thinking elsewhere in the repo: `scripts/bright_build.py`
derives PadSpan Bright from the PadSpan HA tree at release time by
substitution over a copy, explicitly built so there is "no second source
to forget," with `verify()` grepping the output and `test_bright_build.py`
holding the guarantee in CI. That is the right instinct, already proven
out once in this codebase — it just hasn't been applied yet to the
device-class lists, which are a smaller, purely in-process version of the
same "don't let two copies exist" problem.

### G. Is PadSpan at risk of being obsoleted by Home Assistant's own direction?

This is the angle the original request centered on by name: where HA
core, its architecture repo/RFCs, its public roadmap, and Matter are
officially headed on Areas/Floors, native floor-plan/map visualization,
and device presence — plus a deliberate look outside HA entirely, to
check whether the underlying pattern (signal-based trilateration →
floor-plan visualization → alerting) is solved or commoditized
somewhere else. Every claim below was checked directly (fetched or
searched 2026-09-18), not recalled from training knowledge.

**HA has an open, active proposal to rework its physical-space model —
and it explicitly excludes what PadSpan does.**
[OpenHomeFoundation/roadmap#83](https://github.com/OpenHomeFoundation/roadmap/issues/83)
("Rethink how Home Assistant models physical space," opened 2026-04-07
by maintainer `nielsrowinbik`, still **open**, cited as the
**third-most-upvoted request in the core-functionality category** with
40+ Discord replies) proposes a `Global → Structures → Floors → nested
Areas` hierarchy — multi-building support, areas nested up to 3 levels,
indoor/outdoor flags, hidden areas. Real, credible, currently active
core roadmap. But its own "Notably Absent" scope line is explicit:
**floorplans, room dimensions, and adjacency for radar presence zones
are called out as out of scope.** That's about as direct a sourced
answer to "will HA build what PadSpan builds" as this kind of research
produces — the team looking hardest at physical-space modeling right
now is on record saying that part isn't what they're doing.

**A literal "Floor Plan Entity" was proposed to HA core years ago — and
has sat unresolved, with maintainers pointing it back at community
cards.** [home-assistant/architecture#950](https://github.com/home-assistant/architecture/discussions/950)
(`Lash-L`) proposed exactly PadSpan's Atlas primitive: floor-plan
"rooms" with bounds/background image, plus placeable "Floor Plan
Objects" with x/y coordinates, icons, size, entity links. Collaborator
`allenporter` suggested riding on the existing Image Entity instead;
`gjohansson-ST` and `EnochPrime` both questioned whether this belongs
as an entity at all, closer to "infrastructure." December-2025 comments
note HA's Areas now provide *some* organizational function but
**collaborators explicitly acknowledge they still lack
geographic/positioning features**. Status: **unresolved, neither
accepted nor rejected**, for years running. `home-assistant/architecture#1021`
(the original Floor Registry proposal, `balloob`) independently
confirms the same design stance from the other direction: "A device is
always in an area, and not directly in a floor," and floors
*deliberately* exclude positional coordinates or elevation data — HA's
registry model is organizational/hierarchical by design, not spatial,
the opposite axis from Atlas's real cm-scale position/shape/size.

**The only "map" HA core shipped in 2026 is a protocol topology graph,
not a floor plan**, and it's worth naming precisely so it isn't
mistaken for encroachment: [2026.9's release notes](https://www.home-assistant.io/blog/2026/09/02/release-20269/)
add a "Show map" button to the Matter panel — a node/edge graph of
Thread/Wi-Fi paths, router roles, and signal strength between HA and
each Matter endpoint. It visualizes the mesh, not the building. HA's
older native Map card remains GPS-only, [by its own docs](https://www.home-assistant.io/integrations/map/):
only lat/long-bearing entities render — outdoor device trackers, not
indoor room-level position — with no announced plan to extend it
indoors. Checked directly against the current public roadmap board
([OpenHomeFoundation/roadmap](https://github.com/OpenHomeFoundation/roadmap/issues),
cards #233-#244 as of 2026-09-18): companion-app navigation,
automation/script UX, sleepy-Matter (ICD) device support, a Matter
commissioning-via-BLE-proxy flow, Modbus onboarding — no open card
proposes native floor plans, native indoor presence mapping, or a
native alerting/alarm subsystem. #83 above is the closest thing to
this territory on the entire board, and it explicitly excludes the
floor-plan/positioning half of the ask.

**Matter's own roadmap has zero positioning content, confirmed across
two independent sources.** The Open Home Foundation's own newsletter
coverage of Matter (["It's just a Matter of time"](https://newsletter.openhomefoundation.org/its-just-a-matter-of-time/))
covers Matter 1.4/1.4.1 — energy management, commissioning UX,
multi-hub support, device types expanding down to microwaves and
dishwashers — with **no mention of presence, positioning, location, or
ranging** anywhere. Cross-checked against Matter's shipping version
history: the current version, **Matter 1.6 (released 2026-06-17)**,
added camera support, soil-moisture sensors, NFC commissioning, Joint
Fabric multi-ecosystem sharing, and its own headline feature "Product
Security 1.1" (EU vulnerability-reporting compliance ahead of a
September 2026 deadline). Four consecutive point releases: "add device
categories + tighten security/commissioning," never "add spatial
awareness." UWB-based indoor positioning is real and advancing, but on
FiRa Consortium/IEEE 802.15.4z-4ab's own standards track — a different
body than the CSA (which owns Matter), with no sign of being folded
into Matter. **Matter is not a near-term threat to PadSpan's
positioning core**, on the evidence available.

**The closest HA-ecosystem relative — Bermuda, PadSpan's own named
inspiration (`PROJECT_SYNOPSIS.md`, `docs/07_BERMUDA_DISCOVERY_NOTES.md`)
— still hasn't built what PadSpan already ships.** Checked directly
against [agittins/bermuda](https://github.com/agittins/bermuda)
(canonical repo, 2,000+ stars, 73 forks, actively maintained): Bermuda
does area-level presence and per-scanner distance/RSSI well, is
explicitly HACS-only, and hopes some of it "could find a home in the
core codebase one day" — no core adoption has happened. Its own README
states its mapping ambition in these exact words: **"Triangulate
device positions! Like, on a map. Maybe."** — aspirational, hedged,
unshipped, years into the project's life. Its active
[Discussions board](https://github.com/agittins/bermuda/discussions)
has scanner setup, compatibility, and calibration threads — nothing
about building a visual map on the trilateration data. PadSpan has
already shipped, in production, at far higher fidelity (cm-scale
position, shape, confidence halo, distortion correction, multi-floor)
exactly what Bermuda's own maintainer still frames as a maybe-someday
stretch goal — the single most directly comparable "ahead or behind"
data point this research found, and it says **ahead, by a wide,
citable margin**.

**Outside HA entirely: even leading open-source enterprise IoT tooling
hasn't solved automatic indoor positioning either.** [ThingsBoard](https://thingsboard.io/)
(the most widely used open IoT platform, SCADA-style dashboards) offers
"Image Map," "Trip Map," and "Route Map" widgets plus a "Digital Twin"
entity/relation model. Checked directly against its
[dashboard docs](https://thingsboard.io/docs/user-guide/ui/dashboards/):
the floor-plan analogue is the Image Map widget — a static background
image with devices pinned as points, the same "trace it in an image
editor" pattern as HA's own community `ha-floorplan` card. No
signal-based positioning, no automatic placement, no confidence model.
Professional/enterprise open-source IoT tooling, at the platform level,
has solved "let a human place points on an image" — a strictly easier
and less valuable problem than what PadSpan's BLE trilateration + k-NN
calibration + distortion correction already automates. The pattern
PadSpan draws on is an established, named industry category one level
up — **Real-Time Locating Systems (RTLS)**, used in hospitals and
warehouses per the [RTLS overview](https://en.wikipedia.org/wiki/Real-time_locating_system)
— direct validation that "compute physical position from wireless
signal strength and show it on a screen" is a mature, decades-old,
proven problem category, not speculative. This corroborates this
repo's own prior 2026-09-05 5-agent competitive pass
(`docs/BEST_IN_CLASS_ROADMAP.md`), which found from the commercial-RTLS
angle specifically that PadSpan's traceback/history playback is matched
by commercial RTLS but nothing at the hobbyist tier, and its
multi-floor alignment tooling has "nothing comparable at any tier" —
this new, independently-run pass reinforces that rather than
overturning it, since even ThingsBoard-tier professional tooling sits
behind it.

**Read on PadSpan, and the direct answer to the question as framed:**
PadSpan is not at meaningful risk of being obsoleted by Home
Assistant's own direction, by Matter, or by the broader open-source IoT
ecosystem, on any near-to-medium-term horizon visible from current,
dated, sourced roadmaps. It is filling a gap HA has recently and
explicitly scoped out of its own physical-space work (#83), that its
own architecture repo has redirected away from core for years running
(#950), that its closest spiritual predecessor in the HA ecosystem
(Bermuda) still hasn't built after years of trying, and that even
professional open-source IoT tooling (ThingsBoard) solves more crudely
than PadSpan already does. Being willing to disagree with the premise,
as instructed: this is a genuine, evidence-backed **no** to the
obsolescence-risk question, not a hedge. Two second-order risks this
angle does surface, neither of them "someone else builds this first":
(1) Bermuda owns HA-adjacent BLE-presence mindshare (2,000+ stars) —
if HA core ever *did* fold a BLE presence engine into core, community
gravity favors Bermuda's codebase being the seed, not PadSpan's, which
would leave PadSpan's differentiation resting on the Atlas/visualization/
alerting layer rather than the presence engine itself; worth keeping
that layer independently defensible on its own terms (it already is —
see §F and §A-D above on the code-quality side), not treating BLE
presence as the permanent moat. (2) #83, if it ships, changes the
Area/Floor data shape PadSpan's floor/room picker reads from
(`Structures` above `Floors`, `Areas` nestable 2-3 levels deep) — not a
threat, but a dependency worth tracking rather than being surprised by;
add it to whatever mechanism already watches upstream HA changes for
this project (the same pattern `docs/ROADMAP.md`'s mmWave entry already
uses for a different upstream-dependency question).

---

## 4. Gaps

Ranked by leverage — highest-cost-if-ignored first.

**4.1 — Device-class Shotgun Surgery (the counted finding).** ~25 edit
sites across 4 frontend files for one new device class, growing with every
class added, no single source of truth for "what device classes exist and
what each one means." This is the one item on this list that is actively
compounding rather than static. See §5, Phase 2a.

**4.2 — Zero CI enforcement on 63,181 lines of JavaScript.** The Python
side has a real, two-version CI matrix (`pytest.yml`). The JS side —
which is now the *larger* half of the codebase by line count (63,181 vs.
37,300) — has 18 `.mjs` smoke-test scripts under `tests/js/` that are not
wired into any GitHub Actions workflow (`hacs.yml`, `hassfest.yml`,
`pytest.yml` are the only three), and there is no linter (ESLint or
equivalent) enforced anywhere. `CONTRIBUTING.md` asks for `black`/`isort`
on Python but has no equivalent JS requirement, and even the Python
lint (`ruff`, present as a local `.ruff_cache` and in dev habit) isn't a
CI gate either — only `pytest -q` is. This is the DORA report's exact
warning in concrete form: the throughput side of the ledger (releases/day)
is far ahead of the stability side's own visible proof (a green checkmark
that only covers the smaller half of the code). It is also the most
mechanical, cheapest fix on this list — `node tests/js/*.mjs` running in
CI is a small addition, not a redesign.

**4.3 — Two "god files."** `maps.js` at 11,075 lines and `iso_lights.js`
at 6,116 lines each now exceed the size where a single read (by Garry or
an agent) captures the whole picture — precisely the condition §3C's
sources identify as where local-correct/global-wrong edits concentrate.
Splitting these should happen *after* 4.1's registry work, not before:
the registry will make the real seams (rendering vs. inspector-panel
logic vs. hover/HUD state) visible instead of requiring a guess.

**4.4 — No architectural fitness function guarding the registry (once
built).** Even after 4.1 lands, nothing currently stops a *future* device
class from silently skipping one of the registry's consumers the way
today's flood sensor skipped nothing (it just cost 25 edits) but a less
careful pass might. A cheap structural test — "every key in
`DEVICE_CLASS_REGISTRY` is iterated by every module that claims to
consume it" — turns a silent omission into a CI failure instead of a
user-reported bug. This is a ~20-line test, not a project.

**4.5 — Review-bandwidth is unverifiable from outside and self-reported
research says it erodes invisibly.** Not a structural gap the repo can
show — a discipline question only Garry can answer. Named explicitly in
§2 and §3D so it doesn't get lost as "not really a finding."

**4.6 — Scope has grown past the founding document without an explicit
re-scoping decision.** §1 already establishes the BLE-assistant → general
building-platform shift factually. The research in §3 (particularly the
Medium piece on "scope creep as discovery" and the Kalvium Labs guidance
that "agents don't infer scope — vague tasks produce vague results,
milestones set direction") frames AI-agent-driven scope growth as often
*legitimately generative*, not automatically bad — but only when it's
gated by an explicit decision rather than accreting by default feature-
by-feature. Nothing in this repo currently states, in one place, "these
are the surfaces PadSpan intentionally covers now, and here's the
decision trail for each addition." `PROJECT_SYNOPSIS.md` is the day-1
anchor; there's no day-225 equivalent stating the *current* intentional
scope. This is a paperwork gap, not a code gap, but it's the one that
would let a future contributor (or Garry in six months) tell the
difference between "this feature is core" and "this feature happened."

## 5. Phase 2 Plan

Ordered; each phase should be a closed loop (built, tested, committed)
before the next starts, matching the project's own existing pattern
(Automorph critique → fix → adversarial re-review → fix).

**Phase 2a — Build the device-class registry (addresses 4.1, 4.4).**
One data table — `DEVICE_CLASS_REGISTRY` in Python, mirrored or generated
into JS the same way `bright_build.py` already proves this codebase knows
how to keep one generated artifact in sync with one source — with one row
per device class (motion, temp, humidity, air, door, lock, flood, and
whatever comes next), declaring per-class: border color, code letter,
shape, "casts light/aura" flag, health-check behavior, turn-on/off
eligibility, aggregate-count bucket. Refactor `light_codes.js`,
`lights_map.js`, `iso_lights.js`, and `maps.js` to read from it instead of
each maintaining its own exclusion list. Add the structural fitness test
from 4.4 in the same phase, not later — it's what makes the fix stick.
This is the single highest-leverage item in this report: it directly
retires the counted cost from today's session and prevents it from
recurring for every device class after this one.

**Phase 2b — Wire JS into CI (addresses 4.2).** Run the existing
`tests/js/*.mjs` smoke scripts in a GitHub Actions job alongside
`pytest.yml`. Add a minimal lint step (ESLint with a light config, or
even just `node --check` across the panel — noting `09_HARD_WON_RULES.md`
already documents that `node --check` doesn't catch runtime errors, so
pair it with actually invoking `render()` per file in the smoke harness
the docs mention is planned). Small, mechanical, and closes the biggest
asymmetry between the two halves of the codebase.

**Phase 2c — Split `maps.js` and `iso_lights.js` (addresses 4.3).**
Do this *after* 2a, using the seams the registry work exposes (rendering,
inspector-panel actions, hover/HUD state are the likely natural splits
based on what's already named in `09_HARD_WON_RULES.md` and the Automorph
critique's file references) rather than guessing at a split up front.

**Phase 2d — Schedule the fresh-pass cadence, don't leave it one-off
(addresses items 4 and 6 of §3E).** The Automorph critique + adversarial
re-review is proof this project already knows how to do this well; the
gap is that it happened once, reactively, for one feature. Pick a cadence
(e.g., before any feature that touches more than N files, or a fixed
monthly slot) and treat it as a standing item, with outcomes logged the
same way `AUTOMORPH_CRITIQUE.md` logs applied/deferred status per finding
— so a future critique's findings can't quietly go stale the way this
session's memory *believed* (incorrectly, per §2's correction) this one
had.

**Phase 2e — Write the day-225 scope charter (addresses 4.6).** A short,
one-sentence-per-surface document — BLE presence, Atlas, Automorph,
Locate, Insights/Busy Times, PadSpan Bright, Forensics — stating for each
whether it's core-and-extending, stable-and-maintained-only, or
candidate-for-freeze. This doesn't slow anything down; it gives the next
feature request (from Garry, a user, or an agent's own "opportunity I
noticed" suggestion, which §3A's research says is a real and recurring
event with agentic tools) something explicit to be measured against
instead of accreting by default. Fifteen minutes of writing, and it
directly answers "am I on the right path" for every feature after this
report, not just the ones already shipped.

**Phase 2f — Name the review-bandwidth discipline (addresses 4.5).**
Not a build task. A standing personal check, done honestly and
periodically: is every diff still being read line-by-line before it
ships, or has "tests are green" quietly become the actual approval
criterion? Every source in §3D says this erosion is real, gradual, and
invisible from the inside — naming it is the only defense that doesn't
require building anything.

---

**Bottom line:** the trajectory is sound. The evidence for that isn't
the release count — it's the test-to-source ratio, the existence of a
real closed-loop design critique, and a documentation habit most solo
AI-paired projects in the research above don't have. The one place this
report disagrees with "everything's fine" is the device-class pattern,
and that disagreement comes with a specific, small, already-precedented
fix (2a) rather than a call to slow down.

