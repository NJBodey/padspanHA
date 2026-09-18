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

### 3.4 Analytics depth: anomaly detection, predictive maintenance, occupancy-driven HVAC, cross-device correlation

`[DONE — full research trail: research/analytics-depth-phase2.md]`

Researched what BMS, RTLS, and digital-twin platforms offer beyond the
historical dwell-time/occupancy analytics PadSpan already has (Insights /
Busy Times), and whether it's realistically buildable solo, with AI
assistance, at residential scale — or whether it requires a scale of data
science PadSpan genuinely can't reach. Full sourced writeup:
[research/analytics-depth-phase2.md](research/analytics-depth-phase2.md).

**Split verdict, not a single yes/no** — the research separates cleanly
into three buckets:

- **Buildable now, real ROI (do it):** statistical baseline-deviation
  flagging on data PadSpan already computes (Insights/Busy Times dwell
  time vs. that same room's own rolling history) — the exact pattern Flo
  by Moen / Phyn use for leak detection, and the pattern ecobee's own
  production thermostats use for occupancy prediction (a random-forest
  model trained *per individual home*, not a fleet — "relatively
  efficient to train for individual devices" per the published research).
  No ML library, no fleet data, no new device-class plumbing needed.
- **Buildable, conditional value:** explainable cross-device correlation
  via association-rule mining ("motion in Kitchen predicts Kettle on
  within 3 min, seen 84% of mornings") — cheap to compute nightly, fully
  explainable (no black box), reuses stored history. Real caveat: it only
  pays off in homes with enough distinct device classes wired in to
  generate discoverable patterns — worth checking against actual Install
  Base device-class diversity before building, not just assumed.
- **A real trap — do not chase or market this:** true predictive
  maintenance (equipment-failure signatures, e.g. "this compressor fails
  in 14 days") and enterprise FDD fault-mode libraries (on any given day
  40% of commercial AHUs run with an active fault, and the FDD industry
  exists to rank hundreds of named fault types against that). Both are
  built by fleet operators (ABB, Siemens, Uptake, IBM Maximo) from
  thousands of instrumented, actually-failing identical units — data a
  single-home, no-telemetry, GPLv3 HACS integration structurally has no
  path to, by design. Borrowing "predictive maintenance" language from
  BMS vendors would promise a capability the product cannot deliver at
  N=1 furnace.

**PadSpan-specific finding:** PadSpan's BLE presence fabric is already the
one input commercial occupancy-driven HVAC vendors pay the most to
acquire — BrainBox AI, 75F, and Siemens DVO report 15–28% documented
energy savings, with occupancy-awareness adding a further **+8.6%** on top
of a 25% base AI-control saving in one published case study — and it's
already richer than what most residential thermostats get natively (one
sensor per zone vs. PadSpan's trilaterated, room-level graph). An
occupancy-aware HVAC-suggestion feature would ride on infrastructure
PadSpan already shipped, not request new data-science capability.

**Ties directly to the §1 architectural finding, and to §3.3 above:** both
anomaly detection and cross-device correlation are inherently
per-device-class concerns — exactly the dimension currently hand-threaded
separately through `light_codes.js`, `lights_map.js`, `iso_lights.js`, and
`maps.js`. Building analytics on top of today's architecture inherits that
same scattered-list tax per new capability, the same way a second bespoke
alarm subsystem would inherit it per hazard type (§3.3). A device-class
registry refactor reads as a shared prerequisite for both threads, not
unrelated cleanup for either — see Gaps §4.2.

**Bottom line for this angle:** analytics-depth is not uniformly a good
Phase 2 investment or uniformly a trap. Pursue the slice that rides on
data and infrastructure PadSpan already has and stays statistical/
explainable (baseline deviation, association-rule correlation,
occupancy-aware HVAC hints); explicitly do not pursue or market
predictive-maintenance/enterprise-FDD-style analytics — the evidence says
plainly that residential-scale data doesn't support it, regardless of
developer skill or AI assistance.

### 3.7 BMS / Digital-Twin Category Comparison — Willow, Honeywell
Forge, Johnson Controls, Siemens Desigo, Disruptive Technologies,
Density.io, Matterport, and the "is this a category" question

Scope of this pass (run outside the alarm/alert angle above, live web
search, 2026-09-19): the specific companies Garry named as the
category PadSpan is drifting toward, researched for what they actually
do that a residential tool doesn't need, what PadSpan is quietly
reinventing pieces of, and whether a "residential-scale BMS" category
exists with PadSpan as an example of it.

**What real BMS/digital-twin platforms do that a home never needs —
the dividing line is portfolio scale, not any single feature.**
Willow's knowledge graph "unifies spatial, static, and live data"
across "75+ built world systems" and processes "over 10 million
telemetry points in real-time" ([Willow platform](https://willowinc.com/willow-platform/), [Willow digital twin](https://willowinc.com/willow-digital-twin/)); its Oxford
deployment is cited as "approaching $1 million per year in avoided
operating and energy costs" ([Willow Knowledge Graph](https://willowinc.com/knowledge-graph/)) across a large
commercial estate, and even its single-building flagship deployment at
Brookfield's One Manhattan West is measured in "200 hours of developer
*integrator* time saved in a single month" ([Microsoft: RealEstateCore now available](https://techcommunity.microsoft.com/blog/iotblog/realestatecore-a-smart-building-ontology-for-digital-twins-is-now-available/1914794)) — the unit of value
is professional integrator time across many disparate systems, a
problem that doesn't exist for PadSpan because HA already normalizes
every entity it draws before Atlas ever sees it. Siemens Desigo CC's
headline capability is protocol translation — "BACnet, OPC, Modbus and
SNMP" plus "KNX over IP and M-bus TCP/IP" ([Siemens Desigo CC](https://www.siemens.com/us/en/products/buildingtechnologies/automation/desigo-cc.html)) — dozens of
incompatible field protocols from different manufacturers, normalized
into one view. **This is the single biggest reason PadSpan's ~100k
lines look small next to "a real BMS": it is missing an entire
subsystem by design, correctly** — HA did that work already. Willow's
"Active Control" grid-interactive load shedding ([Willow platform](https://willowinc.com/willow-platform/)) requires a
utility relationship no residence has. None of this is latent value
PadSpan is leaving on the table by not building it; it's a different
problem class entirely.

**Formal ISA-18.2-style alarm-management apparatus is scaled for
control-room *volume*, which a house doesn't have** — cross-reference
with §3.1 above, which already covers the ack/silence/reset shape in
depth; the addition from this pass is *why* that apparatus exists at
its full size. ISA-18.2 defines "alarm flood" as "more than 10 alarms
annunciating in a 10-minute period," with a rationalization process
that is a committee-driven review producing "cause, consequence and
corrective action" for every alarm type before it ships ([Emerson: Alarm Rationalization white paper](https://www.emerson.com/documents/automation/white-paper-alarm-rationalization-deltav-en-56654.pdf)).
Honeywell Forge's alarm console has Active/Archived tabs, per-alarm
flag/unflag state, and a full "Alarm Management Reporting" product line
(Collector/Archiver/Analyzer) built to produce compliance documentation
([Honeywell Forge Alarm Management Reporting](https://process.honeywell.com/content/dam/process/en/documents/document-lists/doc-list-alarm-management/hon-alarm-reporting.pdf)). That apparatus exists because an
industrial control room can have hundreds of alarms fire in minutes
during an upset and a missed one is a safety incident — citing
ISA-18.2 as *lineage* for a 2-day flood latch is honest, but the
committee-and-compliance-reporting half of that standard is solving a
volume problem PadSpan doesn't have and shouldn't build toward.

**Device-on-floorplan control has both a commercial and an open-source
precedent, and both point at the same fix §3.1 already flagged for
alarms.** Desigo CC binds devices to floorplans via "dedicated graphic
templates" drawn from a *library*, looked up by device type rather than
hand-drawn per feature ([Siemens Desigo CC](https://www.siemens.com/us/en/products/buildingtechnologies/automation/desigo-cc.html)). Matterport's "Tags" are one
generic attachable-metadata primitive reused across every asset type —
"each tagged asset linked to its specifications, maintenance history,
and vendor contact" ([Matterport: Facilities Document Management](https://matterport.com/blog/facilities-document-management)) — not a
different code path per asset class. §3.1 already found this exact
decoupling in Alarmo ("capability/role is a separate axis from
physical device_class") and flagged it as transferable to "Atlas's
exclusion-list problem" (§1's ~25-edit-sites finding) without spelling
out the industry's dedicated answer to *that specific* problem — which
is worth naming directly: **Brick Schema, Project Haystack, and
RealEstateCore** are metadata ontologies that exist because "highly
customized and inconsistent modeling practices" emerge whenever a
device's class/capabilities are ad hoc logic instead of structured data
([Brick vs. Haystack comparison](https://medium.com/@erik_paulson/a-comparison-of-the-brick-schema-and-project-haystack-2a9adde5013a), [Brick Ontology docs](https://docs.brickschema.org/intro.html)). Brick specifically
represents a device as "triples of descriptive tags" ([Brick comparison page](https://brickschema.org/comparision/))
so type and relationships are *looked up*, not hard-coded into every
consumer of that data — precisely the shape of fix Section 1's finding
(`light_codes.js`/`lights_map.js`/`iso_lights.js`/`maps.js` each
maintaining an independent copy of "which device classes get special
treatment") calls for. PadSpan does not need RDF triples or a graph
database at 7 device classes — but it needs the *pattern*: one
authoritative device-class capability table those four files and the
backend all read from, instead of four hand-maintained copies. This is
the second architectural fix this report identifies with direct
industry precedent (the first being §5.1's alarm engine), and the two
are the same underlying lesson applied to two different subsystems.

**Occupancy-analytics vendors treat "what does this number mean" as a
first-class design problem — worth checking PadSpan's Busy Times/
Insights against directly, not assumed either way.** Density's public
position is that "occupancy sensor accuracy isn't one number" and for
large-area sensors they report "Time Within Tolerance" rather than a
bare percentage, because "real-world conditions matter more than a
flat '99%' claim" ([Density: "99% Accurate" Occupancy Sensors](https://www.density.io/resources/the-truth-behind-99-accurate-occupancy-sensors), [Density: How Accurate Are Occupancy Sensors](https://density.io/guides/how-accurate-are-occupancy-sensors)). BLE
RSSI-derived peak-occupancy and dwell-time numbers sit on the same kind
of noisy substrate Density is describing. This pass did not check
whether Busy Times/Insights currently present any confidence/error
framing or show bare numbers — that's a direct, checkable question
against the live UI (Gaps §4.3), not a finding either way.

**Is there a real "residential-scale BMS" category, and who else is in
it?** No incumbent combining all of PadSpan's pillars — BLE room-level
presence, a full device/sensor floorplan, historical occupancy
analytics, and an alarm-acknowledgment workflow — at consumer pricing
and DIY install surfaced anywhere in this pass. That cuts both ways:
- The commercial BMS/digital-twin vendors above are enterprise/
  portfolio businesses by construction (sales motion, pricing,
  deployment model all assume a facilities team). Honeywell's "Remote
  Building Manager" is explicitly marketed at "small- to medium-sized
  buildings" ([Honeywell SMB press release](https://www.honeywell.com/us/en/press/2020/12/honeywell-makes-building-management-easier-for-small-to-medium-sized-buildings)) — still commercial SMB (offices,
  retail), not residential, and nothing found shows any of Willow/
  Honeywell/JCI/Siemens pricing down toward a home.
- The closest incumbents by price tier and install context are luxury
  home-automation platforms — Control4, Savant, Crestron Home, Josh.ai.
  Savant's "TrueImage" (tap real room photos to control devices) is the
  closest existing consumer metaphor to device-on-a-map control
  ([Digital Systems: Control4 vs Savant vs Josh.ai](https://www.digitalsystemsav.com/blog/smartsystemcomparison/)), but nothing surfaced shows any of
  them shipping occupancy heatmaps, dwell-time analytics, or an
  alarm-ack workflow — they're control-and-scene platforms with a
  polished UI, not sensor-fusion-plus-analytics platforms.
- The closest architectural peers for the device-on-floorplan piece
  specifically are open-source HA floorplan cards — `ha-floorplan`
  (SVG-object entity binding), `housemap-card` (room-level lighting/
  climate/alarm/presence control), `houseplan-card` (no-YAML
  click-to-draw rooms) ([ha-floorplan](https://github.com/ExperienceLovelace/ha-floorplan), [housemap-card](https://github.com/AldenDana/housemap-card), [houseplan-card](https://github.com/Matysh/houseplan-card)) — visualization/
  control primitives, with no BLE fusion, analytics, or alarm workflow
  from what surfaced.

Read honestly, this means one of two things and research alone can't
fully distinguish them: either PadSpan is early to a genuine
residential-BMS whitespace the big vendors have no economic reason to
chase (one house is a rounding error next to a 40-building portfolio
contract) and the luxury-AV incumbents have no technical reason to
chase (they sell installation and scenes, not analytics) — **or**
nobody has found sufficient home demand for occupancy heatmaps and
alarm workflows to be worth building, and PadSpan is testing that
demand for the first time rather than confirming it exists. The way to
tell these apart isn't more research, it's usage data from PadSpan's
own install base (Gaps §4.3 / Phase 2 Plan §5.3).

**Solo-maintainer risk has a documented precedent in exactly this
distribution channel, separate from the BMS-category question but
raised by the same "what does PadSpan now control" lens.** Home
Assistant's security team has twice published coordinated disclosures
naming vulnerabilities in third-party HACS integrations — flaws that
"allowed an attacker to steal any file without logging in"
([HA Security Disclosure, Jan 2021](https://www.home-assistant.io/blog/2021/01/22/security-disclosure/), [HA Security Disclosure 2](https://www.home-assistant.io/blog/2021/01/23/security-disclosure2/)) — and GitHub's own
security team has separately published a methodology for auditing HA
integrations specifically because of this risk class
([GitHub Security Lab: Home Assistant code review](https://github.blog/security/vulnerability-research/securing-our-home-labs-home-assistant-code-review/)). This is the specific
vulnerability class (unauthenticated file/service access via a
third-party HACS integration) that matters most once an integration
controls locks and issues alarm state — which PadSpan now does. Nothing
found suggests PadSpan has this specific problem; the point is the risk
category is proven and rising in relevance as PadSpan's blast radius
grows, independent of code quality.

**Explicit confirm/challenge callouts for this angle:**
- **CONFIRMS**: the device-class-per-file duplication Section 1 counted
  is the *same class of problem* the BMS industry built metadata
  ontologies (Brick/Haystack/RealEstateCore) to solve, and the fix
  those ontologies point at (structured, looked-up device data instead
  of per-file hardcoded logic) is directly, cheaply adoptable at
  PadSpan's current scale without importing RDF or a graph database.
- **CONFIRMS**: no commercial BMS/digital-twin vendor, and no luxury
  home-automation platform, currently bundles PadSpan's specific
  combination of pillars at residential price/install context — which
  is consistent with genuine whitespace, not evidence PadSpan copied
  anyone's homework badly.
- **CHALLENGES**: PadSpan has crossed into a risk category (lock
  control + alarm state, on a 24-releases/14-days HACS-distributed
  integration) where a documented, ecosystem-specific vulnerability
  class applies, and there is no evidence in this repo of a security
  review addressing it — this is a real gap independent of whether the
  BMS-category positioning itself is sound.
- **CHALLENGES, mildly**: "residential-scale BMS" is architecturally
  plausible but not usage-validated — the absence of an incumbent is
  as consistent with untested demand as with unclaimed whitespace, and
  this report's research cannot resolve which without PadSpan's own
  usage data.

### 3.7 Home Assistant's Own Roadmap, Matter, and the Wider Ecosystem — Does PadSpan Risk Being Obsoleted?

This is the angle the original request centered on specifically: where
HA core, its architecture repo/RFCs, and Matter are officially headed
on Areas/Floors, native floor-plan/map visualization, and device
presence — plus a deliberate look outside HA entirely, to check whether
the underlying pattern (signal-based trilateration → floor-plan
visualization → alerting) is solved/commoditized somewhere else.

**HA has an open, active proposal to rework its physical-space model —
and it explicitly excludes what PadSpan does.**
[OpenHomeFoundation/roadmap#83](https://github.com/OpenHomeFoundation/roadmap/issues/83)
("Rethink how Home Assistant models physical space," opened 2026-04-07
by maintainer `nielsrowinbik`, still **open**, cited as the
**third-most-upvoted request in the core-functionality category** with
40+ Discord replies) proposes a `Global → Structures → Floors → nested
Areas` hierarchy — multi-building support, areas nested up to 3 levels,
indoor/outdoor flags, hidden areas. This is real, credible, currently
active core roadmap. But its own "Notably Absent" scope line is
explicit: **floorplans, room dimensions, and adjacency for radar
presence zones are called out as out of scope.** That is about as
direct a sourced answer to "will HA build what PadSpan builds" as this
kind of research can produce — the team looking hardest at
physical-space modeling right now is on record saying that part isn't
what they're doing.

**A literal "Floor Plan Entity" was proposed to HA core — and has sat
unresolved for years, with maintainers pointing it back at community
cards.** [home-assistant/architecture#950](https://github.com/home-assistant/architecture/discussions/950)
(`Lash-L`) proposed exactly PadSpan's Atlas primitive: floor-plan
"rooms" with bounds/background image, plus placeable "Floor Plan
Objects" with x/y coordinates, icons, size, and entity links. Core
collaborator `allenporter` suggested it should ride on the existing
Image Entity instead; `gjohansson-ST` and `EnochPrime` both questioned
whether this belongs as an entity at all, closer to "infrastructure."
Recent comments (December 2025) note HA's Areas now provide *some*
organizational functionality but **collaborators explicitly acknowledge
they still lack geographic/positioning features**. Status: still
**unresolved, not accepted, not rejected**. The pattern across both
this and #83 is consistent: every time HA core gets close to "should we
do spatial positioning," the answer that survives is "no, that's for
the frontend/community" (`ha-floorplan`, `easy-floorplan` — SVG cards
mapping entities onto a hand-drawn image, with no signal-based
positioning underneath).

**Floors, when HA did ship them, were deliberately metadata-only.**
[home-assistant/architecture#1021](https://github.com/home-assistant/architecture/discussions/1021)
(the original Floor Registry proposal, `balloob`) is explicit: "A
device is always in an area, and not directly in a floor," and the
proposal *deliberately* excluded positional coordinates or elevation
data. A second, independent data point that HA's registry model is
organizational/hierarchical by design, not spatial — the opposite axis
from Atlas (real cm-scale position + shape + size per object).

**The only "map" HA core shipped in 2026 is a protocol topology graph,
not a floor plan.** [2026.9's release notes](https://www.home-assistant.io/blog/2026/09/02/release-20269/)
add a "Show map" button to the Matter panel — a node/edge graph of
Thread/Wi-Fi network paths, router roles, and signal strength between
HA and each Matter endpoint. Worth naming precisely because it is
*not* a positioning map: it visualizes the mesh, not the building. Easy
to conflate "HA shipped a map feature" with "HA is entering PadSpan's
space" — the evidence says otherwise. HA's older, existing native Map
card is GPS-only and says so explicitly in its
[docs](https://www.home-assistant.io/integrations/map/): only
lat/long-bearing entities render — outdoor/GPS device trackers, not
indoor room-level position. No announced plan to extend it indoors.

**HA's public roadmap board, checked directly, has nothing in this
space right now beyond #83.** Current open cards on
[OpenHomeFoundation/roadmap](https://github.com/OpenHomeFoundation/roadmap/issues)
(checked 2026-09-18, #233–#244) cover companion-app navigation,
automation/script UX, sleepy-Matter (ICD) device support, a Matter
commissioning-via-BLE-proxy flow, and Modbus onboarding — no open card
proposes native floor plans, native indoor presence mapping, or a
native alerting/alarm subsystem.

**Matter's own roadmap has zero positioning content, confirmed across
two independent sources.** The Open Home Foundation's own newsletter
coverage of Matter
(["It's just a Matter of time"](https://newsletter.openhomefoundation.org/its-just-a-matter-of-time/))
covers Matter 1.4/1.4.1 — energy management, commissioning UX,
multi-hub support, expanding device types down to microwaves and
dishwashers — with **no mention of presence, positioning, location, or
ranging** anywhere. Cross-checked against Matter's shipping version
history: **Matter 1.6 (released 2026-06-17)**, the current version,
added camera support, soil-moisture sensors, NFC commissioning, Joint
Fabric multi-ecosystem sharing, and — the headline for 1.6 specifically
— "Product Security 1.1" (EU vulnerability-reporting compliance ahead
of a September 2026 deadline). Four consecutive point releases: "add
device categories + tighten security/commissioning," never "add
spatial awareness." Separately, UWB-based indoor positioning is real
and advancing on its own standards track (FiRa Consortium
Certification 2.0, Jan 2025; IEEE 802.15.4z/4ab) — a **different**
standards body than the CSA (which owns Matter), on its own timeline,
with no indication it's being folded into Matter's model. **Matter is
not a near-term threat to PadSpan's positioning core** on the evidence
available.

**The closest HA-ecosystem relative — Bermuda, PadSpan's own stated
inspiration — still hasn't built what PadSpan already ships.** Checked
directly against [agittins/bermuda](https://github.com/agittins/bermuda)
(canonical repo, 2,000+ stars, 73 forks, actively maintained): Bermuda
does area-level presence and per-scanner distance/RSSI well, is
explicitly HACS-only, and hopes some of it "could find a home in the
core codebase one day" — no core adoption has happened. Its own README
states its mapping ambition in these exact words: **"Triangulate device
positions! Like, on a map. Maybe."** — aspirational, hedged, unshipped,
years into the project's life. Its active
[Discussions board](https://github.com/agittins/bermuda/discussions)
has scanner setup, compatibility, and calibration threads — no active
thread about building a visual map on top of the trilateration data.
PadSpan has already shipped, in production, at far higher fidelity
(cm-scale position, shape, confidence halo, distortion correction,
multi-floor) exactly what Bermuda's own maintainer still frames as a
maybe-someday stretch goal — the single most directly comparable
"ahead or behind" data point this research found, and it says **ahead,
by a wide, citable margin**.

**Outside HA entirely: even leading open-source enterprise IoT tooling
hasn't solved automatic indoor positioning either.**
[ThingsBoard](https://thingsboard.io/) (the most widely used open IoT
platform, SCADA-style dashboards) offers "Image Map," "Trip Map," and
"Route Map" widgets plus a "Digital Twin" entity/relation model.
Checked directly against its
[dashboard docs](https://thingsboard.io/docs/user-guide/ui/dashboards/):
the floor-plan analogue is the Image Map widget — a static background
image with devices pinned as points, the same "trace it in an image
editor" pattern as HA's own community `ha-floorplan` card. No
signal-based positioning, no automatic placement, no confidence model.
Professional/enterprise open-source IoT tooling, at the platform level,
has solved "let a human place points on an image," a strictly easier
and less valuable problem than what PadSpan's BLE trilateration + k-NN
calibration + distortion correction already automates.

**The pattern PadSpan is built on is an established, named industry
category one level up: Real-Time Locating Systems (RTLS)** — used in
hospitals (staff/equipment tracking, infection control, evacuation
accounting) and warehouses (asset/pallet tracking), per the
[RTLS overview](https://en.wikipedia.org/wiki/Real-time_locating_system).
Its technology list (active RFID, BLE with direction-finding, UWB,
Wi-Fi, IR, ultrasound) is the same toolbox PadSpan draws from at
consumer/prosumer scale — direct validation that "compute physical
position from wireless signal strength and show it on a screen" is a
mature, decades-old, proven problem category, not speculative. This
corroborates `docs/BEST_IN_CLASS_ROADMAP.md`'s own prior 2026-09-05
5-agent competitive pass, which reached a compatible conclusion from
the commercial-RTLS angle specifically: PadSpan's traceback/history
playback is matched by commercial RTLS but nothing at the hobbyist
tier, and its multi-floor alignment tooling has "nothing comparable at
any tier." This new, independently-run pass did not find anything in
the broader RTLS/BMS/IoT landscape that overturns that — if anything it
reinforces it, since even ThingsBoard-tier professional tooling sits
behind it.

**Verdict on this specific angle:** PadSpan is not at meaningful risk
of being obsoleted by Home Assistant's own direction, by Matter, or by
the broader open-source IoT ecosystem, on any near-to-medium-term
horizon visible from current, dated, sourced roadmaps. It is filling a
gap HA has recently and explicitly scoped out of its own physical-space
work (§#83), that its own architecture repo has redirected away from
core for years running (§#950), that its closest spiritual predecessor
in the HA ecosystem (Bermuda) still hasn't built after years of trying,
and that even professional open-source IoT tooling (ThingsBoard) solves
more crudely than PadSpan already does. Being willing to disagree with
the premise, as instructed: the honest finding here is a genuine,
evidence-backed **no** to the obsolescence-risk question, not a hedge —
but see §4.7/§5.7 below for the two real risks this angle *did*
surface, which are about dependency surface and mindshare, not about
being technically out-built.

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

### 4.2 Analytics depth — specific gaps (§3.4)

1. **No baseline/deviation layer on Insights data.** Busy Times already
   computes per-room dwell time and peak occupancy, but nothing compares
   today's numbers to that same room's own rolling history — the data
   exists, the "is this different from normal" layer on top of it does
   not.
2. **No cross-device correlation computation anywhere in the codebase.**
   Insights aggregates within a device/room; nothing currently discovers
   or surfaces relationships *between* device classes ("when X, Y usually
   follows").
3. **No occupancy → HVAC connection point.** Atlas already places
   temperature/humidity sensors and tracks room-level BLE presence, but
   nothing joins the two into an actionable suggestion or automation
   trigger a user would see — the two data sources sit next to each
   other, unconnected.
4. **No fleet/aggregate telemetry pipeline — correctly, by design.**
   Worth stating as a permanent architectural constraint rather than a
   backlog item: PadSpan is GPLv3 with no phone-home telemetry, so true
   predictive-maintenance/fault-signature work is not a "not built yet"
   gap, it's a "cannot be built without becoming a fundamentally
   different, telemetry-collecting product" wall (§3.4).
5. **Same device-class registry gap already identified for alarms
   (§4.1 item 1) applies here too.** Any per-device-class analytics logic
   (baseline deviation grouped by class, correlation restricted to
   meaningful class pairs) would otherwise repeat the same scattered-
   exclusion-list cost Atlas rendering already has — this is a shared
   prerequisite across both the alarm-engine and analytics-depth threads,
   not two separate refactors.

### 5.2 Analytics depth — proposed scope (§3.4)

**Principle:** ship the slice that rides on data/infrastructure PadSpan
already has and stays statistical/explainable; explicitly name and defer
the slice that would require fleet-scale data the product structurally
cannot collect, so it doesn't quietly get re-proposed later without this
research behind it.

1. **Baseline-deviation flags on Insights/Busy Times data** — per-room
   dwell time and occupancy compared against that room's own rolling
   history (Flo/Phyn's pattern, applied to presence instead of water
   flow). Smallest, cheapest item on this list; reuses existing tables,
   no new device-class plumbing, no ML dependency.
2. **Association-rule cross-device correlation surface** — a nightly
   batch job over stored history producing explainable rules ("X predicts
   Y within N minutes, M% of days"), surfaced as plain-language insights,
   not a score. Before building: check actual Install Base device-class
   diversity (the admin dashboard should already have this) to confirm
   enough homes have enough distinct device classes wired in for this to
   surface anything real — a data question to answer before a build
   decision, not after.
3. **Occupancy-aware HVAC hint, passive only** — join existing BLE
   room-presence with existing Atlas temperature/humidity placement into
   a suggestion surface ("Living Room has been empty 6h, zone is still
   heating"), not closed-loop control. Leverages the one input (room-level
   presence) that commercial occupancy-driven HVAC vendors pay the most to
   acquire and that PadSpan already has natively.
4. **Explicitly excluded from Phase 2 — named so it isn't silently
   re-proposed later:** true predictive maintenance (equipment
   failure-signature detection), enterprise FDD-style fault-mode
   libraries, and anything requiring cross-install/fleet telemetry. Not a
   sequencing choice — the research in §3.4 found this requires data
   PadSpan's architecture (single-home, no telemetry, GPLv3) cannot
   collect, not just data it hasn't collected yet.
5. **Shared prerequisite with §5.1:** the device-class registry refactor
   flagged for the alarm engine (§4.1 item 1) is also load-bearing here
   (§4.2 item 5) — both threads should design against the same registry
   rather than each inventing its own, which would recreate the exact
   scattered-list problem both are trying to get out from under.
