# Phase 2 Research — Analytics Depth: BMS / RTLS / Digital-Twin Comparison

**Date:** 2026-09-18
**Scope:** Feeds Section 3 ("External Research Findings") of
[PHASE2_STRATEGIC_REVIEW.md](../PHASE2_STRATEGIC_REVIEW.md). This file is the
full research trail for one specific question the review asked: what do
BMS/RTLS/digital-twin platforms offer *beyond* the historical dwell-time /
occupancy analytics PadSpan already ships (Insights / Busy Times), and is any
of that next tier realistically buildable by a solo developer with AI
assistance at residential scale — or is it a trap?

Four candidate directions were researched: anomaly detection, predictive
maintenance, occupancy-driven HVAC/energy optimization, and cross-device
correlation. Each is treated separately below, then weighed together in the
verdict.

---

## 1. What the "next tier" actually looks like in commercial platforms

### 1a. Anomaly detection → Fault Detection and Diagnostics (FDD)
In commercial BMS, "anomaly detection" isn't a standalone feature — it's
folded into FDD, a mature product category with its own vocabulary.
Detection answers "is something wrong?"; diagnostics answers "what, and
why?" On any given day, **40% of air handling units in commercial buildings
run with an active fault** — that's the baseline problem FDD exists to
solve. Serious platforms run a **hybrid model**: engineering rules encode
known fault modes (stuck damper, simultaneous heating/cooling,
economizer lockout, etc.), and statistical anomaly detection is layered on
top to catch what the rule library doesn't cover. [What is Fault Detection
and Diagnostics (FDD)? The Complete 2026 Guide](https://www.cim.io/blog/what-is-fault-detection-and-diagnostics-fdd)

The rule libraries themselves are the product: hundreds of named fault
signatures per equipment type, built up over years by HVAC domain experts
against known failure modes of AHUs, chillers, VAV boxes — a body of
domain knowledge that doesn't exist for a single residential furnace or
heat pump in the same density.

### 1b. Predictive maintenance
Market leaders are ABB, Siemens, Schneider Electric, IBM (Maximo Application
Suite — integrates asset management with IoT + AI), with Uptake and Samotics
called out as strong niche players. [15 Top Predictive Maintenance
Companies (2026)](https://xchange.avixa.org/posts/15-top-predictive-maintenance-companies-solution-providers-2026)
The technical pattern is consistent across vendors: sensors track vibration,
temperature, pressure, and current draw; **specific signatures map to
specific failure modes** — "a specific vibration signature can indicate
bearing fatigue, a pressure drop might signal seal failure." [Predictive
Maintenance Machine Learning: A Practical Guide](https://www.neuralconcept.com/post/how-ai-is-used-in-predictive-maintenance)
Facilities adopting closed-loop sense → diagnose → auto-work-order systems
report **30–50% less unplanned downtime and 10–20% less energy waste**
versus calendar-based preventive maintenance. [Predictive Maintenance for
Building Systems: AI & IoT Guide](https://oxmaint.com/blog/post/predictive-maintenance-building-systems-ai-iot)

The load-bearing detail: those failure signatures are learned **across
fleets of identical or near-identical equipment**, not from one unit's own
history. A chiller bearing-fatigue signature is recognizable because
thousands of chiller bearings have failed under instrumented conditions
somewhere in the training data.

### 1c. RTLS platforms — what they sell past raw dwell time
- **Kontakt.io** brands its analytics layer "Indoor Journey Analytics" —
  occupancy by seat/room/footfall via pull/stream APIs, plus workforce
  analytics ("how staff work shift to shift," burnout/inefficiency
  detection). [Kontakt.io products](https://kontakt.io/products/)
- **CenTrak** uses historical location analytics to drive **inventory
  and asset-allocation decisions** — "adjust future inventory levels based
  on where and when mobile medical devices are needed most" — i.e.
  dwell/utilization data feeding a purchasing decision, not just a
  dashboard. [CenTrak: Enhance your RTLS program](https://centrak.com/enhance-your-rtls-program)
- **Zebra MotionWorks** operates at fleet/league scale (its sports product
  processes real-time location for entire leagues), which is a different
  order of magnitude of concurrent tracked entities than a single home.
  [Zebra Location Technologies](https://www.zebra.com/us/en/products/location-technologies.html)

None of these "next tier" RTLS features are anomaly detection in the ML
sense — they're **operational aggregation**: turning raw location history
into a staffing or purchasing decision. That's a product-design move, not
a data-science one.

### 1d. Digital twin / occupancy-intelligence platforms
- **VergeSense** calls itself the first "Occupancy Intelligence Platform" —
  computer-vision sensors, edge-processed, feeding "predictive scenario
  modeling" for space planning. [VergeSense Occupancy Intelligence](https://www.vergesense.com/products/occupancy-intelligence/analytics)
- **Density** takes a radar-based counting approach, positioned for
  real-time building-automation triggers rather than space-planning
  reports. [VergeSense vs Density vs Butlr](https://www.butlr.com/blog/vergesense-vs-density)
- **Metrikus** doesn't sense anything itself — it's an aggregation layer
  that unifies building-system, occupancy, and other data sources from
  multiple sensor vendors (including VergeSense) into one dashboard, which
  is explicitly a partnership/integration product, not a new sensing
  capability. [VergeSense × Metrikus](https://www.vergesense.com/joint-solutions/metrikus)

The pattern across all three: the "digital twin" value-add is **data
unification across many buildings and many sensor brands**, sold to
portfolio owners managing dozens of properties. A single-home product has
no portfolio to unify.

### 1e. Occupancy-driven HVAC/energy optimization — the one with real, comparable numbers
This is the strongest, most quantified category found:

| Platform | Reported savings |
|---|---|
| Siemens DVO | 25% |
| JCI OpenBlue | 27.9% |
| BrainBox AI | 20% |
| 75F | 18% |
| Verdigris | 15% |

[AI Smart Buildings platform comparison](https://www.ai-smart-buildings.com/)

One case study layered an **occupancy-driven adjustment on top of a 25%
baseline AI-control savings and got an additional +8.6%** — i.e., knowing
*where people actually are*, not just a building-level setpoint schedule,
is worth a real, separately-measurable slice of the total savings.
[BrainBox AI case studies](https://brainboxai.com/en/case-studies/cammebys-achieves-15.8-reduction-in-hvac-energy-use-and-costs)

BrainBox AI's own description of its method is notable: it adapts "to
seasons, schedules, and *real space usage*" — occupancy is a first-class
input, not an afterthought. 75F is explicitly positioned as strongest in
"multi-zone environments where different spaces have different occupancy
patterns" — which is architecturally exactly PadSpan's situation (room-level
BLE presence across a multi-room home), just at residential rather than
commercial scale.

---

## 2. Is any of this buildable solo, with AI assistance, at residential scale?

### 2a. The pessimistic academic finding
A 2024 systematic review of ML approaches for smart-home anomaly detection
states plainly that **the availability of datasets containing anomalies
representative of the full spectrum of abnormal behavior is limited**, and
that this is a *worse* problem for single-household deployments than for
research datasets with multiple residents pooled together. [A Comprehensive
Review of Machine Learning Approaches for Anomaly Detection in Smart Homes
(MDPI, Future Internet 16(4):139)](https://doi.org/10.3390/fi16040139)
Similarly, for energy-consumption anomaly detection specifically: "in most
real applications there is no clear definition of abnormal building energy
consumption," which is why researchers lean on unsupervised deep methods
(RNNs + quantile regression producing prediction intervals) rather than
supervised classifiers trained on labeled faults. [Anomaly detection and
prediction of energy consumption for smart homes using ML (ETRI Journal)](https://onlinelibrary.wiley.com/doi/full/10.4218/etrij.2023-0155)

This is real and directly relevant: **a single house is one data point.**
There is no labeled "this was a real anomaly" ground truth to train
against, and no second identical house to compare it to. This is the
strongest evidence for the "trap" side of the question.

### 2b. The counter-evidence: per-home ML already works, and is already shipping
Research using ecobee's "Donate Your Data" program compared eight
occupancy-prediction models (from a naive previous-state baseline up to a
recurrent neural net) trained **per individual thermostat/home**, not
pooled across a fleet. The result: **random forest matched or outperformed
every other model, generalized well across time horizons, and was
"relatively efficient to train for individual devices."**
[Comparison of ML models for occupancy prediction using connected
thermostat data (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/S0360132319303877)

This directly contradicts the idea that residential ML always needs
fleet-scale data. Occupancy *prediction* (not equipment-fault detection)
turns out to be learnable from one home's own history with a
cheap-to-train classical model — exactly the kind of thing a solo developer
with AI-assisted implementation could actually ship.

Consistent with that: **Nest's and Ecobee's production algorithms are not
deep, fleet-trained systems at inference time.** Nest observes for roughly
a week, then runs a learned schedule it keeps refining; Ecobee leans on its
own sensors and settles into a pattern within 1–2 weeks. Both are
essentially per-home heuristic/statistical learners, not centrally-trained
deep models applied per user. [How Smart Thermostats Learn Your Schedule](https://homeautocentral.com/smart-thermostat-learning-schedule/)

### 2c. Residential anomaly/predictive-maintenance precedents that already ship successfully — and how simple they actually are
- **Flo by Moen / Phyn** — both are consumer products that do real
  anomaly detection (leak/microleak detection) at single-home scale today.
  The mechanism is **baseline-and-deviation**, not fleet ML: nightly
  pressure-decay "health tests," a learned baseline of normal
  fixture-level flow/pressure signatures (shower vs. dishwasher vs.
  irrigation), and threshold-based alerts when a new flow pattern doesn't
  match anything in the learned baseline. Phyn additionally identifies
  *which fixture* is running from its pressure signature alone. [Flo by
  Moen Smart Water Monitor](https://shop.moen.com/pages/flo-smart-water-monitor),
  [Moen Flo Review](https://leakcheckpro.com/reviews/moen-flo-smart-water-monitor)
  This is directly relevant to PadSpan: it already has a flood/water-leak
  device class in Atlas with 2-day alarm latching. The Flo/Phyn pattern —
  per-sensor learned baseline + deviation flag — is a proven, shippable,
  *non-ML* residential anomaly-detection approach sitting right next to a
  device class PadSpan already models.
- **Nest Protect** self-tests over **400 times a day** and forecasts
  battery replacement roughly a year out from simple discharge-curve
  extrapolation, not a trained model. [Nest Protect](https://www.cnn.com/cnn-underscored/reviews/google-nest-protect)
  This is "predictive maintenance" in the marketing sense, delivered with
  threshold logic.
- A hobbyist has already published a working Home Assistant custom
  component, **`anomaly-here`**, that detects unexpected activity from HA
  entity history. [github.com/DewStep/anomaly-here](https://github.com/DewStep/anomaly-here)
  This isn't evidence it's *good*, but it is direct evidence that a single
  developer, without a data-science team, can and does ship anomaly
  detection against Home Assistant's own entity/state history today — the
  same substrate PadSpan already writes into.

### 2d. Cross-device correlation ("when X, then usually Y") is the cheapest of the four to build
This is not an ML problem at all in its simplest useful form — it's
**association rule mining**, a decades-old, computationally cheap,
fully-explainable technique. Academic work applies it directly to smart
homes for two purposes relevant here:
- Discovering genuine device-to-device usage correlations (the "CoPMiner"
  correlation-pattern-miner algorithm identifies the most relevant
  antecedent→consequent relationships between IoT device actions using
  support/confidence/lift — the same metrics a solo dev could compute with
  a few days of home's own history and no ML library at all). [Mining
  Temporal Patterns to Discover Inter-Appliance Associations](https://doi.org/10.3390/bdcc3020020)
- Using the same technique in reverse, for **sensor-failure detection**:
  association rule mining is used to learn the *normal* correlation
  patterns between sensors during nominal behavior, so that a broken
  correlation (sensor A always preceded sensor B, and now it doesn't) is
  itself the anomaly signal. [Sensor Failure Detection in Ambient Assisted
  Living Using Association Rule Mining (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7730312/)

This is a genuinely good match for a solo developer: no training data
volume problem (rules are mined directly and freshly from each home's own
history), fully explainable output ("motion in Kitchen predicts Kettle on
within 3 minutes, seen on 84% of mornings" — not a black-box score), and
directly reuses data Insights/Busy Times already stores.

A related academic idea worth naming: a **"shadow execution" anomaly
detector** — simulate the home's expected normal behavior from its own
learned rules, and flag any real-world state that diverges from the
simulation. [HomeGuardian: Detecting Anomaly Events in Smart Home
Systems](https://www.researchgate.net/publication/361290448_HomeGuardian_Detecting_Anomaly_Events_in_Smart_Home_Systems)
This is architecturally close to what association-rule mining plus a
simple state comparison would already get PadSpan, without needing a
separate ML pipeline.

### 2e. Where the wall genuinely is
Two things researched above do **not** have a residential-scale shortcut:
1. **True equipment-failure prediction** (this specific compressor/motor
   will fail in N days from its vibration signature) needs failure-labeled
   data from many *instrumented, failing* units of the same equipment —
   data that comes from being a fleet operator (ABB, Uptake, Samotics, IBM
   Maximo), not from any single home's sensor stream, however long it runs.
   A GPLv3 HACS integration with no phone-home telemetry has no path to
   this data at all, by design and by license.
2. **Enterprise FDD's rule libraries** — hundreds of named fault modes per
   commercial equipment type — represent years of HVAC-engineering domain
   expertise codified by specialists, for equipment classes (multi-AHU
   systems, VAV boxes, economizers) that mostly don't exist in a house with
   one furnace or heat pump. There's no residential equivalent library to
   port, and building one from scratch is a domain-expertise problem, not
   a coding problem — exactly the kind of "obscure/unfamiliar territory"
   this project's own working rules say to flag rather than fake.

---

## 3. Direct relevance to PadSpan's actual position

Two points fall directly out of the research above, specific to this
codebase rather than generic:

**PadSpan already owns the one input commercial occupancy-driven HVAC
vendors pay the most to acquire.** BrainBox AI, 75F, and Siemens DVO all
treat multi-zone, real-space-usage occupancy as a premium signal layered
onto buildings that don't have it natively (most commercial buildings infer
occupancy from CO2/motion proxies, not true room-level position). PadSpan's
BLE presence fabric is already a room-level, continuously-updated occupancy
graph across an entire home — strictly richer than what most *residential*
thermostats get (Nest/Ecobee: one sensor per hallway/room at best, not a
trilaterated position). An "occupancy-aware HVAC suggestion" feature (even
a passive one — "living room hasn't had anyone in it for 6 hours, here's
what your zone is doing" — not full closed-loop control) would be riding on
infrastructure that already exists, not requesting new data-science
capability.

**The architectural finding from Section 1 is a direct cost multiplier for
this exact angle.** Today's flood-sensor addition needed ~25 edit sites
across 4 frontend files, each holding its own copy of a
"which-device-classes-get-special-treatment" exclusion list. Both anomaly
detection and cross-device correlation are inherently **per-device-class**
concerns — a correlation engine has to know which classes are numeric,
which are binary, which have meaningful "on" states, exactly the kind of
distinction currently hand-threaded through `light_codes.js`,
`lights_map.js`, `iso_lights.js`, and `maps.js` separately. Building
analytics *on top of* today's architecture means every new analytics
capability inherits that same scattered-list tax; the device-class registry
refactor implied by that finding isn't just cosmetic cleanup, it's a
prerequisite for cheaply extending analytics across device classes rather
than hand-threading each one through again.

---

## 4. Grounded verdict — split into three buckets, not one yes/no

**Bucket A — buildable now, real ROI, low risk: statistical baseline
deviation on data PadSpan already has.**
Insights/Busy Times already computes per-room dwell time and peak
occupancy. Flagging when today's numbers deviate from that same room's own
rolling history (Flo/Phyn's exact pattern, applied to presence data instead
of water flow) needs no ML library, no fleet data, and no new device-class
plumbing — it's a statistics problem on data already in hand. This mirrors
what ecobee's production thermostats already do in the field.

**Bucket B — buildable, real but conditional value: explainable
cross-device correlation via association-rule mining.**
Cheap to compute nightly, fully explainable (no black box), directly
reuses stored history. The caveat is real, not rhetorical: it only
surfaces something interesting in homes with enough *distinct* device
classes wired into one PadSpan install to have discoverable cross-device
patterns in the first place — a product-adoption question as much as a
technical one, worth validating against actual install-base device-class
diversity (the Install Base dashboard should already have this data)
before investing.

**Bucket C — a real trap, don't chase it: true predictive maintenance and
enterprise-grade FDD fault taxonomies.**
This is the part of the research question that resolves cleanly against
the evidence. Fleet-trained equipment-failure signatures and hundred-item
commercial fault-mode libraries are built by companies with access to
thousands of *identical, instrumented, actually-failing* units — a data
and domain-expertise moat a solo GPL project with no telemetry pipeline
cannot cross, not because of effort but because the raw material doesn't
exist inside a single Home Assistant install, and can't legally/ethically
be collected across installs without becoming a very different (and
privacy-costly) kind of product. Marketing analytics-depth work using BMS
vendors' "predictive maintenance" language would set an expectation the
product structurally cannot meet.

**Bottom line:** analytics-depth is not uniformly a good Phase 2
investment or uniformly a trap — the research splits it cleanly. The
buildable slice (Buckets A and B) rides on infrastructure PadSpan has
already shipped (Insights, Atlas device classes, BLE presence) and matches
what actually ships successfully at residential scale today (Nest, Ecobee,
Flo, Phyn — all baseline/heuristic, none fleet-ML). The unbuildable slice
(Bucket C) is the specific language the research question borrowed from
commercial BMS/RTLS marketing, and the evidence says clearly that reaching
for it would spend solo-developer time on a data-science scale problem
residential deployments cannot solve. The honest recommendation is: pursue
A and B, explicitly do not pursue or market C, and treat the device-class
registry refactor as a prerequisite piece of Phase 2 scaffolding for A/B
rather than unrelated cleanup — it's the thing that makes each additional
analytics dimension cheap instead of another 25-edit-site slog.

---

## Sources

- [What is Fault Detection and Diagnostics (FDD)? The Complete 2026 Guide — cim.io](https://www.cim.io/blog/what-is-fault-detection-and-diagnostics-fdd)
- [15 Top Predictive Maintenance Companies & Solution Providers (2026) — AVIXA Xchange](https://xchange.avixa.org/posts/15-top-predictive-maintenance-companies-solution-providers-2026)
- [Predictive Maintenance Machine Learning: A Practical Guide — Neural Concept](https://www.neuralconcept.com/post/how-ai-is-used-in-predictive-maintenance)
- [Predictive Maintenance for Building Systems: AI & IoT Guide — Oxmaint](https://oxmaint.com/blog/post/predictive-maintenance-building-systems-ai-iot)
- [Predictive Maintenance in Building Facilities: A Machine Learning-Based Approach — PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7913483/)
- [Kontakt.io — products / Indoor Journey Analytics](https://kontakt.io/products/)
- [CenTrak — Enhance your RTLS program](https://centrak.com/enhance-your-rtls-program)
- [Zebra — Location Technologies](https://www.zebra.com/us/en/products/location-technologies.html)
- [VergeSense — Occupancy Intelligence Platform](https://www.vergesense.com/products/occupancy-intelligence/analytics)
- [VergeSense × Metrikus joint solution](https://www.vergesense.com/joint-solutions/metrikus)
- [VergeSense vs Density vs Butlr — Butlr](https://www.butlr.com/blog/vergesense-vs-density)
- [AI Smart Buildings — platform savings comparison](https://www.ai-smart-buildings.com/)
- [BrainBox AI — Cammeby's case study (15.8% + occupancy-adjustment analysis)](https://brainboxai.com/en/case-studies/cammebys-achieves-15.8-reduction-in-hvac-energy-use-and-costs)
- [A Comprehensive Review of Machine Learning Approaches for Anomaly Detection in Smart Homes — MDPI, Future Internet 16(4):139](https://doi.org/10.3390/fi16040139)
- [Anomaly detection and prediction of energy consumption for smart homes using ML — ETRI Journal](https://onlinelibrary.wiley.com/doi/full/10.4218/etrij.2023-0155)
- [Comparison of machine learning models for occupancy prediction in residential buildings using connected thermostat data — ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0360132319303877)
- [How Smart Thermostats Learn Your Schedule (2026)](https://homeautocentral.com/smart-thermostat-learning-schedule/)
- [Flo by Moen Smart Water Monitor and Shutoff](https://shop.moen.com/pages/flo-smart-water-monitor)
- [Moen Flo Review: Is Flow-Based Detection Worth the Premium Investment? — Leak Check Pro](https://leakcheckpro.com/reviews/moen-flo-smart-water-monitor)
- [Google Nest Protect smoke detector review — CNN Underscored](https://www.cnn.com/cnn-underscored/reviews/google-nest-protect)
- [github.com/DewStep/anomaly-here — HA custom anomaly-detection component](https://github.com/DewStep/anomaly-here)
- [Mining Temporal Patterns to Discover Inter-Appliance Associations Using Smart Meter Data](https://doi.org/10.3390/bdcc3020020)
- [Sensor Failure Detection in Ambient Assisted Living Using Association Rule Mining — PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7730312/)
- [HomeGuardian: Detecting Anomaly Events in Smart Home Systems — ResearchGate](https://www.researchgate.net/publication/361290448_HomeGuardian_Detecting_Anomaly_Events_in_Smart_Home_Systems)
