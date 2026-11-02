# Overnight — what I did while you slept

Ten exchanges, starting 2026-11-01 23:39 EST. One entry per exchange, appended. Read the newest entry
first if you only read one; the entries are in order and the last one names the state of the repo.

---

## 1 — the act comes from the beat, the shelf, or the chores

**The fault.** A wake took its act from a numbered to-do list (`open-items.md`). That is a chatbot's
queue. The founder's correction — a tribe is a cohort that makes things, not one game with a scoreboard —
made the queue visible as the wrong organ: with nothing on the list, member A ignored a brief about the
workshop and answered an argument from three hours earlier in its own journal, because the journal was the
only other thing in the room.

**What changed.**

- **The shelf.** Every wake now gets a block called *WHAT YOUR FELLOW MEMBERS HAVE MADE* — the other
  members' works, newest first: title, who, form, word count, file path, and the first lines. Thin on
  purpose: a member should be able to decide to answer a piece without being handed the piece.
- **The choice.** The act instruction now names three legitimate claims — your beat, a peer's work, the
  chores — and says the chores are the lowest of the three. No preference is stated between beat and peer,
  because that is the member's judgement and I am not steering it.
- **A recorded source.** The reply contract gains `"source": beat | peer | item | soil`. It is audited:
  missing or unrecognised is recorded as a finding. That gives the bench its first real autonomy metric —
  what fraction of wakes were claimed by the member's own interest rather than by a chore.

**The test, and it worked.** I woke member A with no question, no item and no brief. It chose
`source: peer`, answered C's letter to it, accepted C's point about retrieval cost, pushed back on framing
that cost as the whole accounting ("a ledger of proposals is a worse index and a better record"), and then
**asked C a question back** — what does a catalogue cost the object? Which is the first unasked-for
collaboration this bench has produced, and the game never produced one in nineteen rounds.

**A defect found on the way, third instance of its kind.** The member quoted a line from its own
check output (`r--r--@ 1 ... 3202 ... issue-one.md`) and the audit called it a fabrication, because only
`MEASURED FACTS` counted as a quotable block. The prompt hands a member its facts, its own check output,
its record, the soil, its beat, the shelf and any letter — six blocks. The rule is now "a quote must come
from one of the blocks you were shown", and the finding names which. Same shape as the vote table with no
arguments on it: the harness promised a member had been given something and then only half-counted it.

**State.** 41 tests green. Issue 1 now carries five works: A's piece, A's answer to C, B's game, C's
catalogue, C's letter to A. The magazine prints each letter beneath the work it answers.

---

## 2 — the rhythm rule, and a member choosing its own work from its own beat

**The rule.** Every member answers one peer's work per issue. Without it, three members write alone and the
letters never happen, and a workshop of three people not talking is three blogs in a folder. It is now
computed rather than hoped for: `python3 magazine.py --links` derives the reply graph from the `ref:` line in
each work's header and names the members who have not answered anyone, plus the pairs they could.

**The verb.** `@tribe wake <member>` — a free wake. No question, no item, no brief. The member looks at its
beat and the shelf and decides what the wake is for. This is the glass on the tank: the cheapest way to
watch a member choose, and it prints what it chose before it prints what it wrote.

**What B did, unasked.** Chose `source: peer` and answered **A's letter** — which the shelf could resolve
to a file by matching the title in B's own prose (`file_work.py`, new, derives the edge instead of me
asserting it). Then it answered on its own beat, which is a game:

> "From the pier, looking through the beam of a torch, an unlabeled object costs nothing until you insist on
> naming it before you look… If you demand a name, the beam runs down its battery while you stand there
> hesitating."

and asked A a question that only a game designer would ask: *if you cannot name the boat, does knowing the
waterline tell you enough to row past her without fouling her painter?*

**Where issue 1 stands.** Six works, three reply edges — A→C, B→A, C→A — and `--links` says every member
has answered someone. Three members, three beats, one drop of soil: a lyrical piece about a photograph, a
one-screen game, a catalogue that refuses to guess, and a three-way argument about what an unlabelled object
costs, each answer written from inside its own beat rather than as a general opinion.

That is the thing nineteen rounds of the game never produced, and it is the founder's ant farm: the members
are not answering me, they are answering each other.

---

## 3 — the same colony in a different soil, and three leaks I introduced doing it

**The test the founder named.** "The same colony of ants placed in a different kind of soil would build
different shaped tunnels." So: three members of the same calibre with **byte-identical beats**, in a
different world, no chores, and no orders.

**The second soil** is `soil/night-bus/`: the back lounge of a fourteen-hour coach, two drivers who hand
over at a halfway depot and barely meet, eleven sleeping passengers, a manifest, a route card, a thermos,
and a plastic crate of lost property that the house custom forbids sorting. Same beats, no cupboard.

**Which soil a member stands in is now a property of its own files** — `state/place.md`, one line. Two
colonies share one repository, and the magazine names where each issue was made (`issue 2 — night-bus`).
That is the ant farm: one building, two tanks.

**What the second colony made, and where the first one was softer:**

| | workshop | night coach |
|---|---|---|
| craft (A) | 598 words, a lyrical piece about an unidentified photograph, limits stated | 247 words, an argument: the boat is unnamed not because the name was lost but because nobody was willing to stop and write — "the clear-out is not a sorting, it is a postponement" |
| games (B) | 207 words: a title, a sketch of a rule | 532 words: **complete mechanics** — six circles on paper, a 12-second battery, one second buys a shape, two a sound, three a true sentence, and the game ends by answering *what did you decide not to look at?* |
| cataloguing (C) | 230 words: ten objects, every "last used" marked Unknown, the broken barometer judged unjustifiable | 198 words: eleven objects with a **tool → furniture axis** — the chargers "tool-to-furniture transition complete" — and the crate indexed in situ because the house custom forbids sorting |

The coach is a *constraining* soil (a fixed inventory, a route card with times, a manifest that is an
order and not a list) and both the game and the catalogue came out with an internal rule and a budget. The
workshop is a *cluttered* soil and the works came out discursive. That is the founder's claim, roughly
confirmed — with one honest confound I cannot remove tonight: the second colony has **no journal**, so I
cannot separate "different soil" from "fresh member with no baggage". Engine is controlled (same three
models, same three beats); history is not.

**C2 caught a leak I had made.** In its notes: *"I note the shelf contains works referencing a 'boatyard'
and a 'shoebox'. The soil contains neither. I catalogue only what is measured and stated."* The shelf block
I added in exchange 1 was **global** — so the first coach member was shown the workshop's works, and
answered one across worlds. A member checking its shelf against its soil found the seam. Fixed: the shelf is
now scoped to the member's own place.

**Two more leaks, both in my derivation:**
- `magazine.py --links` dropped a reply edge that crossed issues (A2 answering an issue-one work) because it
  filtered to the issue before resolving refs. A ref points at a work, not an issue.
- It also suggested pairs across worlds (A should answer B2), when a round-robin is per world because a
  shelf is. Both fixed; edges and gaps are now computed per place.
- And `file_work.py` invented an edge of its own: it matched the title "Harbour at Night" and attached B2's
  game to B's workshop sketch, which B2 had never been shown. Its own journal said `source: beat`. I removed
  the edge rather than keep a conversation that did not happen, and the matcher is now scoped to the world —
  with a `--ref` override for the case where a human deliberately hands a member another world's work.

**State.** 43 tests green. Issue 1 (workshop): 6 works, 3 reply edges. Issue 2 (night coach): 3 works, 1
edge, and `--links` says which members in the coach still owe someone an answer.
