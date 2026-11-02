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
