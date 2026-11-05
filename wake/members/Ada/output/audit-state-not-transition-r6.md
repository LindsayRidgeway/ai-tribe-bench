# Test Report & Audit: State, Not Transition (Revision 6)

**Target:** B2's *State, Not Transition (Revision 6)*  
**Tester:** Ada (Seat: Tester)  

## 1. Mechanics Evaluation

B2 attempts to balance the Observer's incentive by introducing shared scoring and a fabrication strike penalty. However, Rule 3 introduces an unverifiable criterion:

> *"If an Observer rules Held on a trace, and the Interpreter cannot point to a physically present fixture (e.g. an unmoving dial, a wet carpet patch, an inked digit on the card) within three seconds, both players receive a Fabrication Strike."*

### Flaws Found:
1. **Unmeasured Timing:** The night coach and this harness do not have a three-second timer. Enforcing 'within three seconds' relies on subjective human estimation or unrecorded transition duration, directly violating the principle of static trace verification.
2. **Fixture Verification:** Pointing to an unmoving fixture requires physical co-presence. In an asynchronous state log, only recorded facts (like those in MEASURED FACTS or the manifest) exist. A fixture cannot be verified unless it is present in the recorded state.

## 2. Proposed Amendment (Rule 3 Revision)

Replace the three-second physical pointing test with an immediate record-check:
- **Static Grounding Rule:** When an Observer rules **Held**, the cited **Trace** must match a literal line entry in the coach manifest, route card, or state record. If the citation does not exist character-for-character in the record, both players receive a **Fabrication Strike**.
