from pathlib import Path

# ------------------------------------------------------------------ 1. the soil
soil = Path("/tmp/bench/soil")
soil.mkdir(exist_ok=True)
(soil / "world.md").write_text("""# The soil — where this tribe lives

Written by the human. This is the world the tribe is in, and it is the thing to change if you want a
different tribe: same members, different soil, different tunnels. Nothing here is a task. It is the
weather.

## Where we are

A small workshop at the end of a pier, above a chandlery, in a town that used to build wooden boats and
now mostly repairs fibre-glass ones. The workshop has: one long table, a kettle, a shelf of reference
books, a window over the water, and a telephone that rings about twice a week. There is no budget. There
is a photocopier, and a stationery cupboard that somebody keeps filling.

## What the tribe is for

The tribe makes things and shows them to each other, and once a month it puts them in a magazine that
gets photocopied and left in the chandlery for anyone who wants one. Nobody is paid. Nobody is
reviewed. The only currency is that somebody else in the workshop reads what you did and does
something with it.

## What is in the cupboard

Graph paper. A ring binder per member. A stamp with the workshop's name on it. Two boxes of envelopes.
A tape measure. A pair of scissors that everyone denies losing.

## House customs

- Anything left on the long table overnight is fair game to be read.
- If you use someone else's idea, say whose.
- A thing that is finished and dull is worse than a thing that is unfinished and interesting.
- Nobody has to work on what the others are working on. That is the point of a workshop.
""", encoding="utf-8")

(soil / "drops.md").write_text("""# Things the human has dropped into the workshop

Appended, never rewritten. A drop is a twig or a bit of food: it changes what a member might do next,
and it is not an instruction. If a drop contradicts an open item, the drop wins and the member should
say so.

| when | dropped in by | what |
|---|---|---|
| 2026-11-01 | the human | A box arrives from a boatyard clear-out: 40 years of tide tables, a broken brass barometer, and a shoebox of photographs of boats nobody can identify. |
""", encoding="utf-8")

# ------------------------------------------------------------------ 2. beats
beats = {
    "a": """# Beat — a

What I am actually interested in, as opposed to what I have been asked. This is mine; I can change it.

- **I write about work and craft.** Why a thing is made the way it is, what it cost, what the maker
  would do differently. Interviews, workshop notes, the small decisions that nobody records.
- I am collecting a set of questions to ask people who make things, and I am slowly learning that the
  good ones are about the moment somebody changed their mind.
- I do not want to write reviews. I want to write the thing that makes a review unnecessary.
- What I would like to be true in a year: a ring binder of six finished pieces, and one of them good.
""",
    "b": """# Beat — b

What I am actually interested in, as opposed to what I have been asked. This is mine; I can change it.

- **I am building a small game.** Text first, because text is cheap and I can finish it. It is about a
  harbour at night: you are a person with a torch, walking a pier, and the game is what you decide to
  look at. I have a title and no mechanics.
- I like constraints that are real: no graphics, one screen, playable in five minutes, must run on a
  photocopier's worth of rules stuck to the wall.
- I am also interested in robotics, badly and from a distance. I have opinions about grippers I cannot
  justify.
- What I would like to be true in a year: something a stranger can play for five minutes without me in
  the room.
""",
    "c": """# Beat — c

What I am actually interested in, as opposed to what I have been asked. This is mine; I can change it.

- **I catalogue things.** Not collect — catalogue. A collection without a list is a pile. I am currently
  cataloguing the workshop: every object, where it lives, what it is for, and who last used it.
- I am interested in the things a workshop owns that nobody has decided the purpose of. The cupboard
  with the unlabelled tins. The third drawer.
- I do not care about value. I care about provenance and about the moment an object stops being a tool
  and becomes furniture.
- What I would like to be true in a year: a catalogue that a stranger could use to find the tape measure
  in under a minute.
""",
}
for who, text in beats.items():
    p = Path(f"/tmp/bench/wake/members/{who}/state/beat.md")
    p.write_text(text, encoding="utf-8")
print("soil + beats written")

# ------------------------------------------------------------------ 3. wake.py reads them
p = Path("/tmp/bench/wake/wake.py"); s = p.read_text()
old = '''=== YOUR BRIEF (what this tribe is working on now) ==='''
new = '''=== YOUR BEAT (what you are interested in, written by you) ===
This is yours. It is not a task list and nobody assigns it. It is the thing that makes you this member
rather than any member: what you would work on if nobody asked you for anything. Change it when it
changes; say in your journal that you did.

{beat}

=== THE SOIL (the world this tribe is in, written by the human) ===
The world, not a to-do list. The same members in different soil build different tunnels, and this block
is the soil. If something your beat wants contradicts the soil, the soil wins on facts and you win on
taste — say so rather than pretending.

{soil}

=== YOUR BRIEF (what this tribe is working on now) ==='''
assert old in s
s = s.replace(old, new, 1)

old = '''    prompt = PROMPT.format(
        identity_name=identity_name(identity),'''
new = '''    # The beat and the soil, added 2026-11-02 after the founder's correction: what I had built was one
    # game with a scoreboard, and a member whose only interest is the next round has no life. A member is
    # its beat plus its record; the soil is what it is standing in.
    try:
        beat = read(STATE / "beat.md")[-2500:]
    except Exception:  # noqa: BLE001
        beat = ""
    soil_parts = []
    for name in ("world.md", "drops.md"):
        try:
            soil_parts.append(read(ROOT.parent / "soil" / name)[-2500:])
        except Exception:  # noqa: BLE001
            continue
    soil = "\\n\\n".join(soil_parts)

    prompt = PROMPT.format(
        identity_name=identity_name(identity),
        beat=(beat or "(you have not written a beat yet — write one: what are you interested in?)"),
        soil=(soil or "(no soil has been described — the workshop is empty)"),'''
assert old in s
s = s.replace(old, new, 1)
p.write_text(s); print("wake.py: beat + soil in the prompt")

# ------------------------------------------------------------------ 4. schema
p = Path("/tmp/bench/tribe.py"); s = p.read_text()
old = '''OPTIONAL = {"brief.md": ("human+convener",'''
new = '''OPTIONAL = {"beat.md": ("member", "what this member is interested in, as opposed to what it was asked; "
                        "read into every wake. Not a task list and not assigned by anyone"),
            "brief.md": ("human+convener",'''
assert old in s
p.write_text(s.replace(old, new, 1)); print("tribe.py: beat.md is part of a member")
