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
3. External research findings — `[IN PROGRESS: 3.1-3.3 alarm/alert angle done; 3.4-3.6 entity/device-class rendering angle done; other angles may still land]`
4. Gaps — `[IN PROGRESS: 4.1 alarm/alert done; 4.2 entity/device-class rendering done]`
5. Phase 2 plan — `[IN PROGRESS: 5.1 alarm engine done; 5.2 device-class registry done]`

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

`[PENDING — written after the research below, not before]`

## 3. External Research Findings

`[DONE — alarm/alert architecture pass. Other research angles may still be pending.]`

### 3.1 Alarm/Alert Subsystem Architecture — Deep Dive

Scope of this pass: given that flood is PadSpan's first bespoke alarm
subsystem (built from scratch this session, see §1), and the founding
worry is "five different bespoke alarm subsystems that don't share
code," this section researched how mature systems — inside and
deliberately outside the HA/smart-home world — architect alarm/alert
handling as a *general* subsystem, not a per-hazard-type build.

**Home Assistant's own `alert` integration** ([docs](https://www.home-assistant.io/integrations/alert/))
is HA core's existing, generic answer to exactly this problem: watch
any entity for a target state, fire repeating notifications
(`repeat:` a list of minute intervals), support `can_acknowledge`
(silences the repeat without touching the underlying entity),
`skip_first`, and a `done_message` sent once the source returns to
normal. It is hazard-agnostic by construction — nothing in it knows or
cares whether the watched entity is a flood sensor, a door, or a
freezer temperature. PadSpan's flood feature does not use it, or
anything shaped like it; `flood_latch.py` is a bespoke module built
around one `device_class` string. This is the single most concrete
confirmation available that PadSpan skipped past an existing generic
building block straight to a hazard-specific one — worth knowing even
though `alert` alone would not have been sufficient (see below).

**`alarm_control_panel`** ([docs](https://www.home-assistant.io/integrations/alarm_control_panel/),
[architecture discussion](https://github.com/home-assistant/architecture/issues/54))
is HA core's real state machine for intrusion: `disarmed`,
`armed_home/away/night/vacation/custom_bypass`, `arming`, `pending`,
`triggered`, each with defined entry/exit-delay semantics. The
community's **Alarmo** ([github.com/nielsfaber/alarmo](https://github.com/nielsfaber/alarmo),
[guide](https://smarthomescene.com/guides/alarmo-make-your-own-alarm-system-in-home-assistant/))
builds a full multi-area, multi-user, per-sensor-bypass security
product entirely on top of that one generic FSM — sensors are
*enrolled* into the alarm as a role ("this entity participates in
armed_away's perimeter"), completely decoupled from whatever
`device_class` or rendering treatment that entity gets elsewhere in
HA. That decoupling — *capability/role is a separate axis from
physical device_class* — is the architectural lesson most directly
transferable to Atlas's exclusion-list problem (see §3.3 below), not
just to alarms.

**Matter's Smoke CO Alarm cluster** (device type `0x0076`,
[matter-survey.org](https://matter-survey.org/device-types/118),
[Sensereo MSC-1](https://sensereo.com/msc-1/)) is the current (2026)
cross-vendor standard for exactly one PadSpan-relevant hazard class. It
models smoke and CO as two *independently tracked* alarms sharing one
attribute *shape* (state enum, battery-alert, test-in-progress,
end-of-service, interconnect-alarm attributes) rather than one flag or
two unrelated mechanisms — i.e. the standards body's answer to "does
smoke share code with CO" is "same template, separate instances," which
is the shape this report recommends PadSpan move flood toward before a
second hazard type arrives.

**Flo by Moen and Phyn** are the closest deployed commercial analogs to
PadSpan's flood feature specifically — a residential water-shutoff
alarm engine, in production, at scale. Flo's documented severity model
([Moen Solutions](https://solutions.moen.com/Smart_Sump_Pump_Monitor/Sump_Pump_Monitor:_Tips/Managing_Alerts))
is three tiers — **Critical / Warning / Informative** — with severity
*driving behavior*, not just color: a Critical alert triggers
auto-shutoff and notifies **even if the user disabled notifications**;
Warning/Informative respect user prefs. FloSense
([explainer](https://solutions.moen.com/Flo_Smart_Water_Monitor_and_Shutoff/Alerts,_Notifications,_and_Settings/FloSense,_explained))
adds anomaly detection on usage patterns on top of the binary
leak-sensor case — a plausible future direction, not an urgent gap.
Both Flo (native `flo` HA integration, plus a maintained fork
[ajplotkin/moen_flo](https://github.com/ajplotkin/moen_flo) after
Moen's SSO migration broke the original) and Phyn
([community thread](https://community.home-assistant.io/t/phyn-integration-water-leak-detector/316197))
integrate into HA the same way everything else does — one more bespoke
custom component each. There is **no emerging water-alarm standard**
the way Matter did for smoke/CO; if PadSpan wants a richer flood
severity model it has to invent one, not inherit one. Flo's 3-tier
model is the best available off-the-shelf reference to crib from.

**ISA-18.2** (process-industry alarm management,
[ISA explainer PDF](https://www.isa.org/getmedia/55b4210e-6cb2-4de4-89f8-2b5b6b46d954/PAS-Understanding-ISA-18-2.pdf),
[instrumentationtools summary](https://instrumentationtools.com/isa-18-2-alarm-management-in-process-plants/))
and its UK-guidance counterpart **EEMUA 191**
([EEMUA](https://www.eemua.org/products/publications/print/eemua-publication-191),
[Wikipedia](https://en.wikipedia.org/wiki/Alarm_management)) define a
richer state machine than PadSpan's flood latch has: an alarm's
lifecycle is genuinely **three independent axes**, not one flag —
active/normal, acknowledged/unacknowledged, and
shelved/suppressed/out-of-service (administratively silenced). An
acknowledged alarm stays visible until the condition itself clears;
acknowledging never auto-resets a still-active condition. EEMUA also
publishes hard numeric benchmarks worth borrowing as a discipline, not
just a citation: **≤1 alarm/10 min is "manageable" steady-state,
>10 alarms/10 min is a declared "flood"**
([benchmark source](https://industrydigits.com/resources/alarm-load-scorer/)).
PadSpan's flood latch has no rate limiting at all today — nothing
would stop a chattering sensor from generating unlimited alarm-history
entries once a unified history exists.

**NFPA 72** (fire alarm code) independently arrives at the same
three-verb split, but for physical panels: **Acknowledge** (silence the
local buzzer, log that a human saw it, no other effect), **Silence**
(also cut the building horns/strobes), and **Reset** (clear the latch —
correctly documented as *not* implying the event was false, and only
appropriate after the cause is actually gone) —
[facpmanuals](https://facpmanuals.com/blog/alarm-vs-trouble-vs-supervisory),
[48fireprotection](https://www.48fireprotection.com/silence-fire-alarm-panel-dilemma/).
PadSpan's flood alarm today has exactly **one** affordance —
`async_reset_latch` — that conflates all three: there is no
acknowledge-without-clearing action, and no silence-without-resetting
action. Somebody who sees the alert and wants to say "I know, working
on it" currently has no move except to make the alarm disappear
entirely.

**PagerDuty / Opsgenie / Prometheus Alertmanager** — deliberately
researched *outside* home automation, as instructed, because this is
where "alarm engine as reusable software infrastructure" is most
mature. The transferable ideas:
- **Alert vs. Incident are two different objects**
  ([PagerDuty docs](https://support.pagerduty.com/main/docs/incidents)):
  a raw signal (alert) is distinct from the tracked, human-facing thing
  it routes into (incident). Severity lives on the alert; priority on
  the incident. PadSpan has neither distinction today — one
  `binary_sensor` state change *is* the alarm, with nothing in between
  a generic history UI could show across hazard types.
- **Acknowledge halts escalation without resolving**
  ([escalation-policy docs](https://support.pagerduty.com/main/docs/escalation-policies)) —
  a third, independent lineage (software incident response, not
  life-safety code or process industry) converging on the identical
  ack≠resolve split NFPA 72 and ISA-18.2 already landed on. Three
  unrelated fields agreeing this precisely is a strong signal this is
  a near-universal correct decomposition, not something to reinvent
  from scratch.
- **Escalation policies are declarative, reusable objects** — an
  ordered rule list plus timeout, defined once and attached to N alert
  sources, rather than written per alert type.
- **Alertmanager's grouping/routing/inhibition**
  ([docs](https://prometheus.io/docs/alerting/latest/alertmanager/),
  [routing-tree guide](https://www.bigiron.cc/guides/alertmanager-routing-trees-grouping-inhibition-and-silences)):
  route by label (e.g. severity) to different receivers, and
  **inhibit** a lower-severity alert when a related higher-severity one
  is already firing. Directly relevant the day PadSpan has two
  simultaneous alarm types (e.g. a leak *and* a door left open) and
  doesn't want to spam Nicole, whose existing rule elsewhere in this
  project is "plain language, taps only" — an alert flood to her is a
  concrete, already-flagged failure mode, not hypothetical.

### 3.2 Explicit confirm/challenge callouts

- **CONFIRMS** the premise: `alarm_control_panel` + Alarmo are an
  existence proof, inside HA's own component model, that a generic FSM
  plus declarative per-entity enrollment scales to a real multi-zone,
  multi-user security product — this is not a theoretical architecture,
  it is shipping.
- **CONFIRMS**: the ack/silence/reset three-way split is not something
  PadSpan needs to invent — NFPA 72 (life-safety code), ISA-18.2
  (industrial process standard), and PagerDuty/Opsgenie (software
  incident tooling) are three independent lineages that converged on
  materially the same decomposition. That convergence is the strongest
  single piece of evidence in this whole research pass.
- **CHALLENGES the scale, not the direction**: every industrial
  reference above (ISA-18.2's full 7-state machine, EEMUA's flood
  benchmarking discipline) assumes a staffed console and a real risk of
  alarm floods at volume. PadSpan is a single-operator residential
  product currently optimizing for 1.7 releases/day feature velocity —
  adopting the *full* ISA-18.2 state machine (including shelved,
  suppressed, out-of-service as separate first-class states) would be
  over-engineering relative to actual usage. Flo's simpler 3-tier
  severity model, with severity gating behavior, is the right *scale*
  reference; ISA-18.2/EEMUA are the right *shape* references
  (independent axes, don't conflate ack/reset) to borrow from without
  importing all seven states.
- **CHALLENGES harder, and this is the one genuine surprise of the
  pass**: none of the commercial products actually researched — Ring,
  SimpliSafe, ADT, Flo, Phyn, Nest Protect — are architected as a
  *general* alarm engine a third party extends per new hazard type.
  Each is a closed product built around one hazard type (or one tightly
  bundled hardware line). The pattern PadSpan should build toward is
  structurally closer to PagerDuty/Alertmanager (software
  incident-management infrastructure) than to anything an actual
  smart-home vendor ships. Put plainly: **no home-automation product on
  the market today has already solved "N heterogeneous hazard types on
  one shared alarm engine."** Building one is not catching up to Ring
  or ADT — it's ahead of the category. That cuts both ways: it's a real
  gap in the market PadSpan is positioned to fill (multi-hazard Atlas,
  not single-hazard like every competitor researched), but it also
  means there is no proven reference implementation to copy wholesale —
  this is genuine, unde-risked product design, not a "well-trodden path
  everyone else already validated."

### 3.3 Verdict on this angle (alarm/alert angle)

**On the core question — should there be a generic alarm engine —
the evidence strongly confirms Garry's instinct.** Every serious
reference model researched (life-safety code, industrial standard,
software incident tooling, and HA's own core `alert`/`alarm_control_panel`
domains) independently separates *hazard type* from *alarm state
machine* from *severity/escalation policy*. `flood_latch.py` is
currently **not** built that way — it is hazard-specific top to
bottom, with no generic `AlarmRecord`/`AlarmLatch` object underneath a
future smoke, CO, or intrusion alarm could reuse. Building a second
bespoke alarm subsystem the same way flood was built would repeat, and
likely worsen, the exact ~25-edit-sites cost already measured for a
*much* simpler feature (rendering one device class) in §1 — alarms
carry more surface per hazard (trigger, acknowledge, reset, notify,
escalate, history) than pure rendering does, so the per-hazard
multiplication is worse, not better, if left unfixed.

**But don't over-scope the fix.** The right-sized target is closer to
Flo's 3-tier severity model wearing ISA-18.2/NFPA-72's independent-axes
shape than to the full industrial 7-state machine: one `AlarmRecord`
concept — `{hazard_type, entity_id, severity (critical/warning/info),
triggered_at, acknowledged_at | None, cleared_at | None, expires_at}` —
with one Python module and one JS mirror, distinct **acknowledge**
(stop the noise, don't clear) and **reset** actions (today only reset
exists), and one shared alarm-history list instead of one bespoke
banner per hazard. Flood should be refactored into the *first caller*
of that engine, not thrown away — it already ships and is tested; this
is a generalization pass, not a rewrite. The Phase 2 plan below (§5.1)
sizes this as concrete, buildable work, and the timing argument is
simple: it's far cheaper to make flood the first caller of a shared
engine now, with one hazard type in play, than to do it later with two
or three already hand-built the bespoke way.

## 4. Gaps

`[IN PROGRESS — filling in per research angle; §4.1 below is the
alarm/alert angle only. Other angles (BLE core, pricing/licensing,
frontend exclusion-list pattern generally, etc.) may still be pending
and should be added as their own numbered subsections, not overwrite
this one.]`

### 4.1 Alarm/Alert Subsystem — specific, measured gaps

1. **No generic alarm object.** `flood_latch.py` is hazard-specific
   from its first line (`device_class == "moisture"` is hardcoded into
   the event listener). There is nothing underneath it a smoke, CO, or
   intrusion alarm could call into — the *next* alarm type gets built
   the same bespoke way unless this is fixed first.
2. **No severity axis at all.** A slow drip and a burst pipe render
   identically — one boolean latch, no tiers. Flo's Critical/Warning/
   Informative split (§3.1) is the nearest off-the-shelf model and is
   absent entirely.
3. **Acknowledge and Reset are conflated into one action.** Only
   `async_reset_latch` exists. NFPA 72, ISA-18.2, and PagerDuty all
   treat "I've seen this" and "this is actually resolved" as distinct,
   independently-triggerable actions (§3.2); PadSpan has no
   acknowledge-without-clearing move today.
4. **No unified alarm history/log.** Today's UI surface is a single
   sidebar banner for the one alarm type that exists. There is no
   list a user (or Garry, debugging) can open to see "every alarm,
   every hazard type, in one place, in order" — which is also the
   object §3.1's Alertmanager/PagerDuty pattern needs to exist before
   grouping, routing, or inhibition between hazard types is even
   possible to build.
5. **No rate limiting / flood protection.** Nothing stops a chattering
   sensor from generating unbounded alarm events once a history exists
   to fill up. EEMUA's numeric benchmark (§3.1) is a usable off-the-shelf
   threshold to borrow, scaled down for a single-operator residential
   context (not the literal industrial number).
6. **No escalation policy concept.** Today's flood alarm does exactly
   one thing (persist a sidebar banner) regardless of how long it's
   been ignored. There's no declarative "if unacknowledged after N
   hours, do X" — the PagerDuty/Opsgenie pattern (§3.1) shows this
   should be a reusable policy object, not per-hazard code, once it's
   needed (not urgent for a single-operator household today — flagged
   as a gap, not a must-fix-now item).

## 5. Phase 2 Plan

`[IN PROGRESS — filling in per research angle; §5.1 below is the
alarm/alert engine proposal only. Other angles may add their own
numbered subsections.]`

### 5.1 Alarm Engine — proposed scope (right-sized, not ISA-18.2-in-full)

**Principle:** generalize now, while there is exactly one hazard type
(flood) to migrate, rather than after a second one is hand-built the
bespoke way. This is a refactor of what already ships, not a rewrite —
flood_latch.py's actual behavior (2-day active window, event-driven
capture) is correct and tested; only its *shape* (hazard-specific
top-to-bottom) needs to change.

1. **New shared module, backend:** `alarm_engine.py` — one
   `AlarmRecord` shape: `{hazard_type, entity_id, severity
   ("critical"|"warning"|"info"), triggered_at, acknowledged_at |
   None, cleared_at | None, expires_at}`, stored under one
   `SettingsStore` key (`alarms`, replacing `flood_latches` as a
   migration, not an addition) keyed by hazard_type + entity_id.
   Exposes `trigger()`, `acknowledge()`, `reset()`, `is_active()`,
   `is_acknowledged()` — hazard-agnostic; a hazard module (flood,
   later smoke/CO/intrusion) only supplies the `device_class` →
   `hazard_type`/`severity` mapping and calls in.
2. **New shared module, frontend:** `alarm_engine.js` mirroring the
   same shape and the three actions, replacing `floodLatchActive()`'s
   hazard-specific logic with a call into the shared module — the
   "change one, change both" maintenance burden the flood_latch.py
   docstring already flags becomes "change one" instead.
3. **Migrate flood as the first (and only, for Phase 2) caller.** Do
   not build a second hazard type in Phase 2 just to prove the engine
   generalizes — that risks scope creep on a feature nobody asked for
   yet. Flood becomes the engine's first real caller; the abstraction
   is validated by successfully carrying flood's existing behavior
   (2-day window, one entry per sensor) through the refactor with the
   existing test suite still green, not by adding new hazard types.
4. **Add the missing acknowledge action** to the UI (distinct button
   from Reset) — the single most concrete, user-visible gap from §4.1,
   and the cheapest of these to ship on its own if the rest of the
   engine work needs to be sequenced later.
5. **Add one unified alarm history view** (even a simple list, not a
   dashboard) — the object every other item on this list, and any
   future escalation/routing work, needs to exist first.
6. **Explicitly deferred out of Phase 2** (flagged as future work, not
   silently dropped): severity-driven auto-actions (Flo's
   auto-shutoff-on-Critical pattern — PadSpan has no valves to shut
   off, but the *pattern* — severity gates behavior, not just color —
   applies to any future hazard type with an actuator), escalation
   policies, alarm-rate limiting/flood protection, and shelve/
   suppress/out-of-service states. None of these are needed until
   there's a second hazard type or a second household member actively
   managing alarms; building them now would be exactly the kind of
   speculative complexity Garry's own guidelines warn against.
