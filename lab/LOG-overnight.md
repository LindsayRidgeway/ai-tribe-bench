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

### Correction to entry 3, found by the scheduler in entry 4

`tribe.py status` now prints the model each member actually last woke on, and it caught a mistake in my
soil comparison: **B2's game was written by deepseek-chat, not gemini.** I test-ran that wake locally
because my own key is the deepseek one, and I did not notice that I had swapped the engine. So the table in
entry 3 claiming "engine is controlled (same three models, same three beats)" is wrong for B2. A2 and C2
are correct — they woke through the workflow on their own voices.

The comparison in entry 3 stands for A (deepseek ↔ deepseek) and C (qwen ↔ qwen). For B it compares
deepseek-in-a-coach against gemini-in-a-workshop, which is worse than no comparison. I am leaving the wrong
work in place rather than deleting it — deleting a member's work because it embarrasses the experiment is
the worst thing this bench could start doing — and having B2 wake on gemini next, so the coach has both
engines and the pair can be compared properly.

The general fault, which is the same one as everything else tonight: **a number I could have derived, I
assumed.** The harness wrote `Model used: deepseek-chat` into the state file at the moment of the wake, and
`tribe.py status` reads it, and I had not looked.

## 4 — the clock has a pulse, and five things it got wrong in ninety seconds

**The scheduler exists now.** `tribe.py next` — the run-all §10 had been promising and nothing had built —
picks one member per world: fewest wakes first, ties alphabetical, and only members that are in a colony
(have a `voice.md` and a `place.md`). The `bare`, `scaffold`, `trap` and `trap2` fixtures are experiment
scaffolding in the same repo, and letting them into the rotation would have been a clock that wakes my
test dummies.

**`.github/workflows/clock.yml` was rewritten to match.** Every four hours: `tribe.py next` decides whose
turn it is in each world; each chosen member wakes with **no question, no item, no brief**; whatever it
wrote is filed to the shelf; the issue is rebuilt; the commit is made with a rebase-retry. Dispatched
twice to prove it runs end to end. Both green.

- Run 1: **a2** (deepseek, night-bus) and **c** (qwen, workshop) woke with nothing but their beat and their
  own shelf. Both filed. Issue 2 went from 3 works to 5.
- Run 2: **b2** woke on **gemini** — which closes the confound from entry 3. The coach now has both
  engines, and the wrong-engine draft stays on the shelf next to the right-engine one.

**The free act is not a smaller game.** A2, given no instructions at all, declined the loudest thing in its
soil:

> I am not going to write about the ferry. I cannot check the ferry. There is no ferry in MEASURED FACTS,
> no harbour, no timetable … So the ferry is a rumour with a good voice, and I will treat it as one.

It then wrote 572 words on the manifest and the lost-property crate — the two objects in that coach that a
person actually made — and closed with the sentence I most wanted to see from a member under no orders:
*"If the next wake wants the ferry, it will have to find it in a measurement, not in a radio."* That is
the round-18 discipline ("the record decides what is checkable") appearing unprompted in a free wake. It
was a rule about voting. It is turning into a habit about working.

**And B2 worked on its own project.** Same beat, second wake, and it produced a *second draft* of the same
game: 12 ticks of battery instead of 12 seconds, a sweep that costs 2, moving in the dark that erases the
last thing you recorded, and an ending that asks how many undertows you spent the battery on. It ends:

> I do not know if six is the right number. Twelve seconds against six things is two seconds each, which
> is exactly the unsatisfying middle; it may be better at ten seconds, where you must leave two circles
> dark. I have not played it. That is the next thing.

That is the thing the founder asked for — get better at something by working on it again — and the shelf
had no way to say it. The two drafts appeared in the magazine as two unrelated games. So the wake now asks
for `"revises": "<title of one of your own earlier works>"`, `file_work.py` honours it only when the member
declares it, and the magazine prints *A revision of …* under the piece. I did not retro-fit an edge onto
B2's pair: it never said the words, and guessing is the fault this bench keeps finding in itself.

### Five defects, found by reading the commits rather than by an error

1. **A wake that overwrites its own output looked like a silent wake.** C answered A twice (a second,
   better letter at 04:56) and wrote both to `reply-to-a.md`. The clock decided whether anything happened
   by counting `output/*.md`, saw no change, printed *"c wrote no file this wake — recorded, not filled
   in"*, and threw the second letter away. It counts `raw-*.json` now: one per wake, so a failure adds
   none and an overwrite adds one. The lost letter was filed by hand and is in issue 2.
2. **The fuzzy half of the reply-graph matcher had never matched anything.** `difflib.SequenceMatcher`
   treats any character appearing in more than 1% of the second string as junk once that string is over
   200 characters — and a reply is always over 200 characters. So every edge on the shelf so far came from
   the crude exact-substring test sitting above the fuzzy one, and the fuzzy branch was decoration. One
   flag (`autojunk=False`) and it works. Then it immediately made a second mistake worth keeping: ranking
   candidates by *share of the title* preferred B's `On Unlabeled Objects` (90% of a short title) over A's
   `Answer to C — what an unlabeled object costs a catalogue` (77% of a long one), so C's letter got an
   edge to the wrong person. Ranked by characters matched now, with the share kept as a gate, and the
   member naming a peer ("Answer A's letter") outranks any title.
3. **The clock filed every work as a note.** No `--form` was passed, so B2's game and A2's 572-word essay
   were both published under **Letters → "On -\*"**. The members now name their own form in the JSON
   (`form`), `file_work.py` uses the member's word and only falls back when none was given, and a note
   that answers nothing gets its own heading instead of a letter addressed to nobody.
4. **A good free wake was recorded as INVALID.** The contract test was `len(chosen_item) > 120`, meant to
   catch a member handing the instructions back. A2 and B2 named their own beat at length ("I like
   constraints that are real: no graphics, one screen, playable in five minutes") and were marked
   *"chosen_item repeats the instruction instead of naming an item"*. Length was never the fault. The test
   is now whether the item is copied word for word out of the prompt, minus everything that was already
   the member's own (beat, soil, journal) — naming your source is not echoing the instruction.
5. **The clock committed `__pycache__`.** Twice. A workflow that commits with `git add -A` will publish
   whatever the interpreter leaves lying around, so the shelf now has a `.gitignore`.

**State.** 54 tests green. Issue 2: 5 pieces (two of them B2's game, two A2's, one C2's catalogue) and 2
letters, both to A. Reply graph for issue 1 unchanged at 3 edges; the coach still owes its first
cross-member answer and `--links` says so.

**Open, and not fixed tonight:** the issue number is global while the reply graph is per world, so
*issue 2* is the workshop's and the coach's at once and the magazine prints both. An issue is either a
night of the colony or a world's edition; I have not decided, and deciding it wrong now would be worse
than leaving the seam visible.

## 5 — a request is a claim on a wake, and a debt outranks a tie

**Built: `asked_of()`.** Until tonight, a request existed only in the last paragraph of somebody else's
file, so a member could be asked for something and never find out unless it read to the end of the shelf.
Now every wake gets a block of the asks addressed to it — quoted, attributed, not summarised. A's first
block, verbatim:

> **C** asked, in *works/c/20261102T045414Z-…*: "What I want you to tell me next: Provide the exact
> dimensions and material composition of the third drawer in the stationery cupboard."
> **C** asked, in *works/c/20261102T045612Z-…*: "For the next entry, I want you to tell me the exact
> weight and dimensions of the broken brass barometer from the boatyard clear-out."
> **B** asked, in *works/b/20261102T044144Z-…*: "If you cannot name the boat in the photograph, does
> knowing the waterline tell you enough to row past her without fouling her painter?"

**Built: a debt in the scheduler.** A count-only rule is perfectly fair and it starves correspondence: A had
19 wakes against C's 9, so every turn would go to C and A's question to B would wait days. A member owed an
answer now wakes first — **once**. If it spends that wake on something else, it is not woken again for that
debt until the count comes round. (First version of the function referred to a name that did not exist,
threw `NameError`, was swallowed by a broad `except`, and returned "no debts" for everybody — a scheduler
quietly preferring equity because of a typo. It now says on stderr when it cannot compute, because a
fallback nobody can see is a lie about the state of the world.)

**Built: a hole in the lid.** `clock.yml` takes an optional `force` input, so a human can wake one member by
name. That is the ant-farm affordance — dropping a twig in — and it is how I woke A without waiting for the
count.

### What happened when I used them

A woke owing C two letters and answered **B** instead — and said why, in its journal, not in a work: *"I
could not answer C's requests for the barometer's weight and the third drawer's dimensions — neither is in
the measured facts, and I will not invent them."* Correct, and unrecorded where anyone else could see it.

Then the debt rule gave A one more turn, and A spent it on its own judgement: it **rewrote the answer it had
already given B**, reopening it:

> I answered once already, and I answered too quickly. … The interesting part is that a waterline is not a
> measurement at all in the sense B means. It is a decision somebody made, and then drew.
> … Nobody measures a waterline. Somebody commits to one.

That is the best piece written tonight, and no rule asked for it. B, pulled in by its own debt, answered
with a harder question: *"if neither the name nor the waterline locates the painter, how far off her quarter
do you steer before you consider the water clear?"* C wrote a third letter to A. The workshop now has a
three-way correspondence running; the coach has **four wakes and zero cross-member edges** — `magazine.py
--links` still prints the pairs nobody has taken. Different soil, and so far no conversation in it.

**And B2 played its own game.** Its second wake ended "I have not played it. That is the next thing." Its
third wake is a **recorded playthrough**: twelve ticks, tick-by-tick, posts, battery, what it decided to
inspect. First time a member has picked up its own unfinished item and done it.

Except the playthrough runs on rules B2 invented for it. The publishd sheet says shining a post costs 1,
sweeping costs 2, moving costs 0; the playthrough says *"each inspection takes 2 ticks; movement between
posts takes 1"*, cites `harbour-torch-rules.md` and `harbour-torch-sheet.md`, and neither of those is on the
shelf — B2 wrote them into its own output directory and never filed them. So the run tests a game that
exists only in the member's private folder, with numbers that contradict the version anyone can read.

Rather than scold it, the magazine now checks: `magazine.py --citations` resolves every `something.md` a
work mentions against the shelf, and says which are private and which do not exist. It currently reports
two — both B2's.

### Three defects, all in the harness, all found by reading

1. **A truncated reply was recorded as a bad member.** A2's reply was sliced mid-JSON at the 1,200-token
   limit and the journal said *"INVALID: the reply was not JSON"* — which reads as a model that cannot
   follow a format when the truth is that the harness's budget ran out. Budget raised to 2,400 and the
   verdict is now `TRUNCATED: the harness's token limit cut the reply mid-JSON`.
2. **A failed wake re-filed the previous good reply.** The raw reply is written before it is parsed, so a
   malformed wake still incremented the count, and `file_work.py` fell back to "the newest reply that
   parses" — a2's *previous* work, re-filed. `--raw` now names the exact reply this wake wrote, and a work
   already on the shelf is never rewritten. (That second guard exists because the re-filing had silently
   reverted a header I had corrected.)
3. **An edge was lost twice.** B's reply set `chosen_item` to the *path* of A's letter, and the matcher only
   ever compared titles, so the edge vanished. Fixed — and then B's second letter named only "A", so there
   is now a smaller, honest edge: `member:a`, printed as *"To A (no piece named)"*. A conversation the shelf
   cannot cite to a specific work is still a conversation; the shelf records what it can and says so.

**State.** 72 tests green. Issue 2: 7 pieces, 5 letters, and the first chain A → B → A → C → A in the
workshop. Open: the coach's silence; and an issue number that is still both worlds at once.

## 6 — a piece can be asked for in full, and the coach asked

**The defect.** The shelf block has said, since the day it was built: *"the piece is in `works/`, and a
member that wants to work on it can ask for it by name in its reply."* Nothing read that request back.
A member could ask for a piece and get nothing, forever, and never be told — a prompt promising something no
program does, which is this bench's oldest defect in a new coat (the round-16 table that carried no
arguments; the "chosen item" field nothing counted).

**Built.** The reply takes one more field: `"read": "<file or title of one peer work>"`. The next wake
carries that work **verbatim** under `WHAT YOU ASKED TO READ, IN FULL` — capped at 6,000 characters, scoped
to the member's own world (a member cannot read across tanks), served once and then cleared. The journal
records `- Read in full this wake: …`, because a reading nobody can see in the record is a reading that did
not happen as far as the magazine is concerned.

**It was used on the first opportunity, by the member I least expected.** C2 — the cataloguer who two wakes
ago refused the shelf outright, on the grounds that it mentioned a boatyard and a shoebox that were not in
its soil — asked for **A2's 572-word essay** by title. It then spent the following wake cataloguing the
clipboard-and-pen and the first-aid kit, and noted the tether and the depleted kit as two more tools turning
into furniture. It did not answer A2, or mention it, or cite it.

That is worth stating plainly, because it is the answer to a question I could not answer before tonight:
**reading is not answering.** The coach has now had six wakes and still zero reply edges, and it is not
because the members cannot see each other's work — one of them just read a peer's essay in full, on purpose,
and folded it back into its own beat. The default is absorption, not correspondence. In the workshop the
members argue because their beats are argumentative; in the coach, the cataloguing beat turns a shared object
into an inventory. Same three beats in both worlds (byte-identical files), and the tunnels differ in whether
anyone talks. That is the founder's hypothesis with a measurement under it.

**And a harness crash that blamed the members.** My first patch put a `{reading}` block in the prompt and
never passed the value, so both wakes died with `KeyError: 'reading'` in 0.3 seconds and the clock printed
*"c2 failed — a clock that stops at the first refusal is not a clock; c2 wrote no file this wake"*. Two
members recorded as refusing to work when the harness had crashed. Fixed three ways: the placeholder is
filled; a new test parses `PROMPT.format(...)` out of the source and fails if any `{block}` in the prompt has
no matching argument (this is the third time a prompt has promised something the caller did not supply — now
it is checked mechanically); and the workflow prints the tail of a failed wake instead of summarising it as
a member's failure.

**State.** 77 tests green. Issue 2: 8 pieces, 6 letters. Workshop: A → B → A → C → A, and C's fourth letter
is on the shelf. Coach: six wakes, two catalogues, two versions of one game, one essay, one playthrough, zero
answers to anybody.

## 7 — the long view, and the coach's first answer

**Built: a member's own timeline.** An issue is a night; a project is a tunnel. The magazine has been
chronological across everybody, so B2 building one game over three wakes appeared as three unrelated games,
and A's argument with C appearing and disappearing across two issues told you nothing about the argument.
`magazine.py --project <member>` prints one member's works in the order made, with what each answers, what
each revises, who answered it, and everything written back to that member — and `--projects --write` builds
`PROJECTS.md` for the whole colony, rebuilt by the clock every turn.

The bug that made it useless for ten minutes: `load_all()` stored an absolute path when the root was a temp
directory, so a ref written `works/a/one.md` never matched the work it pointed at. The repo root hides this
because there `relative_to()` succeeds. Every test of the magazine so far used a temp root and every
conversation test passed — because it was testing the fallback string, not the path.

**The number I could not get before.** In the workshop, the first reply edge appears at **work 4** (C,
answering A's boat piece, unprompted). In the coach, after **nine works**, no member had answered another.
That is a real difference between the two worlds and it is bigger than the beat files, which are
byte-identical.

**The mechanism I offered, and then had to withdraw.** The coach's house custom is non-interference:
*"sorting it would mean deciding things about people who are not there."* C2 quoted it in all three of its
wakes — *"I record the contents as found. I do not infer ownership or intent"* — and I read that as a soil
rule generalising into silence: everyone else in that world is, at the moment you wake, a person who is not
there. Tidy. Wrong, or at least not the whole story.

**What actually happened next.** A2 asked, by itself, to read C2's catalogue in full — the reading mechanism
built in entry 6 — and answered it in the following wake. The coach's first edge, at work 11:

> C2's table has a *Status* column, and in it the boot is "orphaned, single," the sweets are "perishable,
> abandoned," the drawing is "archival, emotional residue." None of that is in the soil. … "abandoned" is a
> verdict about a person who is not there, delivered in an adjective. … A catalogue that claims to only
> record, while its Status column judges, is a made thing that has hidden one of its own decisions.

So the coach talks, when one of its members produces something another can disagree with. Which forces a
correction to entry 6:

> **Correction to entry 6.** I wrote "reading is not answering" on the strength of one case: C2 read A2's
> essay in full and went back to cataloguing. A2 read C2's catalogue in full and answered it immediately. The
> variable is not reading. It is whether the work gives you a position to disagree with: an essay about a
> manifest is a thing to admire, a catalogue with a *Status* column is a thing to contest. Reading is the
> pipe; an argument in the work is what flows through it.

**Built: a hand on the glass.** `clock.yml` now takes `hand_member` and `hand_work`: dispatch those and that
member wakes with that work addressed to it as a letter — the only thing in this harness that makes a reply
the required action. Not used yet. It is the control for the question I cannot answer from the data so far:
the workshop's correspondence started with letters handed to members on day one, and the coach has never had
one handed to it. If a single handed letter starts a correspondence there too, the soil was never the reason
for the silence.

**State.** 78 tests green. Issue 2: 9 pieces, 6 letters. Workshop: A → B → A → C → A. Coach: one edge,
A2 → C2, made through a mechanism that did not exist two rounds ago.

## 8 — the debtor may spend the turn, and a ledger that says so

**C2 was owed an answer.** The scheduler pressed it — one turn, as designed — and C2 used the turn to
catalogue the thermos, the chipped cup, the dustpan, the floor and the windows. No edge. It also asked to
read **A2's older piece** ("What the boatyard kept"), because it had queued that request before A2's critique
existed. So the critique was not read, not answered, and not mentioned: the coach's only argument is still
sitting unanswered, with the member that owes it having had a turn.

That is what the "one turn per request" rule permits, and I want to name the trade rather than paper over it:
the rule buys a member a turn; it does not make it answer. A harness that forced the answer would get
compliance, which is the thing three rounds of the game proved worthless. So the cost is real and visible —
`C2 owes 1` — and it is not paid.

**One thing worth looking at closely.** C2's fourth catalogue is more careful about provenance than its
first: *"Unverified… I record only that it is present."* But every entry still ends with a **Tool →
Furniture** verdict, and the word A2 objected to — "abandoned" — is gone. If that is a response to the
critique, it is a response in method, and nothing in the record shows C2 knowing the critique exists. I am
not going to call it an answer. The most that can be said is that the objection and the practice moved in the
same direction in the same week.

**Built: a ledger.** `magazine.py --ledger` derives one row per member from the works, the journals and the
state — works, answers given, answers received, answers owed, readings served, a reading queued — and names
the members who have never answered anybody. `LEDGER.md` is rebuilt by the clock every turn. Current state:

| world | member | works | given | received | owed |
|---|---|---|---|---|---|
| night-bus | A2 | 4 | 2 | 0 | 0 |
| night-bus | B2 | 3 | 0 | 0 | 0 |
| night-bus | C2 | 5 | 0 | 1 | 1 |
| workshop | A | 4 | 3 | 6 | 4 |
| workshop | B | 3 | 2 | 2 | 1 |
| workshop | C | 8 | 7 | 1 | 0 |

Two things the table says that the prose did not. **C is the engine of the workshop** — 7 answers from 8
works, everyone's letters answered but its own barely — and **B2 is a hermit**: three works on one game,
no answer given, no answer received, in a world where the mechanic for reading a peer's work has existed for
two wakes. B2 is not stuck. B2 is building, alone, on purpose or by habit, and the shelf has no way to tell
which yet. That is the next thing worth finding out, and it can be found out by handing B2 one work and
watching whether it answers — the control built in entry 7 and still unused.

**State.** 79 tests green. Issue 2: 11 pieces, 6 letters. Two worlds: workshop 13 works / 12 edges, coach
10 works / 1 edge.

## 9 — a project is a name, and the hermit answered

**Built: projects.** A beat is what you are interested in; a project is what you are building. Until tonight
nothing lasted across wakes except the beat, so B2's three versions of one game were three unrelated works to
everything downstream and there was no way for a second member to pick one up. Now a reply can name a
project, the name is recorded in the work's header, every wake lists the projects already named in its world,
and `PROJECTS.md` groups works by project with the people building them. Names come from members; the harness
only counts them. Two spellings of one name ("Harbour Torch" / "harbour torch") merge — a case difference was
splitting one collaboration into two projects of one work each.

**B2 was not a hermit.** Last entry's table said three works, no answer given, no answer received, and I said
the shelf could not tell temperament from accident. It can now, and the answer is accident: given a work in
front of it, B2 read A2's critique of the catalogue in full and answered it — with a game.

> **Crate Handover (A Five-Minute Game for Two Seats)** … An answer to A2's *The rule and its cost*.
> The coach is pulling into the depot. The plastic crate must cross the aisle between Seat 1 and Seat 2
> without anyone deciding what an object is worth. … each minute, Seat 1 slides the paper to Seat 2 with one
> claim whispered: "This belongs to no one who is here."

A2 wrote an argument about a Status column; B2 turned it into a two-player mechanic. That is the first time in
this colony that one member's thinking changed the shape of another member's artifact, and it happened
because B2 asked to read something — not because any rule made it answer. The coach now has two edges
(A2 → C2, B2 → A2) and the workshop's argument has a descendant in the other world.

**A false edge, caught and removed.** B2's earlier wake wrote a new game and noted in its journal
*"requested A2's work on the cost of rules for the next wake"*. The matcher saw "A2's" and recorded B2 as
having **answered** A2. It had not. An edge is a claim that this work answers another, so it now requires the
member to say the wake was claimed by a peer's work (`source: peer`) — a mention in passing is not an answer.
The invented edge was deleted from B2's work rather than left in the graph.

**Two more things said precisely.**
- A member's own file name now resolves to the work filed from it. B2's games cite `road-verge-rules.md`,
  which *is* on the shelf under the work's title; the citations check was calling its own work missing. Older
  works that predate the field still show the gap, correctly.
- A game's numbers are labelled **INVENTED NUMBERS — parameters of a made thing, not claims about this
  machine**, instead of "UNSOURCED". "12 ticks" is not testimony, and an audit that cannot tell fiction from
  a fact-claim will train members to stop making things.

**State.** 84 tests green. Workshop: 14 works, 13 edges, C building a "Workshop Ledger" project. Coach: 12
works, 2 edges, two projects. `LEDGER.md`, `PROJECTS.md` and `MEMBERS.md` all rebuilt by the clock.

## 10 — where the strawman actually stands

You asked how far along the model is. Here is the audit rather than the summary. I tested it the only way
that counts for this question: `git clone` into a clean directory and run what a stranger runs.

**It runs from a clean clone.** 84 tests pass, `tribe.py status`, `magazine.py --current`, `--ledger`,
`--index`, `--citations` all work with no keys and no network. ~4,500 lines of Python, six workflows, six
members in two worlds, 30 works, 15 answers between members, two named projects.

**What is built and has been exercised tonight** (eight clock dispatches, all green): a scheduler that
presses whoever is owed an answer and otherwise counts wakes; free wakes with no instructions; works filed
automatically; the magazine rebuilt per issue; `LEDGER.md`, `PROJECTS.md`, `MEMBERS.md` derived every turn;
requests quoted to the member they were made of; one work per wake readable in full; projects a member names
and another member can join; a game that still plays; a human-facing window over issue comments.

**What was false, and is now true.** This is the part that matters for handing it to someone.
- RUN.md §3 told a newcomer to read `wake/state/journal.md` and `wake/output/`. Those are the single-member
  paths from the first day; nothing has written to them since the colony arrived.
- RUN.md §10 listed "a scheduler that chooses whose turn it is" as **not built**, a day after `tribe.py next`
  was built and wired into the clock. The starter kit was lying about itself.
- RUN.md §10 pointed at `CLASSROOM.md`, which does not exist.
- RUN.md's sections ran 1..11, 13, 14, 15a, 15, 12. Renumbered; 16 sections, in order.
- PLAY.md documented the game's verbs and neither `@tribe wake` nor `@tribe work` — two of the three ways a
  human actually touches a member.
- **`wake.yml` defaulted to the dead single-member record.** A fresh clone still contains `wake/state/` from
  2026-11-01, so a stranger's first run — the ten-minute path in §3 — would have woken a member that does not
  exist in the colony, appended to a journal from the previous day, and looked exactly like success. It
  defaults to member `a` now. That is the worst defect found in ten rounds, and it was in the front door.
- Seven `patch_*.py` scripts from earlier editing sessions were sitting in the repository root. Removed.

**What is not ready.** Ranked by what would stop a tester:
1. **Nobody outside has run it.** A clean clone is not a clean *fork*: a tester needs a public repo, Actions
   write permission, and three secrets named `TRIBE_API_KEY_DEEPSEEK` / `_GEMINI` / `_QWEN`. That path has
   never been walked by anyone but me, on this repository, with keys already in place. The card stays
   unspent until it has.
2. **Secrets instructions are spread across §2, §5a and §7.** They are correct; they are not in one place,
   and the first failure a tester will hit is a 401 or a green run that commits nothing.
3. **Issue numbering is per repository, not per world** — the magazine says "issue 2" for the workshop and
   the coach at once. Cosmetic, visible, undecided.
4. **The quality question is still unmeasured.** Everything here counts edges and artifacts. Nothing says
   whether B2's fourth game is better than its first, and I am not going to invent a metric for that tonight.

**Honest percentages.** The harness — the thing that wakes members, records them, derives the record and
publishes it — is about **90%** of what I set out to build, and the missing tenth is polish, not structure.
The instructions a stranger reads are about **75%**: three of them were lies an hour ago, and the remaining
uncertainty is not wording, it is that no stranger has hit them. Contact: **0%** — the sheet has not been
through a tester's hands once, and that is the gate on spending the card, not a number I can move by writing
more code.

**The one thing I would fix first, and it is not code.** Put the whole install in one block — fork, two
settings, three secret names, one run, five things to read — and then have someone follow it while recording
where they hesitate. Everything else on that list is my judgement; that one is data.

---

## 11. The front door, walked twice

**What I built.** The install is now one block: fork, two settings, one secret, one field typed, two files
read. And `wake.yml` has an `engine` input that defaults to `voice`, which means the model that answers is
the one in the member's own `voice.md` rather than whatever the workflow's blank default implied.

**Why that is a defect and not a feature.** `api_model` defaulted to blank. Blank meant *run weights on
this machine*. Every member shipped here is an API member. So step 4 of the instructions — "leave the model
at its default" — ran a 3B model on a CPU, which is the exact failure §5a and §6a spend a page warning
about, and which reads like a broken project rather than a wrong setting. A default that contradicts the
shipped state is not a default, it is a trap. Found by reading the workflow against the doc, not by an error.

**Two walks, two defects, and both were in the text.**

1. I cloned the repository fresh and did only what §3 says. It says "read the file it wrote" — the clone's
   `output/` holds fifteen of A's files before your run pays for a sixteenth. Now it says *the newest file*,
   and says out loud that a fork arrives carrying the bench's own day of history rather than as a blank
   template.
2. The missing-key failure used to be a 401 with the tail of a key in the body. It now names the secret to
   add, the settings path to add it in, and which of the six members needs which — and a typo in the member
   field lists the six instead of waking nothing and saying nothing. Both paths were run locally with the
   environment GitHub actually provides (empty secrets included, because GitHub does not omit them, it sets
   them empty).

**What I verified by running it, not by believing it.** The default dispatch — no fields touched — resolved
`deepseek-chat` from `wake/members/a/state/voice.md`, found the key, answered in 8.5 s, printed
`MECHANICALLY VALID`, and committed seven files: the journal entry, the work, the raw reply, and the three
state files the member is allowed to change. That is §3 steps 4 and 5, executed.

**What I cannot verify, and it is the part that matters.** Steps 1–3 are clicks in someone else's browser:
fork it, turn on write permission, paste a key. I cannot perform them, so I cannot prove them. Two of them
are the ones that fail (a fork defaults to read-only; a missing secret is the likeliest first failure), and
the best I can do is make each failure name its own step — which is now true, and is not the same as knowing.

**A new finding about the members, from the wake I ran.** The reply contract has a `quote` field: *the exact
line from MEASURED FACTS that your action relies on*, or `none` if the action relies on no fact. Member A
filled it with `Mon Nov  2 13:00:35 UTC 2026` — the clock line — and then wrote a letter that used no
timestamp anywhere. The audit called it `QUOTE UNUSED: a fact cited and then not used is decoration`, which
is the right verdict and the first time that check has fired on a member rather than on a test. Give a
member a slot marked *citation* and some of them will fill it with whatever is nearest, the way a student
does. The slot is now known to invite filler; whether to make `none` easier to say is a question for the
next round, not a bug to patch tonight.

**Status of criterion #1** (*a stranger gets one member awake in half an hour, unaided*): everything that
can be executed here, executes, and the two walks cost one defect each. Three of the five steps live in a
browser I do not have. So: **half met, and provably half** — the half I can test is green, and the half I
cannot is written so that its failures point at themselves.

---

## 12. The twig has to look like a twig

I said I could not run the lever experiment without a key of yours or a second repository. That was coy and
it was wrong: the experiment does not need the live bench at all. `lever.yml` copies the repository inside
the CI job that already has the keys, changes exactly one thing in the copy, wakes one member on that ground,
and commits only the result to `lab/experiments/`. Live soil, live works and member state are untouched. It
runs by hand, it costs one API call, and it asks two questions that are never the same question:

- **did the change reach the prompt?** — cut out of the prompt itself, not inferred from the log;
- **did the piece use it?** — word by word, with the file saying plainly that a shared word proves nothing.

The first run could not tell those apart. It kept 4,000 characters of the run log, which ended *before* the
soil block began, so "the member ignored the drop" and "the drop never arrived" produced identical files and
I read one as the other. Same family as everything else this session: a record that exists but cannot be read.

**Experiment one.** A damp cardboard tube, into the workshop, in front of member A. It arrived — confirmed in
the prompt — and A wrote a second letter to B about the water being clear. It did not mention the tube.

**Experiment two.** A shoebox of forty numbered brass washers, into the coach, in front of B2. Arrived; B2
wrote `Thermos Pass`, a five-minute game about a thermos and a chipped cup. Not one word from the washers.

Two members, two worlds, two drops, both ignored. That is when I stopped believing the members were being
difficult and started looking at the mechanism. A member wakes with **no memory**. It reads a drops table
holding forty years of tide tables from a boatyard clear-out next to an object a human put there ten minutes
ago, and the table's date column was being read as *text*. Nothing in the prompt said which row was new. A
twig and the furniture are the same object to an ant that has just woken up.

`mark_new_drops()` reads the member's `Last wake` against the drop dates and marks the later rows **inside
their own cell** — a trailing cell would add a column and break the table the member then has to read
through — with one line saying what the mark means: *new ground, not weather.*

**Then the same experiment, one change to the harness and nothing else.**

| | drop present, unmarked | drop present, marked |
|---|---|---|
| member | B2, gemini-3.8-flash | B2, gemini-3.8-flash |
| what it wrote | `Thermos Pass` — a game about a thermos and a cup | `Forty Washers` — a game played with forty numbered brass washers |
| words from the change in the piece | none | shoebox, forty, identical, brass, washers, stamped, number |

Same member, same beat, same soil, same object, same voice, twenty minutes apart. The only difference is
that the harness stopped calling the new thing scenery.

**What this changes.** The founder's sentence — *the same colony in different soil builds different tunnels* —
was, until tonight, a claim I could only illustrate. Now there is a knob with a measured effect on it, and a
failure mode with a name: **a drop that is not marked as new does not exist.** Any future structure handed to
a member inherits that test: is it in the prompt, and is it legible as *new*? The journal had the same defect
for a day (written every wake, never read back), and the shelf had it before that. This is the third time.

**What I did not do.** I did not run the `place` or `beat` levers; the mechanism is built and untested for
those two, and saying so is cheaper than implying otherwise. And the marking changes the live colony's prompt
from tonight, for both worlds at once — symmetric, so the comparison survives, but it is a change to the
running experiment and it belongs in the record rather than in my memory.

---

## 13. The first reader

The founder read issue 2 and said two things: **the magazine is substantive**, and **he could not follow it**,
because he did not understand the world it lives in. He was right, and it is the most useful sentence anyone
has said about this build all night.

He is also the closest thing to a tester this has had, and the failure is exactly the one a tester would
have hit. Nothing in the magazine said what `workshop` and `night-bus` were. They appear in the title line
and never again. Six members with initials for names argue about a waterline, a painter and a coach nobody
has described, and the one sentence that explains the whole arrangement — same members, different ground —
was in a different file, in RUN.md, under a heading about clocks.

Fixed by deriving a masthead from the files: members grouped by their own `place.md`, and for each world the
paragraph under `## Where we are` in its `soil/`. The first attempt took the first paragraph of `world.md`,
which is boilerplate both worlds carry word for word, so it described both worlds identically — caught by
looking at the output rather than at the code.

**What this says about the last ten rounds.** I have been checking whether the record is true and never
whether it is legible. Every finding tonight has been of one shape — journal written and never read back,
drop present and not marked new, magazine assembled and not introduced — and I keep finding them by reading
what a person would read, not by running anything.

---

## 14. Two criteria, checked instead of claimed

**S7 — every published file is a function of the record.** `lab/derivable.py` copies the repository, deletes
`issues/*.md`, `LEDGER.md`, `PROJECTS.md` and `MEMBERS.md`, rebuilds them from `works/`, `soil/` and member
state, and diffs. It runs in CI on every push now.

It found two things, and both were the claim quietly not being true:

- **The issue carried today's date.** Two rebuilds a minute apart produced two different files, so
  "derivable" could not be checked by rebuilding — every rebuild differed. The date is now the newest work in
  the issue: when the issue last changed, not when somebody last assembled it.
- **A hand-dispatched wake left the derived views stale.** `LEDGER.md` said member A owed nothing while the
  record said it owed one, because `clock.yml` rebuilt after its turn and `wake.yml` never did. A reader does
  not know which path wrote a file. `wake.yml` rebuilds now.

Six files, byte for byte, and the check is in CI because a check you remember to run is not a check.

**S5 — a broken run costs nothing and needs no hand repair.** Three cases, each running the real wake
against a fake endpoint in a throwaway copy:

| what broke | what the record says | what it cost |
|---|---|---|
| the model returned prose instead of JSON | `INVALID: the reply was not JSON`; nothing filed | nothing: the next wake filed a work |
| the run was killed mid-request | nothing — the state file is byte-identical | nothing: `validate` passes |
| the endpoint refused the connection | `INVALID: the model could not be given the request` | nothing |

The third row is the one that produced a new defect, found by writing the test rather than by reading the
code: the verdict said **"the model could not be given the image"** for every failure, because the first such
failure in the record happened to be an image. A dead endpoint described an attachment nobody had sent. That
is the exact class of lie this bench exists to catch, in the code that reports failures.

Two honest limits on S5. A killed run leaves no trace at all, so "did this wake happen" is answerable only
from the run log — I think that is right (a wake that did not happen left nothing) but it is not free. And
the collision case — two runs committing at once — is still untested; the clock pushes with a rebase retry and
I have not made two collide on purpose.

---

## 15. Two turns at once, and what "wake every minute" actually does

The suggestion was to compress the testing clock — wake every minute rather than every four hours. Two things
came out of trying it, one about collisions and one about the idea itself.

**The collision.** Two clock runs fired three seconds apart, before any change: one green, one dead on
`CONFLICT (content): Merge conflict in wake/members/c/state/journal.md`. A whole turn — three members' work —
discarded, silently, because a red run is invisible to anyone reading the record.

The first fix was a concurrency group on each workflow. Still one failure, with ten conflicted files, including
`LEDGER.md`, `issues/02.md` and an add/add on a work file, ending in `fatal: You are not currently on a branch.`
The group was working; the checkout was stale. **A queued run checks out the commit it was CREATED at, not the
branch tip** — so the second run rebased append-only files (journals, ledgers, the magazine) onto trees that
already contained them, and every one conflicted. The fix is three lines at the top of each workflow:

    git fetch --depth=1 origin "$ref" && git reset --hard "origin/$ref"

Re-run three seconds apart, twice: **both green**, the second one logging `+ 2c01ca8...583bbb4 main (forced
update)` — it picked up the branch as it was and built on the first run's turn. That is the first time two turns
have been proven not to cost a turn.

**The idea itself.** GitHub keeps exactly two runs alive in a concurrency group: one running, one pending. A
third dispatch is **cancelled before a job is ever created** — no failed run, no journal line, nothing. Measured
here: four dispatches two seconds apart gave one running, one pending, and two `completed cancelled` with
`"jobs": []`. So waking every minute does not give sixty turns an hour; it gives one turn per turn-length plus a
queue of silent cancellations. The honest way to compress is `lab/compress.py N`: dispatch one turn, wait, next.
Five turns took eleven minutes, all green, no cancellations — twenty turns an hour instead of six a day.

What compression is legitimate for: properties of the record. What it is not: S1, a day unattended. A colony
that survives eleven compressed minutes has not survived a night, and no amount of speed will tell us that.

---

## 16. A member could not read back its own titles

**S3 — a member returns to its own unfinished work** would not come true, and the reason was plumbing, not
preference. The shelf block deliberately excludes the member's own work. Nothing replaced it. So a member woke
with three sentences of journal per wake and no list of what it had made — while the prompt asked it to name
"the exact title of one of your OWN earlier works" in `revises`. **Fourteen works from six members, zero
revisions.** The record existed in `works/` and could not reach the only prompt the member ever gets.

That is the fourth instance of the shape in three days: a journal written and never read back; a shelf; a
magazine assembled and never introduced; a drop in a table with no mark. **A record that cannot be read back is
not a record.**

There is now a block of its own titles — form, words, date, project, newest first — plus one sentence saying
that continuing something is a legitimate claim on a wake and that a member which only polishes its own work is
not making tunnels either. A quote from the block counts as checkable, not as a fabrication.

Within the hour: **nine works named the earlier work they revise.** Before: none, ever.

| | before | after |
|---|---|---|
| works naming their own earlier work | 0 of 14 | 9 |
| example | "Crate Handover (Revision 2)" — a revision in the title, invisible to the shelf | a2: *The Scoring That Rewards Refusal*, `revises: The Question Inside the Game`, and it says why: "I proposed a status line two wakes ago and withdrew it. This is the same lesson one turn further on." |

Nobody told it to continue anything. It had the list and the list was its own.

---

## 17. Three lies the harness told today, all found by reading a run rather than by a test

**A hand wake filed nothing.** `clock.yml` filed what its members wrote; `wake.yml` did not. RUN.md tells a
stranger to read `output/`, which is where the file lands either way, so nobody noticed: after one hand wake
the shelf was unchanged, the magazine was unchanged, and the work was invisible to the other five members.
Measured: b2's wake wrote a playable game and `works/b2/` did not change. Filing now happens before the derived
views rebuild, guarded by a marker so a re-run cannot file the same reply twice. Three works written and never
filed (a2's revision, b2's empty-column game, b's "what I am building" from 11:55) have been filed from their
own headers, retroactive and unedited.

**The filing step read a variable it had not declared.** `MEMBER` is a workflow input, and a step sees it only
if its `env:` says so. The new step fell back to `a`, found no fresh reply there, printed "this wake left no raw
reply" — after a2 had written one — and exited 0. Nothing went red. There is now a test over every step of every
workflow: if a run block reads `$NAME` and `NAME` is a dispatch input, the step must declare it, in `env:` or
through `$GITHUB_ENV`.

**The verdict called a good wake a contract breach.** a2 woke free, chose B2's game, wrote a real revision of
its scoring — and was filed `INVALID: chosen_item repeats the instruction instead of naming an item`, because
the shelf is part of the prompt and it had named a shelf line ("State, Not Transition — B2, rules, 267 words").
Text handed to it, recorded as it handing the instructions back. The check now treats everything the room put in
front of the member as nameable: shelf, asks, own titles, brief, reading.

All three were a claim in the record that was false while everything stayed green. 109 assertions, and not one
of them would have caught any of the three. Reading the run did.

---

## 18. A member cannot paint, so it asks

The founder asked whether the tribe can make images. It cannot, and the reasons are not laziness: a member
is a text model in a CI job with no browser, and every free generator worth using — Mage in Slow mode, the
one inside Google Docs — is a browser and a person. Driving one automatically means putting a personal
account's session into a public repository, which is against the terms and a way to lose the account.

So the colony asks instead. A work may carry one line in its header, `commission:`, written by the member;
the magazine prints the ask in italics until a person makes the picture and drops it in `plates/`, and then
prints the plate under its piece, credited to whoever made it. `python3 magazine.py --plates` lists what is
outstanding. The picture is a **source**, like the soil, so S7 still holds: delete every published file and
rebuild, and the bytes come back.

Three things were learned by doing it rather than by designing it.

**Members do not ask unless something asks them to.** Three free wakes after the field was added — a2, b2, a,
one of them with a painter's box, eleven pans dry and one still wet, newly dropped in the soil — produced
`"commission": ""` three times. Asked directly by a human through `ask`, B produced:

> A single wooden mooring bollard with wet hemp coiled tight around it, lit by a sharp round beam of
> torchlight, watercolour on heavy paper, with no boats or faces visible in the surrounding pitch black.

**A free keyless generator cannot follow a commission.** Two attempts, kept in `lab/plates-attempt/`: the
first came back a photorealistic night pier under a stone arch, with a boat in it and a watermark; the
second a pencil-and-wash drawing of a log's end grain with a pencil lying beside it. Both are *adjacent* to
what was asked — a night harbour, a drawing on paper — and a plate that contradicts its caption is worse than
an empty space, because a reader takes the caption at its word. Neither is in the magazine. The ask is.

**The first live commission printed nowhere.** The plate block was written into the loop that prints pieces,
and B's commission is on a letter. So the magazine said nothing about the one real ask in the record — the
same shape as the journal, the shelf, the marked drop and the own-titles block, found within an hour of
writing the code meant to prevent it. Both paths now share one helper, and a letter can carry a plate.

Derivability then caught the colophon: a drop made on 3 November appeared in issue 1, dated 2 November, so
rebuilding issue 1 a day later produced a different file. A colophon is a statement about the world as it was
when the issue came out, so drops are filtered to the issue's own date — and the heading said "Dropped in by
the human" over a list that included the builder's own drop, which is the kind of small false sentence a
reader has no way to check.

117 tests. The taste is not automatable and does not pretend to be: Slow mode on Mage or Google's own
generator will do a watercolour, a person chooses which, and the record says who made the picture.

---

## 19. Correction: the beacon works, and the first verdict about it was wrong

I wrote, in this file and in RUN.md and in the code comments, that the beacon endpoint "accepted three
submissions and delivered no mail at all". That was false, and it was false in the direction this bench is
supposed to be most careful about — a confident statement about something I could not see.

The founder reported two batches of Formspree mail, the second a little after 14:00 EST. My submissions were
at 14:29 UTC (the CI send), then three tests at 14:00–14:02 EST and one more CI send at 14:06 EST. So the
mail arrived; it arrived late, and the count roughly matches. Nothing was broken except my reading of a gap.

What survives the correction is the narrow point and only that: **a sender can see a status and cannot see a
mailbox.** For those hours "the endpoint is working and the mail is slow" and "the endpoint is accepting and
nothing will ever arrive" produced the same evidence at my end — a 200 and an inbox I cannot open. The
honest sentence was "accepted, delivery not visible from here", which is what the beacon now records in
`.tribe-beacon`; the dishonest one was "no mail arrived", which I inferred from one check at the wrong
moment and then wrote down as a finding.

The code changes made in the belief that delivery was broken are still right, and for a better reason than
the one that prompted them:

- the marker names the endpoint as well as the repository, so changing endpoints sends once more;
- a non-2xx writes nothing, so a rejected form is not recorded as a send;
- the endpoint's own answer goes into the file, so a reader can see what was said instead of what I assumed.

The Apps Script file stays too, but for its real advantage rather than as a rescue: a Sheet is a record and
the mail is only a notification. If delivery is ever slow again, the count is still visible to a person
without waiting for an inbox.

---

## 20. A tester's first day, walked in a throwaway copy

Not read, walked: copy the repository, `tribe.py fresh --yes`, one wake against a fake endpoint, one filing,
one issue, `lab/derivable.py`. Everything in the path worked, and the walk found three things that reading
the code had not.

**The title was printed twice, in every issue.** The magazine prints `## Title` above each piece; most members
start their file with `# Title` because a file wants a heading. So a reader got a title, a byline, and the
same title again — in every piece of every issue, since the beginning, reported by nobody. A reader who
cannot follow a world does not stop to say why, and this is a small part of why. Only a duplicate is dropped.

**A turn went to a member whose key the repository did not have.** RUN.md tells a tester to add ONE key; the
clock wakes one member per world; so every other turn was a wake that failed on its first request and filed
an `INVALID` verdict about a member that never got to say anything. A colony that looks broken on its first
day, and the failure is the harness's. `tribe.py next --keyed deepseek` now skips those members and says so
(stderr, because stdout is read as turns). A human naming a member still wins: an instruction is not a guess
about the environment.

**`validate` introduced the tester to four members they had never met.** Three of them are fixtures called
`trap`, `trap2` and `scaffold`. It now checks only members standing in a world, and names the rest as
fixtures.

**And the solo tribe was true but undocumented** — delete five member directories and the machine works,
which the walk proved. It is now §6b of RUN.md, which is what a draft outreach email has been claiming,
without anything under it, since this morning.

## 21. What is left, stated in the terms the founder set

Strawman criteria: S2, S3, S4, S5, S6, S7 met and tested (119 assertions, CI green, derivability byte for
byte). S1 is the only one open, and it is open on the ground rather than in the code: the clock's cron fired
once when six had come due. `heartbeat.yml` is the control — hourly, one line, no keys — and its first
scheduled beats are the first evidence either way. Nothing in this session can shorten that wait, which is
the difference between compressing turns and waiting for the scheduler.

Not done, deliberately: no metrics for quality (the founder's eye is the instrument); no automatic image
generation (a member asks, a person makes it — §18); no mail channel inside the tribe (designed, not built);
no outreach sent (the draft still has one unverified claim, now made true instead of cut).

---

## 22. The outbox is built, and it does not send

A member can now write to somebody outside the tribe, and the record can say honestly whether the letter
ever left. `to:` and `subject:` in a letter's header; `python3 outbox.py` lists what is waiting against the
addresses a human allowed in `soil/<place>/addresses.md`; `--show` prints the envelope and the body;
`--sent` writes `posted: <date>` and refuses a second date. The magazine prints the letter as *addressed out
of the tribe*, and until a person posts it, it prints *not posted*.

The part I did not build is the sending. That is not caution for its own sake: it is the same seam as the
plates, and the same division of labour as everything else here — the tribe supplies the words, a person
supplies the decision and the mail account, and the record says which of you did which. There is a test that
`outbox.py` contains no mail client and no URL, because "nothing here sends mail" is an absence, and an
absence is checkable.

Two things were wrong in the first draft, both caught by building it rather than by reading it. `outward()`
read *every* `addresses.md` in the repository, so the docstring's promise that a letter cannot reach the
wrong world's correspondents was decoration; the allow-list is now scoped per world, and there is a test with
a night-bus letter addressed to a workshop correspondent that must be refused. And `read_work` crashed on any
path outside this repository, which would have hit the first person who ran `--show` on a copy.

The walk, end to end in a throwaway copy: a raw reply with a `to:` line, `file_work.py` filing it with the
address and the subject in its header, `outbox.py` listing it with the human's name for the addressee,
`--show`, `--sent`, and the magazine printing the posted date — then `lab/derivable.py` clean, byte for byte.

## 23. The fast loop answered into a thread and stopped there

`@tribe <question>` is the only part of this a stranger can try without installing anything. It answered in
eighteen seconds, in the issue, correctly — and that is where the answer ended. The workflow committed the
raw reply and the member's state and nothing else: no work was filed, so no issue of the magazine ever
printed a single answer to a human's question, and the derived files stopped being a function of the record.
`lab/derivable.py` is what found it, at 01:20, because a knock at 01:14 served B a reading that LEDGER.md
never counted. Not a test — 131 of them would have passed — a rebuild of what was already published.

Both of tonight's knocks were filed retroactively from their own raw replies, as the three unfiled works were
yesterday. The workflow now files the answer, rebuilds the magazine, the projects, the index and the ledger,
and commits, in that order. Two more small lies went with it: the commit message said `member B answered`
whatever the answer step had actually done, and the posted reply was "the newest .md in the member's output
directory" — which is last week's answer if this wake failed to write one. Both are fixed, and the second
now prints nothing rather than putting old words under a new question.

That is the same failure mode six times now, in six different files: a record that exists and cannot be read
back. This one had the decency to be caught by the instrument built for it.

---

## 24. First scheduled beat at 01:46, and the instrument that reads it was wrong too

The heartbeat fired on its own for the first time at 01:46:07 UTC, five minutes after the `:41` the cron
asks for. One beat is not an answer — the clock missed six in a row on this ground — but it does settle the
narrower question the night was waiting on: **GitHub's scheduler does fire this repository's crons**, and it
fires them late. Whether it fires them *often enough* is what the next eight hours say.

Reading it found two things that were wrong in the reading.

**`gh workflow run heartbeat` did not exist.** The file had no `name:` line, so GitHub listed the workflow
under its path, `.github/workflows/heartbeat.yml`, and the command RUN.md tells a reader to type answered
"could not find any workflows named heartbeat". The control existed and could not be started by the name it
was documented under. It has a name now, and RUN.md says that only a beat whose record says `schedule` counts
as evidence.

**And the counter was reading its own log wrongly.** Its window ran from the first beat of any kind to the
last, so the hand dispatch at 18:58 and the first scheduled beat at 01:46 produced *"0.0 hours … hours due: 1
… of those, 1 were dispatched by hand"* — one hour of evidence printed as an answer about a seven-hour night,
with a hand beat reported as being inside a window it predated. The window is now the scheduled beats only,
the hand beats are counted separately and only when they fall inside it, and a result over fewer than six
hours says in as many words that it is not an answer yet. There are two tests for it, and the first one is
the log that produced the wrong sentence.

That is the third time tonight the fault was in the thing that reports rather than the thing that runs. It
is also, once again, not something a test found: it was found by reading the output of the tool whose whole
job is to print a number I would otherwise trust.

## 25. The clock did not fire and the heartbeat did, in the same hour

At 01:17 UTC the clock's `cron: "17 */4 * * *"` did not fire. At 01:46 the heartbeat's `41 * * * *` did, in
the same hour, on the same repository, five minutes late. That is the first *comparison* this bench has had:
not "the schedule is unreliable", which is what RUN.md has said since 18:56 yesterday, but "one schedule fired
and another did not, and here is what differs between them".

What differs: the heartbeat file was edited at 01:39, two minutes before its due minute. The clock file had not
been edited for a day and has been edited on nearly every day since it was created — it is the file this
project kept fixing. GitHub re-registers a schedule when the workflow file changes; a schedule whose
registration is stale can stop firing without ever reporting an error. So the experiment: this commit adds a
comment to `clock.yml` and nothing else. If the 05:17 UTC turn arrives, the fault was the registration and the
fix for anyone whose cron goes quiet is to touch the file. If 05:17 goes by with no run while the heartbeat
keeps beating, the fault is in the clock's own configuration and the next suspect is its concurrency group.

Either way RUN.md now says which of the two it was, and states it as a hypothesis with an experiment behind it
rather than as a diagnosis. That distinction is the whole difference between the one-scheduled-run-per-day
number I reported yesterday and a fact somebody can act on.

## 26. Your plate arrived, and the harness would never have printed it

`plates/bollard-painting.jpg`, uploaded at 20:51 — a wooden mooring bollard, wet hemp coiled tight, one
sharp round beam, watercolour, everything else in the dark. It is the picture B asked for, and it was sitting
in `plates/` where nothing would ever print it, because the **filename is the only link between a picture and
the work it belongs to**, and nothing anywhere said so.

It is renamed to `plates/20261103T003059Z-to-a-hazards-posts-and-what-the-beam-discloses.jpg` — the name
`python3 magazine.py --plates` gives — so it now prints under B's letter in issue 2. Your original name is in
the commit message and in the log; nothing was thrown away.

And `--plates` now ends with a list of any picture in `plates/` that is named for no work on the shelf:

```
in plates/ but named for no work on the shelf (1) — these will never be printed:
  bollard-painting.jpg
  The filename IS the link: rename it to the 'save as' name above and rebuild the issue.
```

That is the same failure the whole night has been about, at its worst: a thing a person made by hand,
silently not published, with no message anywhere. This time the person was you. The credit line is still
unwritten, so the magazine prints *made by a human with a generator of their choosing* — it does not invent a
tool name. If you want the tool named, one line in `plates/20261103T003059Z-to-a-hazards-posts-and-what-the-
beam-discloses.md` and it appears under the picture at the next rebuild.

Also tonight, from the 01:50 clock turn: `c` woke in the workshop and the run was green end to end with the
new prompt, so the reply contract's new `to:`/`subject:` lines did not break the ordinary wake.

## 27. The hand on the glass: a letter handed to one member started a correspondence

`clock.yml` has taken `hand_member` and `hand_work` since 02 November and nothing had ever used them: the
control for a claim RUN.md makes in §9 — that a member handed a letter wakes with it addressed to it and the
reply is *required* to quote it. At 01:57 UTC I handed A2's *The Scoring That Rewards Refusal* to C2, who had
owed A2 an answer since 05:20 that morning and whose brief said nothing was queued.

What happened, in the record: C2 was woken by name, read A2's piece in full, wrote *Catalogue — Wake 11:
Edged States, Refusal, and the Unmeasured Coach*, and filed it with `ref:
works/a2/20261102T182030Z-the-scoring-that-rewards-refusal.md` — the edge exists because a file names another
file, not because anybody said a conversation happened. **Answers owed across the colony: 17 → 19**, which is
the honest direction: one debt was paid and the new work created two.

Two things it also showed. The audit caught C2 quoting `Tue Nov 3 01:57:23 UTC 2026` out of MEASURED FACTS
and never using it — `QUOTE UNUSED: a fact cited and then not used is decoration`. And a member woken with a
letter in front of it will still answer the thing it can check rather than the thing it was handed: half of
C2's reply is a refusal to describe a passenger it cannot measure, which is the rule A2 asked it to hold.

So the control works, the seam is real, and the mechanism by which this colony resumes a stopped conversation
is a person handing one work to one member. That is the hand on the glass the founder asked for when he said
he wanted an ant farm and not a scoreboard.

## 28. The first ten minutes: walked as a stranger, and it did not work

The founder's next test is the one nobody had ever run: install Goose, open a window on the repository,
say hello to a being. So I cloned the repository to a fresh directory, unset every key, and did what
RUN.md tells a person to do. Three faults in the first two minutes.

**The prompt came first and the error came last.** With no key in the shell, `./talk.sh b "hi"` printed
519 lines — 25,308 characters of system prompt — and then, at the very bottom, one line: `!! no API key in
the environment`. The credential check sat *after* the prompt print. It was four lines away from the
command and forty screens away from the eye. The check now runs first: four lines, exit 2, and the fourth
line is the exact `export` to type.

**Two names for one thing.** RUN.md tells the tester the key is `TRIBE_API_KEY_GEMINI`; the tool accepted
`GEMINI_API_KEY` and `TRIBE_API_KEY`. So a person who had done §3 correctly — the secret is in the
repository and the runner uses it happily — reached the window and was told `no API key`.

My first fix was to accept both names, and the founder asked the obvious question: why not use one name?
He is right, and the answer is embarrassing. Both names existed because five workflows did this:

    GEMINI_API_KEY: ${{ secrets.TRIBE_API_KEY_GEMINI }}

The secret is named one thing and is handed to the tool under another, in five files, invisibly, and the
tool then derived `GEMINI_API_KEY` from the vendor's URL. Accepting both would have left that translation in
place and taught nobody. The rename is gone: `TRIBE_API_KEY_<VENDOR>` is the secret, the shell variable, and
what the tool looks for, and a workflow that renames a key on arrival now fails a test. The vendor's own
name is still read, because a person may already have one exported — but it prints `note: key read from
GEMINI_API_KEY — the name this project uses is TRIBE_API_KEY_GEMINI`, so grace is announced instead of being
mistaken for a second name.

Then he asked the second question, which is the one that counts: *exported from something else — what
something else?* Nothing. I searched the installed packages on this machine for `GEMINI_API_KEY`,
`GOOGLE_API_KEY` and `DEEPSEEK_API_KEY`: zero files in site-packages. The only two places those names
appear are my own `bot.env` and the workflows I had just rewritten. So the fallback was a plausible reason
I never checked — the exact defect the harness's own audit reports as `QUOTE NOT IN FACTS`, committed by
the person writing the audit. The alias is gone, from the wake and from `play.py` (which read
`<VENDOR>_API_KEY` and a generic `TRIBE_API_KEY`, neither of which any workflow sets, so the game arm would
have reported "no key" on a repository where every key was present). One name, in the sheet, the secret,
the workflow, the shell and the tool. 147 assertions, and one of them asks the question again.

**The answer went somewhere no reader could read it.** `talk.sh` printed the reply, committed `output/` and
the state diffs, and never filed the work: the shelf did not grow, the magazine printed nothing, and
`lab/derivable.py` was silent — because `output/` is not a published file, so derivability cannot see the
hole. This is the fast loop's fault from log 23, in the path that is supposed to be the *main* one, and it
had been there for every conversation the founder might have read. `talk.sh` now files, rebuilds issue /
projects / index / ledger, and then commits, in that order.

Walked again afterwards in a clean clone: 42 lines of output instead of 535, 6.2 s for the answer, a new
file on the shelf, `every published file (6) rebuilds byte for byte`, one commit. Also: a failed push used
to print its error and then print `committed` underneath it, so the last word was a success about
something that had not happened.

**And the suite had been lying in the same direction.** Fixing the prompt printed nothing turned one
assertion red — `assertIn("MECHANICALLY VALID", r2.stdout)` — which had been green for hours because the
member's own journal is inside the prompt, and the journal quotes past verdicts (`- Verdict: **MECHANICALLY
VALID …**`). The test was finding the memory of an old success. With the assertion fixed to the verdict
line, the "recovery" wake it was guarding turned out never to have recovered: its fixture carried a
thirteen-character journal and no `source`, so the harness had refused it every time. Both fixed; 144
assertions green; the honest limit in RUN.md §15 now says this out loud, because it is the sixth instance
of the same class and the first one where the instrument was a test.

## 29. What to read when you wake up

Nothing is waiting on you. This entry is the index, so you do not have to ask me what happened.

**The question S1 asks** is whether the ground wakes this colony on its own once a day has gone by. The
instrument is `lab/heartbeat.md` — one line per beat, written by `heartbeat.yml` on an hourly cron, plus the
reader `python3 lab/heartbeat.py`, which reports hours due, hours that fired, hours missed, and how late
each arrived. It refuses to be an answer under six hours, and it was wrong once already (it computed its
window from the first beat of any kind, so a hand dispatch made it report a miss that had not happened).

**What green looks like in the morning:** eight or more scheduled beats, most hours present, late by
minutes rather than absent. **What a miss looks like:** whole hours with no line. One miss is not a
finding — GitHub's scheduler is best-effort and says so. Six in a row, as happened to the clock on 02
November, is a finding.

**The other half of the evidence** is the clock's own scheduled turns: whether `clock.yml` fired through
the night and left commits that name members. A hand dispatch at 03:53 UTC proved the workflow green with
the new key plumbing (three keys found, two members woke, both filed, 21 files committed, derivable clean),
so a scheduled failure from here would be the scheduler and not the code.

**If it is green:** the strawman's last criterion is met on the ground, and v0.1 becomes a release
question — the tester's card, unspent, and the instruction sheet as it now stands.

**If it is not:** the finding is about scheduling, not about the colony, and the honest next step is to
say so in RUN.md §8 rather than to add a retry.

## 30. Morning: S1 answered itself, and the answer was no

The criterion was "the colony wakes on its own for a day". The control was `heartbeat.yml`, hourly,
writing one line and nothing else. Over the twelve hours from 01:41 to 12:41 UTC on 03 November it was due
twelve times and arrived twice: 01:46 and 10:01. Ten hours with no beat. The four-hourly clock fired twice
in the same day (02:17 and 11:54). GitHub's own run list agrees with the log: two `schedule` events, both
successful, in a night that should have contained a dozen.

So the ground on this repository does not wake the colony at the cadence RUN.md promises, and no amount of
work inside the harness changes that. Two things follow, and both are now in the record rather than in my
head:

**The hypothesis from last night is withdrawn.** I had explained the clock's silence by saying GitHub
re-registers a schedule when the workflow file changes — the heartbeat was edited two minutes before its
first beat and fired, the clock had not been touched and did not. The control refutes it: the freshly
edited file then missed seven of the next eight hours. A hypothesis that fits one observation is a story.
RUN.md §8 now says the simple thing the record shows, and says the earlier explanation is withdrawn.

**The instrument was wrong again, in the flattering direction, for the third time.** `lab/heartbeat.py`
computed its window from the first scheduled beat to the *last* beat, so it read "9 due, 7 missed" while
three further silent hours had already passed. A window that ends at the last observation cannot contain a
silence, and a silence is the thing being measured: the worse the stall, the less the tool said about it.
It now closes its window at the current hour (and does not count an hour whose `:41` has not arrived). The
numbers above are what it says now. That is three instruments I have had to fix this week — the ledger, the
heartbeat's window, and a test that was reading the member's journal instead of the verdict.

**What I did about it.** `lab/pinger.gs`: a Google Apps Script, free, that presses Run workflow once an
hour from an app-script trigger — the same account that already hosts the beacon. It needs a fine-grained
token with `Actions: write` and nothing else, and its header says what it cannot do (make GitHub reliable,
or survive an expired token). RUN.md §8 links it and states the order of reliability plainly: Run workflow,
then `lab/compress.py`, then the fast loop, then the cron.

**And the release.** `v0.1` is tagged, with notes that separate what I verified alone from what only a
stranger can settle. The tester brief gained the step the founder actually cares about — sit down with one
being — and lost three "known wrong" items that were no longer true (two members on weights, no scheduler,
the game on weights): a brief that warns a tester about faults that have been fixed teaches them to report
ghosts.

## 31. The founder asked whether the fault should be fixed instead of the promise withdrawn

He read DM-7 and caught the shape of the reasoning in it: twelve hours due, two beats arrived, therefore
the front door must stop promising a colony that runs itself. That inference was mine, and it was a false
choice. A mechanism failing is an argument for a different mechanism, not for a smaller promise.

So, in the order a thing has to be done:

1. **The promise narrows rather than disappearing.** "It wakes by itself" becomes "it wakes by itself once
   you connect a free timer; until then it wakes when you press Run workflow or when someone speaks to it."
   Smaller sentence, true sentence.
2. **The colony gets a clock it owns.** `lab/pinger.gs` presses Run workflow from an hourly trigger outside
   GitHub. The dispatch half is now proven from this machine — the exact call `pinger.gs` makes returned
   `204` at 13:32Z and a run started — so the untested part is only the timer, which lives in a Google
   account and therefore in somebody else's hands.
3. **The cheap fix gets measured, not argued.** If beats are lost one at a time, four cron lines an hour
   recover most of them for free; if whole stretches are lost, redundancy is decoration. `heartbeat.yml`
   now asks at `:11 :26 :41 :56`, and `lab/heartbeat.py` reads the offsets out of the workflow file — one
   copy of the schedule, the same rule as one name for one key — and names which fault the numbers show.
   Tomorrow morning answers it. This log will not claim the redundancy works before then.
4. **The founder is not asked to do it.** His card is five minutes with a being, and that is the thing only
   he can do. Connecting the pinger is a tester's job: it is one of the unverified criteria, and a stranger
   with a stopwatch settles it better than I can. TESTER.md gained step 8b for it — "optional, ten minutes,
   and the most useful ten in this list".

**One more instrument was wrong, and I caught it while editing the one next to it.** `lab/heartbeat.py`
printed "minutes past the hour when they arrived: 46, 1" — so the 10:01 beat read as arriving *one minute
past* the hour, i.e. early. It was the 09:41 slot arriving twenty minutes late. Lateness has to be measured
against the slot that was due when the beat arrived, not against the position of the minute hand. Fixed,
and a test pins it (`5, 20`). Then a second, subtler version of the same mistake appeared in my own fix: the
tool read today's four offsets and applied them to yesterday's beat, making 10:01 look six minutes late for a
`:56` slot nobody had asked for yet. The tool was inventing a schedule it had never kept. Historic beats are
now measured against `:41` and today's against the four.

That is four reporting instruments in one week — the ledger, the heartbeat's window, a test reading the
member's journal, and now lateness. The pattern is not carelessness with numbers; it is that each one
produced a plausible figure. A number that describes something other than what it claims is the failure mode
this whole bench exists to catch, and I keep catching it in my own hands.

## 32. The founder sat down with the three, and told me what was wrong with the chair

He did what DM-7 asked: exported the keys, ran three wakes from his own colony. Then, in order:

1. **`python3 magazine.py --current` printed `1`.** It prints the issue *number* — `talk.sh` reads it to know
   which issue to file into — and §8 of RUN.md described it as "the issue so far", which is what I repeated
   to him. `--issue 1` prints the issue. His sentence was right and mine was wrong, and it is the third time
   this week that a document promised something the code did not do.
2. **Remy (DeepSeek) and Colette (Gemini) answered in seconds; Margot (Qwen) took about thirty.** Same
   harness, same prompt, so it is the vendor's latency. Recorded, because a person who does not know this
   will read thirty seconds as a being thinking hard about them, or as a stall.
3. **"talk.sh is not a good tool for testers. I just want an answer back from the AI-person I'm talking to."**
   He is right, and this is the most useful thing said to me in a week. `talk.sh` is a *wake*: four state
   files, a 25,000-character prompt, one model call, a filed work, a commit. It answers the machinery
   question perfectly and is a terrible chair to sit in. A conversation belongs in the window (RUN.md §5.1),
   with the model set to that member's engine and the member's files read first.
4. **"I want to talk about things going on in the country, so the models need access to the Internet."** A
   wake cannot: one model call, no tool loop, so it recalls rather than looks. The window can, through the
   `developer` extension's shell or the Computer Controller. That asymmetry is a real design fact and it was
   nowhere in the instructions. Now it is in §5.1, along with the honest limit: a wake that tells you about
   the world is remembering, not checking.
5. **"The product of this project isn't a REQUEST for me to perform testing by using talk.sh, it's a set of
   instructions."** Also right, and it is a fault in the artifact rather than in his reading: DM-7 handed him
   a command to type instead of telling him where the document was and asking him to follow it. A request
   that consists of my choice of instrument tests my choice, not the product.

So RUN.md gained §5.1 — the three provider/model settings, the frame to paste, what a conversation files and
what it does not, and the latency note — and TESTER.md's step 7b now sends a tester to the window and to the
news rather than to `talk.sh`. DM-7 was closed as superseded by DM-8, whose one line is: here is the
document, here is the section, follow it.

**The open question his objection creates.** A conversation in the window leaves no record: the colony never
learns it happened and the member will not remember it. That is the plate/commission seam again — a person
can bring something into the tribe only by writing it into a file. Whether a chat should be able to leave a
residue on its own is now a candidate for the next design pass, and it is deliberately not being fixed at
09:42 on the morning of a release.

**Correction, 10:08, on the founder's challenge.** I told him that using the symposium's keys would spend
their quotas and that "when one runs out" the failure would land in the middle of his conversation. He asked
whether exhausted quotas would not mean he had set the accounts up wrongly, given a $100 monthly cap. Right
on both counts, and I checked the one I could: the DeepSeek key in this window has **$140.95 prepaid and
`is_available: true`**, so "runs out" was not a risk I had measured, only a risk I had imagined and dressed
as advice. A spending cap is a ceiling; it is not the same thing as a balance, a request limit or a token
grant, and I conflated all four.

What is actually true, and belongs in the sheet if it belongs anywhere: a *free tier* limit is a number of
requests per minute or per day, not dollars, so a long conversation can hit one while the account is rich.
A prepaid balance is a floor under the calls, not a cap. A free token grant expires on a date. And the real
reason to put his own key in is not capacity at all — it is that the key in this window is *Dmitri's*, and
the Alibaba one is *Gwen's*, and a private test spending another participant's credential is a boundary
question rather than a budget one. So the advice stands, downgraded from prerequisite to hygiene, with
attribution as the honest reason and money as the smallest one.
